"""Test cases for the repository service."""

import os
import pytest
from uuid import UUID
from app.services.repository import RepositoryService


def test_generate_job_id() -> None:
    """Test job ID generation."""
    service = RepositoryService()
    job_id = service.generate_job_id()

    # Verify it's a valid UUID
    assert UUID(job_id)


def test_get_repo_path() -> None:
    """Test repository path generation."""
    service = RepositoryService()
    job_id = "test-job"
    expected_path = os.path.join(service.storage_path, job_id)
    assert service.get_repo_path(job_id) == expected_path


@pytest.mark.asyncio
async def test_clone_repository_invalid_url() -> None:
    """Test cloning from an invalid repository URL."""
    service = RepositoryService()
    job_id = "test-job"
    success = await service.clone_repository("https://invalid-url", job_id)
    assert not success
