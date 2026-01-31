import os
import requests
from typing import List, Dict, Any
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()


class ReductoService:
    def __init__(self):
        self.api_key = os.getenv("REDUCTO_API_KEY")
        if not self.api_key:
            raise ValueError("Missing REDUCTO_API_KEY")

        self.base_url = "https://platform.reducto.ai"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

    async def process_pdf(self, pdf_bytes: bytes, file_name: str) -> List[Dict[str, Any]]:
        """
        Process PDF with Reducto API and extract figures with text

        Returns:
            List of dicts with 'figure_content' (text) and 'image_data' (bytes)
        """
        # Step 1: Upload the PDF file
        upload_response = requests.post(
            f"{self.base_url}/upload",
            headers=self.headers,
            files={"file": (file_name, pdf_bytes, "application/pdf")}
        )
        upload_response.raise_for_status()

        file_id = upload_response.json().get("file_id")
        if not file_id:
            raise ValueError("Failed to get file_id from Reducto upload")

        print(f"Uploaded to Reducto: {file_id}")

        # Step 2: Parse the document with comprehensive configuration
        parse_response = requests.post(
            f"{self.base_url}/parse",
            headers={**self.headers, "Content-Type": "application/json"},
            json={
                "input": f"reducto://{file_id}",
                "enhance": {
                    "agentic": [
                        {
                            "prompt": "Describe data trends and axes labels",
                            "scope": "figure"
                        },
                        {
                            "prompt": "Extract and preserve mathematical notation in LaTeX format, especially within table cells.",
                            "scope": "table"
                        },
                        {
                            "prompt": "Identify in-text citations (e.g., [1], [2] or Author et al.) and ensure they are mapped to the Bibliography/References section.",
                            "scope": "text"
                        }
                    ],
                    "summarize_figures": True
                },
                "formatting": {
                    "add_page_markers": False,
                    "include": [],
                    "merge_tables": False,
                    "table_output_format": "dynamic"
                },
                "retrieval": {
                    "chunking": {
                        "chunk_mode": "page",
                        "chunk_size": None
                    },
                    "filter_blocks": []
                },
                "settings": {
                    "extraction_mode": "hybrid",
                    "force_url_result": False,
                    "ocr_system": "standard",
                    "page_range": {"start": 1, "end": 5},
                    "persist_results": True,
                    "return_images": ["figure"],
                    "return_ocr_data": False,
                    "timeout": 900
                },
                "spreadsheet": {
                    "clustering": "accurate",
                    "exclude": [],
                    "include": [],
                    "split_large_tables": {
                        "enabled": True,
                        "size": 50
                    }
                }
            }
        )
        parse_response.raise_for_status()

        parse_data = parse_response.json()

        # The response might be async, check if we need to poll
        if "status" in parse_data and parse_data["status"] == "processing":
            job_id = parse_data.get("job_id")
            # Poll for results
            max_retries = 30
            for _ in range(max_retries):
                time.sleep(2)
                status_response = requests.get(
                    f"{self.base_url}/status/{job_id}",
                    headers=self.headers
                )
                status_data = status_response.json()
                if status_data.get("status") == "completed":
                    parse_data = status_data
                    break

        # Extract figures and their associated text
        pairings = []

        # Parse the result structure based on Reducto API response
        # Structure: result -> chunks -> blocks
        result = parse_data.get("result", {})
        chunks = result.get("chunks", [])

        figure_counter = 1

        for chunk in chunks:
            blocks = chunk.get("blocks", [])

            for block in blocks:
                block_type = block.get("type", "")

                # Look for Figure blocks (capital F based on API response)
                if block_type == "Figure":
                    # Extract text content from the content field
                    figure_content = block.get("content", "").strip()

                    if not figure_content:
                        figure_content = f"Figure {figure_counter}"

                    # Get image URL from image_url field
                    image_url = block.get("image_url")
                    image_data = None

                    if image_url:
                        try:
                            # Download the image
                            img_response = requests.get(image_url, timeout=30)
                            if img_response.status_code == 200:
                                image_data = img_response.content
                        except Exception as e:
                            print(f"Failed to download image from {image_url}: {str(e)}")
                            continue

                    if image_data:
                        pairings.append({
                            "figure_content": figure_content,
                            "image_data": image_data
                        })
                        print(f"✓ Extracted figure {figure_counter} with {len(figure_content)} chars of content")
                        figure_counter += 1

        return pairings


reducto_service = ReductoService()
