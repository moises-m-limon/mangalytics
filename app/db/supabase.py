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
        self.bucket_panels = "panels"

    async def check_file_already_processed(
        self,
        email: str,
        topic: str,
        file_name: str
    ) -> bool:
        """Check if a file has already been processed"""
        result = self.client.table("recommendation_requests").select("id").eq(
            "email", email
        ).eq("topic", topic).eq("file_name", file_name).execute()

        return len(result.data) > 0

    async def delete_existing_recommendation(
        self,
        email: str,
        topic: str,
        file_name: str
    ) -> None:
        """Delete existing recommendation records for a file (cascade will delete pairings)"""
        self.client.table("recommendation_requests").delete().eq(
            "email", email
        ).eq("topic", topic).eq("file_name", file_name).execute()

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

    async def insert_recommendation_pairings(
        self,
        request_id: str,
        pairings: List[Dict[str, Any]]
    ) -> None:
        """Insert multiple recommendation pairings with Reducto data"""
        records = [
            {
                "request_id": request_id,
                "figure_content": pairing["figure_content"],
                "image_path": pairing["image_path"],
                "reducto_data": pairing.get("reducto_block")  # Store full Reducto block data
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

    async def get_pairings_for_path(
        self,
        email: str,
        topic: str,
        date: str,
        max_files: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Get all recommendation pairings for files in a path

        Returns:
            List of dicts with 'figure_content', 'image_path', and 'image_data'
        """
        bucket_path = f"{email}/{topic}/{date}"

        # Get all PDF files in the path
        pdf_files = self.list_files_in_path(bucket_path)
        if not pdf_files:
            return []

        # Limit to max_files
        pdf_files = pdf_files[:max_files]

        all_pairings = []

        for file_path in pdf_files:
            # Query recommendation_requests for this file
            requests = self.client.table("recommendation_requests").select(
                "id, recommendation_pairings(figure_content, image_path, reducto_data)"
            ).eq("email", email).eq("topic", topic).eq("file_name", file_path).execute()

            if requests.data:
                for request in requests.data:
                    pairings = request.get("recommendation_pairings", [])

                    # Download image data for each pairing
                    for pairing in pairings:
                        try:
                            # Download image from storage
                            image_data = self.client.storage.from_(self.bucket_images).download(
                                pairing["image_path"]
                            )

                            all_pairings.append({
                                "figure_content": pairing["figure_content"],
                                "image_path": pairing["image_path"],
                                "image_data": image_data,
                                "reducto_data": pairing.get("reducto_data")
                            })
                        except Exception as e:
                            print(f"Warning: Could not download image {pairing['image_path']}: {e}")
                            continue

        return all_pairings

    def upload_image(
        self,
        image_path: str,
        image_data: bytes,
        content_type: str = "image/png"
    ) -> str:
        """Upload image to reducto-images bucket and return the path"""
        self.client.storage.from_(self.bucket_images).upload(
            image_path,
            image_data,
            {"content-type": content_type}
        )
        return image_path

    def upload_panel_image(
        self,
        image_path: str,
        image_data: bytes,
        content_type: str = "image/png"
    ) -> str:
        """Upload panel image to panels bucket and return the path"""
        self.client.storage.from_(self.bucket_panels).upload(
            image_path,
            image_data,
            {"content-type": content_type}
        )
        return image_path

    def get_public_url(self, image_path: str) -> str:
        """Get public URL for an image in reducto-images bucket"""
        result = self.client.storage.from_(self.bucket_images).get_public_url(image_path)
        return result

    def get_panel_public_url(self, image_path: str) -> str:
        """Get public URL for a panel image in panels bucket"""
        result = self.client.storage.from_(self.bucket_panels).get_public_url(image_path)
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

    def upload_manga_panels(
        self,
        file_path: str,
        content: str,
        content_type: str = "application/json"
    ) -> str:
        """
        Upload manga panels JSON to Supabase panels bucket

        Args:
            file_path: Path in format "email/topic/date/filename.json"
            content: JSON string or text content
            content_type: MIME type (default: application/json)

        Returns:
            The file path in storage
        """
        try:
            # Convert string to bytes
            content_bytes = content.encode('utf-8')

            self.client.storage.from_(self.bucket_panels).upload(
                file_path,
                content_bytes,
                {"content-type": content_type}
            )
            print(f"✓ Uploaded manga panels to {file_path}")
            return file_path
        except Exception as e:
            print(f"✗ Error uploading manga panels: {str(e)}")
            raise

    def get_panels_public_url(self, file_path: str) -> str:
        """Get public URL for manga panels in panels bucket"""
        result = self.client.storage.from_(self.bucket_panels).get_public_url(file_path)
        return result


supabase_db = SupabaseDB()
