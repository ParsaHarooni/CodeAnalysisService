from pydantic import BaseModel, HttpUrl
from typing import List


class RepositoryAnalysisRequest(BaseModel):
    repo_url: HttpUrl


class AnalysisJobResponse(BaseModel):
    job_id: str


class FunctionAnalysisRequest(BaseModel):
    job_id: str
    function_name: str


class FunctionAnalysisResponse(BaseModel):
    suggestions: List[str]


class JobStatus(BaseModel):
    status: str
    message: str = ""
