# mangalytics

A FastAPI application that scrapes arXiv search results using Firecrawl and uploads PDFs to Supabase storage.

## Features

- Dynamic arXiv search parameters
- Scrapes PDF links from arXiv search results
- Downloads and uploads first 5 PDFs to Supabase bucket
- Preview endpoint to see available PDFs before uploading

## Setup

### Option 1: Using Conda (Recommended)

1. Create a new conda environment:
```bash
conda create -n mangalytics python=3.11 -y
```

2. Activate the environment:
```bash
conda activate mangalytics
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables in `.env` file (already created with your credentials)

5. Make sure your Supabase bucket named `pdfs` exists

### Option 2: Using pip/venv

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables in `.env` file (already created with your credentials)

4. Make sure your Supabase bucket named `pdfs` exists

## Running the API

```bash
python main.py
```

Or using uvicorn directly:
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

## Endpoints

### GET `/`
Health check endpoint

### POST `/scrape-and-upload`
Scrapes arXiv and uploads first 5 PDFs to Supabase with partitioned storage

**Storage Structure:** `email/topic/MM_DD_YYYY/filename.pdf`

**Request Body:**
```json
{
  "email": "user@example.com",
  "topic": "LLMs",
  "terms": "LLMs",
  "field": "title",
  "operator": "AND",
  "abstracts": "show",
  "size": 50,
  "order": "-submitted_date"
}
```

**Response:**
```json
{
  "success": true,
  "uploaded_count": 5,
  "files": [
    "user@example.com/LLMs/01_31_2026/2301.12345.pdf",
    "user@example.com/LLMs/01_31_2026/2301.12346.pdf",
    ...
  ],
  "errors": null
}
```

### GET `/search-preview`
Preview available PDFs without uploading

**Query Parameters:** Same as scrape-and-upload

**Response:**
```json
{
  "search_url": "https://arxiv.org/search/...",
  "total_pdfs_found": 50,
  "first_5_pdfs": ["https://arxiv.org/pdf/2301.12345", ...]
}
```

## API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Example Usage

```bash
# Preview PDFs
curl -X GET "http://localhost:8000/search-preview" \
  -H "Content-Type: application/json"

# Scrape and upload
curl -X POST "http://localhost:8000/scrape-and-upload" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "topic": "LLMs",
    "terms": "LLMs",
    "field": "title",
    "operator": "AND",
    "size": 50
  }'
```