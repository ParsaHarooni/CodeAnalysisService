"""Main FastAPI application."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.core.config import settings
from app.core.database import get_db, init_db
from app.models.database import Job
from app.models.schemas import (
    RepositoryAnalysisRequest,
    AnalysisJobResponse,
    FunctionAnalysisRequest,
    FunctionAnalysisResponse,
)
from app.services.repository import RepositoryService
from app.api.job import router
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

repository_service = RepositoryService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for the FastAPI application."""
    # Startup
    logger.info("Initializing database...")
    await init_db()

    yield
    # Shutdown
    logger.info("Shutting down...")


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
)

# Include routers
app.include_router(router,)
