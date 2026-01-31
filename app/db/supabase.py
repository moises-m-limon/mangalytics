from supabase import create_client, Client
import os
from typing import Dict, List, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class SupabaseDB:
    def __init__(self):
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        if not supabase_url or not supabase_key:
            raise ValueError("Missing Supabase credentials")

        self.client: Client = create_client(supabase_url, supabase_key)
        self.bucket_documents = os.getenv("SUPABASE_BUCKET", "documents")
        self.bucket_images = "reducto-images"

    async def insert_recommendation_request(
        self,
        email: str,
        topic: str,
        file_name: str
    ) -> str:
        """Insert a recommendation request and return the request_id"""
        result = self.client.table("recommendation_requests").insert({
            "email": email,
            "topic": topic,
            "file_name": file_name
        }).execute()

        return result.data[0]["id"]

    async def insert_recommendation_pairings(
        self,
        request_id: str,
        pairings: List[Dict[str, str]]
    ) -> None:
        """Insert multiple recommendation pairings"""
        records = [
            {
                "request_id": request_id,
                "figure_content": pairing["figure_content"],
                "image_path": pairing["image_path"]
            }
            for pairing in pairings
        ]

        self.client.table("recommendation_pairings").insert(records).execute()

    async def get_recommendation_with_pairings(
        self,
        request_id: str
    ) -> Dict[str, Any]:
        """Get recommendation request with its pairings"""
        request = self.client.table("recommendation_requests").select(
            "*, recommendation_pairings(*)"
        ).eq("id", request_id).execute()

        return request.data[0] if request.data else None

    def upload_image(
        self,
        image_path: str,
        image_data: bytes,
        content_type: str = "image/png"
    ) -> str:
        """Upload image to Supabase storage and return the path"""
        self.client.storage.from_(self.bucket_images).upload(
            image_path,
            image_data,
            {"content-type": content_type}
        )
        return image_path

    def get_public_url(self, image_path: str) -> str:
        """Get public URL for an image"""
        result = self.client.storage.from_(self.bucket_images).get_public_url(image_path)
        return result

    def download_pdf(self, file_path: str) -> bytes:
        """Download PDF from documents bucket"""
        result = self.client.storage.from_(self.bucket_documents).download(file_path)
        return result

    def list_files_in_path(self, path: str) -> List[str]:
        """List all files in a specific path in documents bucket"""
        try:
            result = self.client.storage.from_(self.bucket_documents).list(path)
            # Filter for PDF files only
            pdf_files = [
                f"{path}/{file['name']}"
                for file in result
                if file['name'].endswith('.pdf')
            ]
            return pdf_files
        except Exception as e:
            print(f"Error listing files in {path}: {str(e)}")
            return []


supabase_db = SupabaseDB()
