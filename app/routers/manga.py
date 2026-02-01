from fastapi import APIRouter, HTTPException
from typing import List
import json
from datetime import datetime

from app.models.schemas import (
    MangaGenerationRequest,
    MangaGenerationResponse,
    MangaPanel
)
from app.services.gemini import gemini_service
from app.services.resend_email import resend_service
from app.db.supabase import supabase_db

router = APIRouter(prefix="/manga", tags=["manga"])


@router.post("", response_model=MangaGenerationResponse)
async def generate_manga_and_send(request: MangaGenerationRequest):
    """
    Generate manga artwork from research figures and send via email

    This endpoint:
    1. Fetches figures from recommendation_pairings table (pre-processed by /recommendations)
    2. Generates manga narrative using Gemini 2.5 Flash (nano-banana technique)
    3. Creates actual manga artwork images using Gemini image generation model
    4. Uploads manga images to Supabase storage
    5. Sends the manga digest via Resend email

    Args:
        request: MangaGenerationRequest with email, topic, date, and optional paper_title

    Returns:
        MangaGenerationResponse with narrative, panels, and email status
    """
    try:
        # Fetch figures from recommendation_pairings table instead of calling Reducto
        print(f"🔍 Fetching figures from recommendation_pairings for {request.email}/{request.topic}/{request.date}")

        all_figures = await supabase_db.get_pairings_for_path(
            email=request.email,
            topic=request.topic,
            date=request.date,
            max_files=request.max_files
        )

        if not all_figures:
            raise HTTPException(
                status_code=404,
                detail=f"No recommendation pairings found for path: {request.email}/{request.topic}/{request.date}. "
                       f"Make sure you've run the /recommendations endpoint first to process PDFs."
            )

        print(f"\n🎨 Total figures collected: {len(all_figures)}")

        # Generate manga narrative using Gemini
        print("🤖 Generating manga narrative with Gemini...")
        try:
            manga_result = await gemini_service.generate_manga_from_figures(
                figures=all_figures,
                paper_title=request.paper_title or f"{request.topic} Research",
                topic=request.topic
            )

            narrative = manga_result["narrative"]
            panels = manga_result["panels"]

            print(f"✓ Generated {len(panels)} manga panels")

        except Exception as e:
            print(f"✗ Gemini generation failed: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate manga narrative: {str(e)}"
            )

        # Convert panels to MangaPanel models
        manga_panels = [
            MangaPanel(
                panel_number=panel.get("panel_number", f"Panel {i}"),
                title=panel.get("title"),
                description=panel.get("description"),
                dialogue=panel.get("dialogue")
            )
            for i, panel in enumerate(panels, 1)
        ]

        # Generate actual manga artwork images using Gemini
        print("🎨 Generating manga artwork with Gemini image generation...")
        panel_images = []
        panel_image_urls = []
        try:
            panel_images = await gemini_service.generate_manga_panel_images(
                panels=panels,
                research_figures=all_figures[:4] if len(all_figures) >= 4 else all_figures
            )

            print(f"✓ Generated {len(panel_images)} manga artwork images")

        except Exception as e:
            print(f"⚠️  Failed to generate manga images: {str(e)}")

        # Upload manga panels to Supabase panels bucket
        print("📦 Uploading manga panels to Supabase...")
        try:
            # Create filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            panels_filename = f"manga_panels_{timestamp}.json"
            panels_path = f"{request.email}/{request.topic}/{request.date}/{panels_filename}"

            # Prepare JSON data
            manga_data = {
                "email": request.email,
                "topic": request.topic,
                "date": request.date,
                "paper_title": request.paper_title or f"{request.topic} Research",
                "generated_at": datetime.now().isoformat(),
                "narrative": narrative,
                "panels": [
                    {
                        "panel_number": p.panel_number,
                        "title": p.title,
                        "description": p.description,
                        "dialogue": p.dialogue
                    }
                    for p in manga_panels
                ],
                "figures_used": len(all_figures)
            }

            # Upload to Supabase
            supabase_db.upload_manga_panels(
                file_path=panels_path,
                content=json.dumps(manga_data, indent=2)
            )

            # Get public URL
            panels_url = supabase_db.get_panels_public_url(panels_path)
            print(f"✓ Manga panels JSON saved: {panels_url}")

            # Upload panel PNG images to panels bucket
            for panel_img in panel_images:
                try:
                    panel_num = panel_img["panel_number"]
                    img_filename = f"panel_{panel_num}.png"
                    img_path = f"{request.email}/{request.topic}/{request.date}/{img_filename}"

                    try:
                        supabase_db.upload_panel_image(
                            image_path=img_path,
                            image_data=panel_img["image_data"],
                            content_type="image/png"
                        )
                        print(f"✓ Uploaded panel {panel_num} PNG to panels bucket: {img_path}")
                    except Exception as upload_error:
                        # Check if it's a duplicate error (409)
                        error_str = str(upload_error)
                        if "409" in error_str or "Duplicate" in error_str or "already exists" in error_str:
                            print(f"⚠ Panel {panel_num} already exists in panels bucket at {img_path}, using existing file")
                        else:
                            # For other errors, re-raise to skip this panel
                            raise

                    # Get public URL for the panel image (whether new or existing)
                    img_url = supabase_db.get_panel_public_url(img_path)
                    panel_image_urls.append({
                        "panel_number": panel_num,
                        "url": img_url,
                        "image_data": panel_img["image_data"]
                    })

                except Exception as e:
                    print(f"✗ Failed to process panel {panel_num} PNG: {str(e)}")
                    continue

        except Exception as e:
            print(f"⚠️  Failed to upload manga panels to Supabase: {str(e)}")
            # Don't fail the entire request if upload fails

        # Send email with Resend
        print("📧 Sending manga digest via email...")
        email_sent = False
        email_id = None
        try:
            email_result = await resend_service.send_manga_email(
                to_email=request.email,
                topic=request.topic,
                manga_narrative=narrative,
                panels=panels,
                figure_images=all_figures[:5],  # Include first 5 figures as attachments
                panel_images=panel_image_urls  # Include panel PNG images
            )

            email_sent = email_result.get("success", False)
            email_id = email_result.get("email_id")

            if email_sent:
                print(f"✓ Email sent successfully! ID: {email_id}")
            else:
                print(f"⚠️  Email failed: {email_result.get('error')}")

        except Exception as e:
            print(f"✗ Email sending failed: {str(e)}")
            # Don't fail the entire request if email fails

        return MangaGenerationResponse(
            email=request.email,
            topic=request.topic,
            narrative=narrative,
            panels=manga_panels,
            figures_used=len(all_figures),
            email_sent=email_sent,
            email_id=email_id
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"✗ Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
