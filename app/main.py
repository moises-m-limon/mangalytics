from fastapi import FastAPI
from dotenv import load_dotenv
import os

from app.routers import scraper, recommendations

load_dotenv()

app = FastAPI(
    title="Mangalytics API",
    version="2.0.0",
    description="API for scraping arXiv papers and generating recommendations with Reducto"
)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Mangalytics API is running",
        "status": "healthy",
        "version": "2.0.0"
    }


app.include_router(scraper.router)
app.include_router(recommendations.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
