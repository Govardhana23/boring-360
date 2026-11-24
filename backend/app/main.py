from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from backend.app.database import init_db
from backend.app.routes.panorama import router as panorama_router
from backend.app.utils.file_storage import OUTPUTS_DIR, UPLOADS_DIR
from backend.app.utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Boring 360 database and storage directories...")
    init_db()
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("Boring 360 backend is ready.")
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

# Include routers
app.include_router(panorama_router)


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Boring 360 Panorama Processing Engine",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)
