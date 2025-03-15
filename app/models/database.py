"""Database models for the application."""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


class Job(Base):
    """Model for repository analysis jobs."""

    __tablename__ = "jobs"

    id = Column(String, primary_key=True)
    repo_url = Column(String, nullable=False)
    status = Column(String, nullable=False)
    message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
