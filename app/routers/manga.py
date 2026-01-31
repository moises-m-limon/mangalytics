from fastapi import APIRouter, HTTPException
from typing import List
import json
from datetime import datetime

from app.models.schemas import (
    MangaGenerationRequest,
    MangaGenerationResponse,
    MangaPanel
)
from app.services.reducto import reducto_service
from app.services.gemini import gemini_service
from app.services.resend_email import resend_service
from app.services.panel_generator import panel_generator
from app.db.supabase import supabase_db

router = APIRouter(prefix="/manga", tags=["manga"])


@router.post("", response_model=MangaGenerationResponse)
async def generate_manga_and_send(request: MangaGenerationRequest):
    """
    Generate manga panels from research figures and send via email

    This endpoint:
    1. Fetches PDFs from Supabase storage
    2. Extracts figures using Reducto
    3. Generates manga narrative using Gemini (nano-banana technique)
    4. Sends the manga digest via Resend email

    Args:
        request: MangaGenerationRequest with email, topic, date, and optional paper_title

    Returns:
        MangaGenerationResponse with narrative, panels, and email status
    """
    try:
        # Build the path based on email/topic/date
        bucket_path = f"{request.email}/{request.topic}/{request.date}"

        print(f"🔍 Listing files in path: {bucket_path}")

        # List all PDF files in the path
        pdf_files = supabase_db.list_files_in_path(bucket_path)

        if not pdf_files:
            raise HTTPException(
                status_code=404,
                detail=f"No PDF files found in path: {bucket_path}"
            )

        print(f"📁 Found {len(pdf_files)} PDF files, processing first {request.max_files}")

        # Limit to max_files
        pdf_files = pdf_files[:request.max_files]

        # Collect all figures from all processed PDFs
        all_figures = []

        # Process each PDF file
        for file_path in pdf_files:
            try:
                print(f"\n📄 Processing file: {file_path}")

                # Download PDF from Supabase
                try:
                    pdf_bytes = supabase_db.download_pdf(file_path)
                except Exception as e:
                    print(f"✗ Failed to download {file_path}: {str(e)}")
                    continue

                # Process with Reducto
                print("🔬 Extracting figures with Reducto...")
                try:
                    reducto_result = await reducto_service.process_pdf(
                        pdf_bytes,
                        file_path
                    )
                    reducto_pairings = reducto_result.get("pairings", [])
                except Exception as e:
                    print(f"✗ Reducto processing failed for {file_path}: {str(e)}")
                    continue

                if not reducto_pairings:
                    print(f"⚠️  No figures found in {file_path}")
                    continue

                print(f"✓ Extracted {len(reducto_pairings)} figures")
                all_figures.extend(reducto_pairings)

            except Exception as e:
                print(f"✗ Unexpected error processing {file_path}: {str(e)}")
                continue

        if not all_figures:
            raise HTTPException(
                status_code=404,
                detail="No figures could be extracted from the PDFs"
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

        # Generate PNG images for each panel
        print("🎨 Generating panel PNG images...")
        panel_images = []
        panel_image_urls = []
        try:
            import os
            corgi_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "corgis.png")

            panel_images = panel_generator.create_all_panels(
                panels=panels,
                corgi_image_path=corgi_path
            )

            print(f"✓ Generated {len(panel_images)} panel images")

        except Exception as e:
            print(f"⚠️  Failed to generate panel images: {str(e)}")

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
                "figures_used": len(all_figures),
                "processed_files": pdf_files
            }

            # Upload to Supabase
            supabase_db.upload_manga_panels(
                file_path=panels_path,
                content=json.dumps(manga_data, indent=2)
            )

            # Get public URL
            panels_url = supabase_db.get_panels_public_url(panels_path)
            print(f"✓ Manga panels JSON saved: {panels_url}")

            # Upload panel PNG images
            for panel_img in panel_images:
                try:
                    panel_num = panel_img["panel_number"]
                    img_filename = f"panel_{panel_num}.png"
                    img_path = f"{request.email}/{request.topic}/{request.date}/{img_filename}"

                    supabase_db.upload_image(
                        image_path=img_path,
                        image_data=panel_img["image_data"],
                        content_type="image/png"
                    )

                    # Get public URL for the panel image
                    img_url = supabase_db.get_public_url(img_path)
                    panel_image_urls.append({
                        "panel_number": panel_num,
                        "url": img_url,
                        "image_data": panel_img["image_data"]
                    })

                    print(f"✓ Uploaded panel {panel_num} PNG: {img_url}")

                except Exception as e:
                    print(f"✗ Failed to upload panel {panel_num} PNG: {str(e)}")
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
