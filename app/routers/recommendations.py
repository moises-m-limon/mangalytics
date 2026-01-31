from fastapi import APIRouter, HTTPException
from datetime import datetime

from app.models.schemas import (
    RecommendationRequest,
    RecommendationResponse,
    FileRecommendation,
    FigurePairing
)
from app.services.reducto import reducto_service
from app.db.supabase import supabase_db

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("", response_model=RecommendationResponse)
async def create_recommendation(request: RecommendationRequest):
    """
    Process all PDFs in a bucket path with Reducto and store figure pairings

    Args:
        request: RecommendationRequest with email, topic, and date

    Returns:
        RecommendationResponse with all files and their pairings
    """
    try:
        # Build the path based on email/topic/date
        bucket_path = f"{request.email}/{request.topic}/{request.date}"

        print(f"Listing files in path: {bucket_path}")

        # List all PDF files in the path
        pdf_files = supabase_db.list_files_in_path(bucket_path)

        if not pdf_files:
            raise HTTPException(
                status_code=404,
                detail=f"No PDF files found in path: {bucket_path}"
            )

        print(f"Found {len(pdf_files)} PDF files, processing first {request.max_files}")

        # Limit to max_files
        pdf_files = pdf_files[:request.max_files]

        file_recommendations = []
        figure_counter = 1  # Global counter for figure naming

        # Process each PDF file
        for file_path in pdf_files:
            try:
                print(f"\nProcessing file: {file_path}")

                # Download PDF from Supabase
                try:
                    pdf_bytes = supabase_db.download_pdf(file_path)
                except Exception as e:
                    print(f"✗ Failed to download {file_path}: {str(e)}")
                    continue

                # Process with Reducto
                print("Processing with Reducto...")
                try:
                    reducto_pairings = await reducto_service.process_pdf(
                        pdf_bytes,
                        file_path
                    )
                except Exception as e:
                    print(f"✗ Reducto processing failed for {file_path}: {str(e)}")
                    continue

                if not reducto_pairings:
                    print(f"No figures found in {file_path}")
                    continue

                print(f"Found {len(reducto_pairings)} figures")

                # Insert recommendation request for this file
                try:
                    request_id = await supabase_db.insert_recommendation_request(
                        email=request.email,
                        topic=request.topic,
                        file_name=file_path
                    )
                except Exception as e:
                    print(f"✗ Failed to insert request for {file_path}: {str(e)}")
                    continue

                # Upload images and prepare pairings
                db_pairings = []
                response_pairings = []

                for pairing in reducto_pairings:
                    try:
                        # Upload image to Supabase storage
                        image_path = f"{request.email}/{request.topic}/{request.date}/figure_{figure_counter}.png"
                        supabase_db.upload_image(
                            image_path,
                            pairing["image_data"],
                            content_type="image/png"
                        )

                        db_pairings.append({
                            "figure_content": pairing["figure_content"],
                            "image_path": image_path
                        })

                        # Get public URL for response
                        image_url = supabase_db.get_public_url(image_path)
                        response_pairings.append(FigurePairing(
                            figure_content=pairing["figure_content"],
                            image_url=image_url
                        ))

                        print(f"✓ Uploaded figure {figure_counter} to {image_path}")
                        figure_counter += 1

                    except Exception as e:
                        print(f"✗ Failed to upload figure {figure_counter}: {str(e)}")
                        figure_counter += 1
                        continue

                # Insert pairings into database
                if db_pairings:
                    try:
                        await supabase_db.insert_recommendation_pairings(
                            request_id,
                            db_pairings
                        )
                    except Exception as e:
                        print(f"✗ Failed to insert pairings for {file_path}: {str(e)}")
                        continue

                # Add to file recommendations
                file_recommendations.append(FileRecommendation(
                    file_name=file_path,
                    created_at=datetime.now(),
                    pairings=response_pairings
                ))

                print(f"✓ Completed processing {file_path}")

            except Exception as e:
                print(f"✗ Unexpected error processing {file_path}: {str(e)}")
                continue

        if not file_recommendations:
            raise HTTPException(
                status_code=500,
                detail="Failed to process any files successfully"
            )

        return RecommendationResponse(
            email=request.email,
            topic=request.topic,
            date=request.date,
            total_files_processed=len(file_recommendations),
            files=file_recommendations
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
