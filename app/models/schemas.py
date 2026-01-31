from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime


class SearchParams(BaseModel):
    """Model for dynamic search parameters"""
    email: EmailStr
    topic: str
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


class RecommendationRequest(BaseModel):
    """Request model for recommendations endpoint"""
    email: EmailStr
    topic: str
    date: str
    max_files: int = 3  # Default to processing 3 files


class FigurePairing(BaseModel):
    """Model for figure/image pairing"""
    figure_content: str
    image_url: str


class FileRecommendation(BaseModel):
    """Model for a single file's recommendation"""
    file_name: str
    created_at: datetime
    pairings: List[FigurePairing]


class RecommendationResponse(BaseModel):
    """Response model for recommendations endpoint"""
    email: str
    topic: str
    date: str
    total_files_processed: int
    files: List[FileRecommendation]
