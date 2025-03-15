"""API endpoints for the code analysis service."""

from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.core.config import settings
import logging

from app.core.database import get_db
from app.models.database import Job
from app.models.schemas import (
    RepositoryAnalysisRequest,
    AnalysisJobResponse,
    FunctionAnalysisRequest,
    FunctionAnalysisResponse,
)
from app.services.repository import RepositoryService

logger = logging.getLogger(__name__)
router = APIRouter()
repository_service = RepositoryService()


async def process_repository(
    job_id: str,
    repo_url: str,
    db: AsyncSession,
) -> None:
    """Background task to clone and process a repository."""
    try:
        logger.info(f"Starting repository clone for job {job_id}")
        success = await repository_service.clone_repository(repo_url, job_id)

        status = "completed" if success else "failed"
        message = (
            "Repository cloned successfully"
            if success
            else "Failed to clone repository"
        )

        stmt = (
            update(Job).where(Job.id == job_id).values(status=status, message=message)
        )
        await db.execute(stmt)
        await db.commit()

    except Exception as e:
        logger.error(f"Error processing repository: {str(e)}")
        stmt = (
            update(Job).where(Job.id == job_id).values(status="failed", message=str(e))
        )
        await db.execute(stmt)
        await db.commit()


@router.post("/analyze/start", response_model=AnalysisJobResponse)
async def start_analysis(
    request: RepositoryAnalysisRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> AnalysisJobResponse:
    """Start a background job to analyze a repository."""
    job_id = repository_service.generate_job_id()

    # Create new job in database
    job = Job(
        id=job_id,
        repo_url=str(request.repo_url),
        status="pending",
        message="Repository clone started",
    )
    db.add(job)
    await db.commit()

    # Start background task
    background_tasks.add_task(process_repository, job_id, str(request.repo_url), db)
    return AnalysisJobResponse(job_id=job_id)


@router.get("/analyze/status/{job_id}")
async def get_job_status(
    job_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get the status of a repository analysis job."""
    stmt = select(Job).where(Job.id == job_id)
    result = await db.execute(stmt)
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return {"status": job.status, "message": job.message}


@router.post("/analyze/function", response_model=FunctionAnalysisResponse)
async def analyze_function(
    request: FunctionAnalysisRequest,
    db: AsyncSession = Depends(get_db),
) -> FunctionAnalysisResponse:
    """Analyze a specific function from a previously downloaded repository.
    
    This endpoint performs the following steps:
    1. Validates that the job exists and is completed
    2. Retrieves the function code from the repository
    3. Sends the code to the LLM service for analysis
    4. Returns the suggestions from the LLM service
    
    The LLM service URL is configured via settings.LLM_SERVICE_URL
    """
    # Check if the job exists in the database
    stmt = select(Job).where(Job.id == request.job_id)
    result = await db.execute(stmt)
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Ensure the repository has been successfully cloned
    if job.status != "completed":
        raise HTTPException(
            status_code=400, detail="Repository analysis job is not completed"
        )

    # Extract the function code from the repository
    function_code = repository_service.get_function_code(
        request.job_id, request.function_name
    )
    if not function_code:
        raise HTTPException(status_code=404, detail="Function not found in repository")

    # Send the function code to the LLM service for analysis
    # The service is expected to return a JSON response with a suggestions array
    async with httpx.AsyncClient() as client:
        response = await client.post(
            settings.LLM_SERVICE_URL, json={"function_code": function_code}
        )
        suggestions = response.json().get("suggestions", [])

    return FunctionAnalysisResponse(suggestions=suggestions)
