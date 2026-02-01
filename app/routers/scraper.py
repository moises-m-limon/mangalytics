from fastapi import APIRouter, HTTPException
from firecrawl import Firecrawl
import requests
import os
from datetime import datetime
from typing import List
from dotenv import load_dotenv

from app.models.schemas import SearchParams, UploadResponse
from app.db.supabase import supabase_db

# Load environment variables
load_dotenv()

router = APIRouter(prefix="/scraper", tags=["scraper"])

firecrawl = Firecrawl(api_key=os.getenv("FIRECRAWL_API_KEY"))


def build_firecrawl_url(params: SearchParams) -> str:
    """Build arXiv search URL with dynamic parameters"""
    base_url = "https://arxiv.org/search/advanced"
    query_params = (
        f"?advanced=1"
        f"&terms-0-term={params.terms}"
        f"&terms-0-operator={params.operator}"
        f"&terms-0-field={params.field}"
        f"&classification-physics_archives=all"
        f"&classification-include_cross_list=include"
        f"&date-filter_by=all_dates"
        f"&date-year="
        f"&date-from_date="
        f"&date-to_date="
        f"&date-date_type=submitted_date"
        f"&abstracts={params.abstracts}"
        f"&size={params.size}"
        f"&order={params.order}"
    )
    return base_url + query_params


@router.post("/scrape-and-upload", response_model=UploadResponse)
async def scrape_and_upload(params: SearchParams):
    """
    Scrape arXiv search results and upload first 5 PDFs to Supabase

    Args:
        params: Search parameters for arXiv

    Returns:
        UploadResponse with upload status and file list
    """
    try:
        search_url = build_firecrawl_url(params)
        print(f"Scraping URL: {search_url}")

        result = firecrawl.scrape(search_url, formats=["links", "markdown"])

        if not result or not hasattr(result, 'links'):
            raise HTTPException(status_code=500, detail="Failed to scrape links from arXiv")

        pdf_links = [link for link in result.links if "/pdf/" in link or link.endswith(".pdf")]

        if not pdf_links:
            raise HTTPException(status_code=404, detail="No PDF links found")

        pdf_links = pdf_links[:5]
        print(f"Found {len(pdf_links)} PDF links to upload")

        uploaded_files = []
        errors = []

        current_date = datetime.now().strftime("%m_%d_%Y")

        for idx, pdf_url in enumerate(pdf_links, 1):
            try:
                paper_id = pdf_url.split("/")[-1].replace(".pdf", "")
                if not paper_id:
                    paper_id = f"paper_{idx}"

                file_path = f"{params.email}/{params.topic}/{current_date}/{paper_id}.pdf"

                print(f"Downloading {idx}/5: {pdf_url}")

                response = requests.get(pdf_url, timeout=30)
                response.raise_for_status()

                try:
                    supabase_db.client.storage.from_(supabase_db.bucket_documents).upload(
                        file_path,
                        response.content,
                        {"content-type": "application/pdf"}
                    )
                    print(f"✓ Uploaded: {file_path}")
                except Exception as upload_error:
                    # Check if it's a duplicate error (409)
                    error_str = str(upload_error)
                    if "409" in error_str or "Duplicate" in error_str or "already exists" in error_str:
                        print(f"⚠ PDF already exists: {file_path}, skipping")
                    else:
                        # For other errors, re-raise
                        raise

                # Add to uploaded files list (whether new or existing)
                uploaded_files.append(file_path)

            except Exception as e:
                error_msg = f"Failed to process {pdf_url}: {str(e)}"
                print(f"✗ {error_msg}")
                errors.append(error_msg)

        return UploadResponse(
            success=len(uploaded_files) > 0,
            uploaded_count=len(uploaded_files),
            files=uploaded_files,
            errors=errors if errors else None
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/search-preview")
async def search_preview(params: SearchParams):
    """
    Preview the arXiv search URL and available PDFs without uploading

    Args:
        params: Search parameters for arXiv

    Returns:
        Preview information with URL and PDF links
    """
    try:
        search_url = build_firecrawl_url(params)
        result = firecrawl.scrape(search_url, formats=["links"])

        if not result or not hasattr(result, 'links'):
            raise HTTPException(status_code=500, detail="Failed to scrape links from arXiv")

        pdf_links = [link for link in result.links if "/pdf/" in link or link.endswith(".pdf")]

        return {
            "search_url": search_url,
            "total_pdfs_found": len(pdf_links),
            "first_5_pdfs": pdf_links[:5]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
