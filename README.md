# mangalytics

A FastAPI application that:
1. Scrapes arXiv search results using Firecrawl and uploads PDFs to Supabase storage
2. Processes PDFs with Reducto to extract figures and stores them in a normalized database structure
3. Generates manga-style narratives from research figures using Gemini AI
4. Sends beautiful email digests with a friendly corgi guide via Resend

## Features

- Dynamic arXiv search parameters
- Scrapes PDF links from arXiv search results
- Downloads and uploads first 5 PDFs to Supabase bucket with partitioned storage
- Preview endpoint to see available PDFs before uploading
- Reducto integration for PDF processing and figure extraction
- Normalized database schema for recommendation tracking
- Automatic image storage in Supabase with public URLs
- **NEW: Manga generation with Gemini AI using nano-banana technique**
- **NEW: Friendly corgi avatar as research guide/narrator**
- **NEW: Email delivery via Resend with beautiful HTML formatting**
- **NEW: Visual PNG panel generation with custom styling**
- **NEW: Automatic upload to Supabase panels bucket**

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

4. Configure environment variables in `.env` file:
   - `FIRECRAWL_API_KEY`
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_ROLE_KEY`
   - `REDUCTO_API_KEY`

5. Set up Supabase database and storage:
   - Run the SQL migrations in `db_migrations.sql`
   - Create bucket `documents` (for PDFs)
   - Create bucket `reducto-images` (for extracted figures)
   - Create bucket `panels` (for manga panel images)

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
python -m app.main
```

Or using uvicorn directly:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## Project Structure

```
app/
  main.py              # FastAPI application entry point
  routers/
    scraper.py         # arXiv scraping endpoints
    recommendations.py # Reducto processing endpoints
  services/
    reducto.py         # Reducto API integration
  db/
    supabase.py        # Supabase database operations
  models/
    schemas.py         # Pydantic models
```

## Endpoints

### GET `/`
Health check endpoint

### POST `/scraper/scrape-and-upload`
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

### GET `/scraper/search-preview`
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

### POST `/recommendations`
Process ALL PDFs in a bucket path with Reducto and extract figures

**Request Body:**
```json
{
  "email": "user@example.com",
  "topic": "LLMs",
  "date": "01_31_2026",
  "max_files": 3
}
```

**Note:** `max_files` defaults to 3 if not specified.

**Response:**
```json
{
  "email": "user@example.com",
  "topic": "LLMs",
  "date": "01_31_2026",
  "total_files_processed": 2,
  "files": [
    {
      "file_name": "user@example.com/LLMs/01_31_2026/2301.12345.pdf",
      "created_at": "2026-01-31T18:42:00Z",
      "pairings": [
        {
          "figure_content": "Figure 1: Model architecture",
          "image_url": "https://.../reducto-images/.../figure_1.png"
        }
      ]
    }
  ]
}
```

## API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Example Usage

```bash
# Preview PDFs
curl -X GET "http://localhost:8000/scraper/search-preview" \
  -H "Content-Type: application/json"

# Scrape and upload PDFs
curl -X POST "http://localhost:8000/scraper/scrape-and-upload" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "topic": "LLMs",
    "terms": "LLMs",
    "field": "title",
    "operator": "AND",
    "size": 50
  }'

# Process all PDFs in a path with Reducto
curl -X POST "http://localhost:8000/recommendations" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "topic": "LLMs",
    "date": "01_31_2026"
  }'
```

See `EXAMPLES.md` for more detailed examples.