from fastapi import FastAPI, HTTPException
from firecrawl import Firecrawl
from supabase import create_client
import requests
import os
from dotenv import load_dotenv
from typing import List, Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime

# Load environment variables
load_dotenv()

# Initialize FastAPI
app = FastAPI(title="Mangalytics API", version="1.0.0")

# Initialize clients
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
BUCKET_NAME = os.getenv("SUPABASE_BUCKET", "documents")

if not all([FIRECRAWL_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY]):
    raise ValueError("Missing required environment variables")

firecrawl = Firecrawl(api_key=FIRECRAWL_API_KEY)
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


class SearchParams(BaseModel):
    """Model for dynamic search parameters"""
    email: EmailStr  # Required: user email for partitioning
    topic: str  # Required: topic for partitioning (e.g., "LLMs")
    terms: str = "LLMs"
    field: str = "title"
    operator: str = "AND"
    abstracts: str = "show"
    size: int = 50
    order: str = "-submitted_date"


class UploadResponse(BaseModel):
    """Response model for upload operation"""
    success: bool
    uploaded_count: int
    files: List[str]
    errors: Optional[List[str]] = None


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


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Mangalytics API is running", "status": "healthy"}


@app.post("/scrape-and-upload", response_model=UploadResponse)
async def scrape_and_upload(params: SearchParams):
    """
    Scrape arXiv search results and upload first 5 PDFs to Supabase

    Args:
        params: Search parameters for arXiv

    Returns:
        UploadResponse with upload status and file list
    """
    try:
        # Build and scrape the URL
        search_url = build_firecrawl_url(params)
        print(f"Scraping URL: {search_url}")

        result = firecrawl.scrape(search_url, formats=["links", "markdown"])

        if not result or not hasattr(result, 'links'):
            raise HTTPException(status_code=500, detail="Failed to scrape links from arXiv")

        # Filter for PDF links
        pdf_links = [link for link in result.links if "/pdf/" in link or link.endswith(".pdf")]

        if not pdf_links:
            raise HTTPException(status_code=404, detail="No PDF links found")

        # Take only the first 5
        pdf_links = pdf_links[:5]
        print(f"Found {len(pdf_links)} PDF links to upload")

        uploaded_files = []
        errors = []

        # Get current date for partitioning
        current_date = datetime.now().strftime("%m_%d_%Y")

        # Download and upload each PDF
        for idx, pdf_url in enumerate(pdf_links, 1):
            try:
                # Extract paper ID from URL
                paper_id = pdf_url.split("/")[-1].replace(".pdf", "")
                if not paper_id:
                    paper_id = f"paper_{idx}"

                print(f"Downloading {idx}/5: {pdf_url}")

                # Download PDF
                response = requests.get(pdf_url, timeout=30)
                response.raise_for_status()

                # Create partitioned path: email/topic/date/filename.pdf
                file_path = f"{params.email}/{params.topic}/{current_date}/{paper_id}.pdf"

                # Upload to Supabase Storage
                supabase.storage.from_(BUCKET_NAME).upload(
                    file_path,
                    response.content,
                    {"content-type": "application/pdf"}
                )

                uploaded_files.append(file_path)
                print(f"✓ Uploaded: {file_path}")

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


@app.get("/search-preview")
async def search_preview(params: SearchParams):
    """
    Preview the arXiv search URL and available PDFs without uploading

    Args:
        params: Search parameters for arXiv

    Returns:
        Preview information with URL and PDF links
    """
    try:
        # Build and scrape the URL
        search_url = build_firecrawl_url(params)
        result = firecrawl.scrape(search_url, formats=["links"])

        if not result or not hasattr(result, 'links'):
            raise HTTPException(status_code=500, detail="Failed to scrape links from arXiv")

        # Filter for PDF links
        pdf_links = [link for link in result.links if "/pdf/" in link or link.endswith(".pdf")]

        return {
            "search_url": search_url,
            "total_pdfs_found": len(pdf_links),
            "first_5_pdfs": pdf_links[:5]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
