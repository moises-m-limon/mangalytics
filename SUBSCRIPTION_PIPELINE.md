# subscription pipeline

complete end-to-end pipeline triggered by frontend subscription form.

## overview

when a user subscribes via the frontend, the `/subscribe` endpoint orchestrates three services in sequence:

1. **scrape pdfs** from arxiv
2. **process with reducto** to extract figures
3. **generate manga** and send email

## architecture

```
Frontend (Next.js)
  ↓
  POST /api/subscribe
  ↓
Backend API
  ↓
  POST /subscribe
  ├─→ Step 1: POST /scraper/scrape-and-upload
  │   └─→ Uploads 5 PDFs to Supabase (email/topic/date/)
  ├─→ Step 2: POST /recommendations
  │   └─→ Processes PDFs with Reducto, extracts figures
  └─→ Step 3: POST /manga
      └─→ Generates manga panels and sends email
```

## endpoint: POST /subscribe

### request

```json
{
  "email": "user@example.com",
  "topic": "LLMs"
}
```

### response

```json
{
  "success": true,
  "email": "user@example.com",
  "topic": "LLMs",
  "date": "01_31_2026",
  "pipeline_summary": {
    "step_1_scraping": {
      "status": "completed",
      "pdfs_uploaded": 5,
      "files": [
        "user@example.com/LLMs/01_31_2026/2301.12345.pdf",
        "..."
      ]
    },
    "step_2_processing": {
      "status": "completed",
      "files_processed": 1,
      "figures_extracted": 4
    },
    "step_3_manga": {
      "status": "completed",
      "email_sent": true,
      "email_id": "abc123",
      "panels_generated": 4
    }
  },
  "message": "Subscription processed! Check user@example.com for your manga digest."
}
```

## pipeline steps

### step 1: scrape and upload pdfs

- searches arxiv for papers matching the topic
- downloads first 5 PDFs
- uploads to supabase `documents` bucket
- path structure: `email/topic/MM_DD_YYYY/filename.pdf`

**configuration:**
```python
SearchParams(
    email=email,
    topic=topic,
    terms=topic,
    field="title",
    operator="AND",
    abstracts="show",
    size=50,
    order="-submitted_date"
)
```

### step 2: process with reducto

- lists all PDFs in the path
- processes first 1 file (configurable via `max_files`)
- extracts figures and text from each PDF
- stores in `recommendation_pairings` table with reducto metadata
- uploads figure images to `reducto-images` bucket

**configuration:**
```python
RecommendationRequest(
    email=email,
    topic=topic,
    date=date,
    max_files=1
)
```

### step 3: generate manga and send email

- fetches figures from database
- generates manga narrative with gemini
- creates 4 manga panel images
- uploads panels to `panels` bucket
- sends email with embedded panel images

**configuration:**
```python
MangaGenerationRequest(
    email=email,
    topic=topic,
    date=date,
    max_files=1,
    paper_title=None
)
```

## error handling

### graceful degradation

- if step 1 fails → entire pipeline fails (no PDFs to process)
- if step 2 fails → entire pipeline fails (no figures for manga)
- if step 3 fails → pipeline returns success but notes email failed

### step 3 failure handling

manga generation/email sending doesn't fail the entire request because:
- PDFs are already uploaded and stored
- figures are already extracted and in database
- user can manually retry manga generation later

## frontend integration

### next.js api route

located at: `frontend/app/api/subscribe/route.ts`

```typescript
export async function POST(request: NextRequest) {
  const { email, topic } = await request.json();

  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

  const response = await fetch(`${backendUrl}/subscribe`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, topic })
  });

  return NextResponse.json(await response.json());
}
```

### frontend form

located at: `frontend/app/page.tsx`

```typescript
const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault();
  setLoading(true);

  const response = await fetch('/api/subscribe', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, topic })
  });

  const data = await response.json();

  if (response.ok) {
    setSuccess(true);
  }
};
```

## environment variables

### backend (.env)

```bash
FIRECRAWL_API_KEY=your-key
SUPABASE_URL=your-url
SUPABASE_SERVICE_ROLE_KEY=your-key
REDUCTO_API_KEY=your-key
GEMINI_API_KEY=your-key
RESEND_API_KEY=your-key
SUPABASE_BUCKET=documents
```

### frontend (.env.local)

```bash
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
# or for production:
NEXT_PUBLIC_BACKEND_URL=https://your-cloud-run-url.run.app
```

## testing

### local testing

1. start backend:
```bash
cd /path/to/mangalytics
python -m app.main
```

2. start frontend:
```bash
cd frontend
npm run dev
```

3. open http://localhost:3000
4. fill in email and topic
5. click subscribe
6. watch terminal logs for pipeline progress

### manual api testing

```bash
curl -X POST http://localhost:8000/subscribe \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "topic": "LLMs"
  }'
```

## timing expectations

typical pipeline execution time:

- **step 1 (scraping)**: 10-30 seconds
- **step 2 (reducto)**: 30-90 seconds per file (×1 file = 0.5-1.5 minutes)
- **step 3 (manga)**: 30-60 seconds

**total**: 1-3 minutes end-to-end

## monitoring

### backend logs

```
🚀 Starting subscription pipeline for user@example.com - LLMs
📥 STEP 1/3: Scraping and uploading PDFs from arXiv...
✓ Step 1 complete: Uploaded 5 PDFs

🔬 STEP 2/3: Processing PDFs with Reducto...
✓ Step 2 complete: Processed 1 file
  Extracted 4 figures total

🎨 STEP 3/3: Generating manga and sending email...
✓ Step 3 complete: Email sent! ID: abc123

✓ SUBSCRIPTION PIPELINE COMPLETE
```

### error logs

```
✗ Step 1 failed: Failed to upload PDFs: Connection timeout
✗ Step 2 failed: Reducto processing failed: API rate limit exceeded
✗ Step 3 failed: Email sending failed: Invalid API key
```

## supabase data structure

### after pipeline completion

**tables:**
- `recommendation_requests`: 1 row (one per processed file)
- `recommendation_pairings`: 4 rows (all extracted figures)

**storage buckets:**
- `documents/email/topic/date/`: 5 PDF files
- `reducto-images/email/topic/date/`: 4 figure PNGs
- `panels/email/topic/date/`: 4 panel PNGs + 1 JSON metadata

## customization

### adjust file limits

in `app/routers/subscriptions.py`:

```python
# process more files with reducto
RecommendationRequest(
    max_files=3  # default: 1
)

# use more files for manga
MangaGenerationRequest(
    max_files=2  # default: 1
)
```

### change search parameters

```python
SearchParams(
    terms=f"{topic} AND neural networks",  # more specific search
    size=100,  # get more results
    field="abstract"  # search in abstract instead of title
)
```

## production deployment

### cloud run configuration

the subscription endpoint should have:
- **timeout**: 900 seconds (15 minutes)
- **memory**: 2-4 GB
- **concurrency**: 1-10 (depends on reducto rate limits)

### async processing (future enhancement)

for production, consider:
- returning immediately with a job ID
- processing pipeline in background worker
- sending status updates via webhook
- storing progress in database

## troubleshooting

### pipeline stuck at step 2

**cause**: reducto api timeout or rate limit
**solution**: check reducto api key, increase timeout, reduce max_files

### email not received

**cause**: resend api key invalid or email bounced
**solution**: check resend dashboard, verify email address, check spam folder

### no figures extracted

**cause**: pdf is image-based or scanned document
**solution**: reducto may struggle with scanned pdfs, try different papers

### frontend timeout

**cause**: pipeline takes too long (>30 seconds)
**solution**: increase frontend timeout or implement async processing

## future enhancements

- [ ] async job processing with status polling
- [ ] webhook notifications for pipeline completion
- [ ] retry logic for failed steps
- [ ] pipeline progress bar in frontend
- [ ] email preview before sending
- [ ] multiple paper selection
- [ ] custom manga style preferences
- [ ] scheduled daily/weekly digests
