from fastapi import FastAPI
from dotenv import load_dotenv
import os

from app.routers import scraper, recommendations, manga

load_dotenv()

app = FastAPI(
    title="Mangalytics API",
    version="3.0.0",
    description="API for scraping arXiv papers, generating recommendations with Reducto, and creating manga digests with Gemini"
)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Mangalytics API is running",
        "status": "healthy",
        "version": "3.0.0",
        "features": [
            "arXiv scraping",
            "Reducto figure extraction",
            "Gemini manga generation",
            "Resend email delivery"
        ]
    }


app.include_router(scraper.router)
app.include_router(recommendations.router)
app.include_router(manga.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
