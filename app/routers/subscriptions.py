from fastapi import APIRouter, HTTPException
from datetime import datetime
from typing import Optional

from app.models.schemas import (
    SubscriptionRequest,
    SearchParams,
    RecommendationRequest,
    MangaGenerationRequest
)
from app.routers.scraper import scrape_and_upload
from app.routers.recommendations import create_recommendation
from app.routers.manga import generate_manga_and_send

router = APIRouter(prefix="/subscribe", tags=["subscriptions"])


@router.post("")
async def process_subscription(request: SubscriptionRequest):
    """
    Complete subscription pipeline:
    1. Scrape and upload PDFs from arXiv
    2. Process PDFs with Reducto to extract figures
    3. Generate manga panels and send email

    Args:
        request: SubscriptionRequest with email and topic

    Returns:
        Summary of the entire pipeline execution
    """
    try:
        email = request.email
        topic = request.topic
        date = datetime.now().strftime("%m_%d_%Y")

        print(f"\n{'='*60}")
        print(f"🚀 Starting subscription pipeline for {email} - {topic}")
        print(f"{'='*60}\n")

        # Step 1: Scrape and upload PDFs
        print("📥 STEP 1/3: Scraping and uploading PDFs from arXiv...")
        try:
            search_params = SearchParams(
                email=email,
                topic=topic,
                terms=topic,
                field="title",
                operator="AND",
                abstracts="show",
                size=50,
                order="-submitted_date"
            )

            scrape_result = await scrape_and_upload(search_params)

            if not scrape_result.success or scrape_result.uploaded_count == 0:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to upload PDFs: {scrape_result.errors}"
                )

            print(f"✓ Step 1 complete: Uploaded {scrape_result.uploaded_count} PDFs")
            uploaded_files = scrape_result.files

        except Exception as e:
            print(f"✗ Step 1 failed: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"PDF scraping failed: {str(e)}"
            )

        # Step 2: Process PDFs with Reducto
        print(f"\n🔬 STEP 2/3: Processing PDFs with Reducto...")
        try:
            recommendation_request = RecommendationRequest(
                email=email,
                topic=topic,
                date=date,
                max_files=1  # Process first 1 file
            )

            recommendation_result = await create_recommendation(recommendation_request)

            if recommendation_result.total_files_processed == 0:
                raise HTTPException(
                    status_code=500,
                    detail="No files were successfully processed by Reducto"
                )

            print(f"✓ Step 2 complete: Processed {recommendation_result.total_files_processed} files")
            total_figures = sum(len(f.pairings) for f in recommendation_result.files)
            print(f"  Extracted {total_figures} figures total")

        except Exception as e:
            print(f"✗ Step 2 failed: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Reducto processing failed: {str(e)}"
            )

        # Step 3: Generate manga and send email
        print(f"\n🎨 STEP 3/3: Generating manga and sending email...")
        try:
            manga_request = MangaGenerationRequest(
                email=email,
                topic=topic,
                date=date,
                max_files=1,  # Use first file for manga generation
                paper_title=None  # Will be auto-detected
            )

            manga_result = await generate_manga_and_send(manga_request)

            if not manga_result.email_sent:
                print(f"⚠️  Manga generated but email failed")
            else:
                print(f"✓ Step 3 complete: Email sent! ID: {manga_result.email_id}")

        except Exception as e:
            print(f"✗ Step 3 failed: {str(e)}")
            # Don't fail the entire request if manga/email fails
            # User still got PDFs processed
            manga_result = None

        # Summary
        print(f"\n{'='*60}")
        print(f"✓ SUBSCRIPTION PIPELINE COMPLETE")
        print(f"{'='*60}\n")

        return {
            "success": True,
            "email": email,
            "topic": topic,
            "date": date,
            "pipeline_summary": {
                "step_1_scraping": {
                    "status": "completed",
                    "pdfs_uploaded": scrape_result.uploaded_count,
                    "files": uploaded_files
                },
                "step_2_processing": {
                    "status": "completed",
                    "files_processed": recommendation_result.total_files_processed,
                    "figures_extracted": total_figures
                },
                "step_3_manga": {
                    "status": "completed" if manga_result and manga_result.email_sent else "failed",
                    "email_sent": manga_result.email_sent if manga_result else False,
                    "email_id": manga_result.email_id if manga_result else None,
                    "panels_generated": len(manga_result.panels) if manga_result else 0
                }
            },
            "message": f"Subscription processed! Check {email} for your manga digest."
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"\n✗ PIPELINE FAILED: {str(e)}\n")
        raise HTTPException(
            status_code=500,
            detail=f"Subscription pipeline failed: {str(e)}"
        )
