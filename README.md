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
   - `GEMINI_API_KEY`
   - `RESEND_API_KEY`
   - `RESEND_FROM_EMAIL` (set to `mangalytics <noreply@mangalytics.online>`)

5. Set up Supabase database and storage:
   - Run the SQL migrations in `db_migrations.sql`
   - Create bucket `documents` (for PDFs)
   - Create bucket `reducto-images` (for extracted figures)
   - Create bucket `panels` (for manga panel images)

**Note on Email Sending:**
- Domain `mangalytics.online` is verified with Resend
- Emails can now be sent to any recipient
- From address: `mangalytics <noreply@mangalytics.online>`
- See `RESEND_SETUP.md` for domain verification details

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

### POST `/subscribe` ⭐ NEW
**Complete subscription pipeline** - orchestrates scraping, processing, and manga generation

**Request Body:**
```json
{
  "email": "user@example.com",
  "topic": "LLMs"
}
```

**What it does:**
1. Scrapes and uploads 5 PDFs from arXiv
2. Processes first 1 PDF with Reducto (extracts figures)
3. Generates manga panels and sends email

**Response:**
```json
{
  "success": true,
  "email": "user@example.com",
  "topic": "LLMs",
  "date": "01_31_2026",
  "pipeline_summary": {
    "step_1_scraping": { "status": "completed", "pdfs_uploaded": 5 },
    "step_2_processing": { "status": "completed", "files_processed": 1 },
    "step_3_manga": { "status": "completed", "email_sent": true }
  }
}
```

**⏱️ Expected time:** 1-3 minutes

See `SUBSCRIPTION_PIPELINE.md` for detailed documentation.

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

**Note:** `max_files` defaults to 1 if not specified.

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

## Frontend

A Next.js subscription form is included in the `frontend/` directory.

### Running the Frontend

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:3000` to see the subscription form.

### Frontend Configuration

Set the backend URL in `frontend/.env.local`:
```bash
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

For production, update to your Cloud Run URL:
```bash
NEXT_PUBLIC_BACKEND_URL=https://your-service.run.app
```

## Example Usage

```bash
# Complete subscription pipeline (recommended)
curl -X POST "http://localhost:8000/subscribe" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "topic": "LLMs"
  }'

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

## Deployment to Google Cloud Run

### Prerequisites

1. Install Google Cloud SDK:
```bash
# macOS
brew install google-cloud-sdk

# Or download from: https://cloud.google.com/sdk/docs/install
```

2. Authenticate with Google Cloud:
```bash
gcloud auth login
gcloud auth configure-docker
```

3. Set your project ID:
```bash
gcloud config set project mangalytics
```

### Build and Deploy

1. Build the Docker image for Cloud Run (linux/amd64 platform):
```bash
docker build --platform=linux/amd64 -t gcr.io/mangalytics/mangalytics_service:latest .
```

2. Push the image to Google Container Registry:
```bash
docker push gcr.io/mangalytics/mangalytics_service:latest
```

3. Deploy to Cloud Run:
```bash
gcloud run deploy mangalytics-service \
  --image gcr.io/mangalytics/mangalytics_service:latest \
  --platform managed \
  --region us-west1 \
  --allow-unauthenticated \
  --port 8080 \
  --memory 2Gi \
  --timeout 900 \
  --set-env-vars FIRECRAWL_API_KEY=your-key,SUPABASE_URL=your-url,SUPABASE_SERVICE_ROLE_KEY=your-key,REDUCTO_API_KEY=your-key,GEMINI_API_KEY=your-key,RESEND_API_KEY=your-key,RESEND_FROM_EMAIL="mangalytics <noreply@mangalytics.online>"
```

**Note:** Replace the environment variables with your actual credentials or use `--env-vars-file` to load from a file.

### Using Environment File (Recommended)

1. Create a `.env.yaml` file:
```yaml
FIRECRAWL_API_KEY: "your-firecrawl-key"
SUPABASE_URL: "your-supabase-url"
SUPABASE_SERVICE_ROLE_KEY: "your-supabase-key"
REDUCTO_API_KEY: "your-reducto-key"
GEMINI_API_KEY: "your-gemini-key"
RESEND_API_KEY: "your-resend-key"
RESEND_FROM_EMAIL: "mangalytics <noreply@mangalytics.online>"
SUPABASE_BUCKET: "documents"
```

2. Deploy with environment file:
```bash
gcloud run deploy mangalytics-service \
  --image gcr.io/skyspace-476120/mangalytics/mangalytics_service:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080 \
  --memory 2Gi \
  --timeout 900 \
  --env-vars-file .env.yaml
```

### Quick Deploy Script

Create a `deploy.sh` file:
```bash
#!/bin/bash

# Configuration
PROJECT_ID="skyspace-476120"
SERVICE_NAME="mangalytics-service"
IMAGE_NAME="gcr.io/${PROJECT_ID}/mangalytics/mangalytics_service:latest"
REGION="us-central1"

echo "Building Docker image..."
docker build --platform=linux/amd64 -t ${IMAGE_NAME} .

echo "Pushing image to GCR..."
docker push ${IMAGE_NAME}

echo "Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --port 8080 \
  --memory 2Gi \
  --timeout 900 \
  --env-vars-file .env.yaml

echo "Deployment complete!"
```

Make it executable and run:
```bash
chmod +x deploy.sh
./deploy.sh
```

### Post-Deployment

1. Get your service URL:
```bash
gcloud run services describe mangalytics-service --region us-central1 --format 'value(status.url)'
```

2. Test the deployment:
```bash
curl https://your-service-url.run.app/
```

3. View logs:
```bash
gcloud run services logs read mangalytics-service --region us-central1
```

### Configuration Notes

- **Memory**: 2Gi recommended for PDF processing with Reducto
- **Timeout**: 900 seconds (15 minutes) for large PDF processing jobs
- **Port**: Must be 8080 (Cloud Run default)
- **Authentication**: Set to `--allow-unauthenticated` for public API access
- **Region**: `us-central1` or change to your preferred region

### Troubleshooting

**Build Issues:**
- Make sure you're building for `linux/amd64` platform
- Ensure all required files (corgis.png, logo.png) are in the root directory

**Environment Variables:**
- Don't commit `.env` or `.env.yaml` files with secrets
- Use Google Secret Manager for production deployments
- Verify all required API keys are set

**Memory/Timeout:**
- Increase memory if getting out-of-memory errors
- Increase timeout for processing many large PDFs