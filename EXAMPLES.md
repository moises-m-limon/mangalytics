# API Examples

## 1. Scrape and Upload PDFs

Upload PDFs from arXiv to Supabase storage.

### Request

```bash
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
```

### Response

```json
{
  "success": true,
  "uploaded_count": 5,
  "files": [
    "user@example.com/LLMs/01_31_2026/2301.12345.pdf",
    "user@example.com/LLMs/01_31_2026/2301.12346.pdf",
    "user@example.com/LLMs/01_31_2026/2301.12347.pdf",
    "user@example.com/LLMs/01_31_2026/2301.12348.pdf",
    "user@example.com/LLMs/01_31_2026/2301.12349.pdf"
  ],
  "errors": null
}
```

---

## 2. Create Recommendations

Process all PDFs in a bucket path with Reducto to extract figures and store them in Supabase.

### Request

```bash
curl -X POST "http://localhost:8000/recommendations" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "topic": "LLMs",
    "date": "01_31_2026",
    "max_files": 3
  }'
```

**Note:** `max_files` defaults to 3 if not specified. You can adjust this to process more or fewer files.

### Response

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
          "figure_content": "Figure 1: Architecture diagram",
          "image_url": "https://tsrqtoafjecskllsokpo.supabase.co/storage/v1/object/public/reducto-images/user@example.com/LLMs/01_31_2026/figure_1.png"
        },
        {
          "figure_content": "Figure 2: Performance comparison",
          "image_url": "https://tsrqtoafjecskllsokpo.supabase.co/storage/v1/object/public/reducto-images/user@example.com/LLMs/01_31_2026/figure_2.png"
        }
      ]
    },
    {
      "file_name": "user@example.com/LLMs/01_31_2026/2301.12346.pdf",
      "created_at": "2026-01-31T18:42:10Z",
      "pairings": [
        {
          "figure_content": "Figure 3: Training loss curves",
          "image_url": "https://tsrqtoafjecskllsokpo.supabase.co/storage/v1/object/public/reducto-images/user@example.com/LLMs/01_31_2026/figure_3.png"
        }
      ]
    }
  ]
}
```

---

## 3. Health Check

Check if the API is running.

### Request

```bash
curl -X GET "http://localhost:8000/"
```

### Response

```json
{
  "message": "Mangalytics API is running",
  "status": "healthy",
  "version": "2.0.0"
}
```

---

## Workflow

1. **First**: Use `/scraper/scrape-and-upload` to download PDFs from arXiv
2. **Then**: Use `/recommendations` with the email/topic/date path to process ALL PDFs in that folder

The files will be organized in storage as:
- **PDFs**: `documents/{email}/{topic}/{date}/{paper_id}.pdf`
- **Figures**: `reducto-images/{email}/{topic}/{date}/figure_{n}.png`

**Note**: The `/recommendations` endpoint processes ALL PDF files in the specified path (email/topic/date) automatically.
