from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import cv2

from backend.app.database import init_db
from backend.app.api.routes import router as api_router
from backend.app.core.config import settings
from backend.app.utils.file_storage import OUTPUTS_DIR, UPLOADS_DIR
from backend.app.utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Boring 360 database and storage directories...")
    init_db()
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("Boring 360 backend is ready with OpenCV %s.", cv2.__version__)
    yield


app = FastAPI(
    title="BORING 360 API",
    description="Intelligent Smartphone Panorama Generation Platform API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount outputs directory to serve thumbnails and stitched panoramas directly
app.mount("/outputs", StaticFiles(directory=str(OUTPUTS_DIR)), name="outputs")

# Include main API router with /api prefix
app.include_router(api_router, prefix="/api")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)
