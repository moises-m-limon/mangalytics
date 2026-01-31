# title and authors extraction

extracting paper title and authors from reducto api response and storing in database.

## overview

the reducto service now extracts title and authors from the beginning of PDF documents and stores them in the recommendation_requests table. this provides document-level metadata for each processed paper.

## changes made

### 1. reducto service (app/services/reducto.py)

updated to extract title and authors from reducto blocks:

```python
async def process_pdf(self, pdf_bytes: bytes, file_name: str) -> Dict[str, Any]:
    """
    Process PDF with Reducto API and extract title, authors, and figures

    Returns:
        Dict with 'title', 'authors', and 'pairings' (list of figure dicts)
    """
```

**extraction logic:**
- searches for blocks with `type="Title"` to extract paper title
- looks for the next `type="Text"` block after title for authors
- extracts from the beginning of the document (first occurrence)

**return structure:**
```python
{
    "title": "NeuroFaith: Evaluating LLM Self-Explanation...",
    "authors": "Milan Bhan*12 Jean-Noël Vittaut1...",
    "pairings": [
        {
            "figure_content": "Figure 1: Architecture",
            "image_data": bytes,
            "reducto_block": {...}
        }
    ]
}
```

### 2. database schema (db_migrations.sql)

added title and authors columns to recommendation_requests table:

```sql
CREATE TABLE IF NOT EXISTS recommendation_requests (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT NOT NULL,
  topic TEXT NOT NULL,
  file_name TEXT NOT NULL,
  title TEXT,
  authors TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

**migration for existing tables:**
```sql
ALTER TABLE recommendation_requests ADD COLUMN IF NOT EXISTS title TEXT;
ALTER TABLE recommendation_requests ADD COLUMN IF NOT EXISTS authors TEXT;
```

### 3. supabase db (app/db/supabase.py)

updated insert method to accept title and authors:

```python
async def insert_recommendation_request(
    self,
    email: str,
    topic: str,
    file_name: str,
    title: str = None,
    authors: str = None
) -> str:
    """Insert a recommendation request and return the request_id"""
    result = self.client.table("recommendation_requests").insert({
        "email": email,
        "topic": topic,
        "file_name": file_name,
        "title": title,
        "authors": authors
    }).execute()

    return result.data[0]["id"]
```

### 4. recommendations router (app/routers/recommendations.py)

updated to handle new reducto return structure:

```python
reducto_result = await reducto_service.process_pdf(pdf_bytes, file_path)
title = reducto_result.get("title")
authors = reducto_result.get("authors")
reducto_pairings = reducto_result.get("pairings", [])

# Insert with title and authors
request_id = await supabase_db.insert_recommendation_request(
    email=request.email,
    topic=request.topic,
    file_name=file_path,
    title=title,
    authors=authors
)
```

### 5. manga router (app/routers/manga.py)

updated to handle new reducto return structure:

```python
reducto_result = await reducto_service.process_pdf(pdf_bytes, file_path)
reducto_pairings = reducto_result.get("pairings", [])
```

## example reducto blocks

**title block:**
```json
{
  "type": "Title",
  "content": "NeuroFaith: Evaluating LLM Self-Explanation Faithfulness via Internal Representation Alignment",
  "bbox": {
    "height": 0.03977272727272727,
    "left": 0.15604575163398693,
    "page": 1,
    "top": 0.1148989898989899,
    "width": 0.6642156862745098
  },
  "confidence": "high"
}
```

**authors block (text after title):**
```json
{
  "type": "Text",
  "content": "Milan Bhan*12 Jean-Noël Vittaut1 Nicolas Chesneau2 Sarath Chandar3 Marie-Jeanne Lesot1",
  "bbox": {
    "height": 0.011363636363636364,
    "left": 0.17647058823529413,
    "page": 1,
    "top": 0.16477272727272727,
    "width": 0.6470588235294118
  },
  "confidence": "high"
}
```

## querying the data

### get all papers with titles and authors

```sql
SELECT
  id,
  email,
  topic,
  file_name,
  title,
  authors,
  created_at
FROM recommendation_requests
WHERE title IS NOT NULL;
```

### search by title keyword

```sql
SELECT *
FROM recommendation_requests
WHERE title ILIKE '%LLM%';
```

### search by author name

```sql
SELECT *
FROM recommendation_requests
WHERE authors ILIKE '%Bhan%';
```

### get papers with their figure count

```sql
SELECT
  rr.id,
  rr.title,
  rr.authors,
  COUNT(rp.id) as figure_count
FROM recommendation_requests rr
LEFT JOIN recommendation_pairings rp ON rr.id = rp.request_id
GROUP BY rr.id, rr.title, rr.authors;
```

## benefits

1. **metadata preservation**: paper title and authors stored at document level
2. **searchability**: easy to search papers by title or author
3. **organization**: better tracking of which papers were processed
4. **context**: provides context for the extracted figures
5. **backwards compatible**: null values allowed for existing records

## testing

### insert test data

```python
# the service will automatically extract title and authors
reducto_result = await reducto_service.process_pdf(pdf_bytes, "test.pdf")

request_id = await supabase_db.insert_recommendation_request(
    email="test@example.com",
    topic="LLMs",
    file_name="test.pdf",
    title=reducto_result.get("title"),
    authors=reducto_result.get("authors")
)
```

### verify extraction

```sql
SELECT title, authors
FROM recommendation_requests
ORDER BY created_at DESC
LIMIT 5;
```

## migration steps

1. run the database migration to add title and authors columns
2. restart the backend service to load updated code
3. process new PDFs - title and authors will be automatically extracted
4. existing records will have NULL for title and authors (can be backfilled if needed)

## notes

- title and authors are extracted from the first occurrence in the document
- if title or authors blocks are not found, values will be NULL
- the extraction looks for the Text block immediately after the Title block
- works with the existing reducto API configuration
- no changes needed to figure extraction - it still works the same way
