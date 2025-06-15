from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ArxivPaper(BaseModel):
    """Schema for arXiv API response data."""

    arxiv_id: str = Field(..., description="arXiv paper ID")
    title: str = Field(..., description="Paper title")
    authors: List[str] = Field(..., description="List of author names")
    abstract: str = Field(..., description="Paper abstract")
    categories: List[str] = Field(..., description="Paper categories")
    published_date: str = Field(..., description="Publication date (ISO format)")
    pdf_url: str = Field(..., description="URL to PDF")


class PaperCreate(BaseModel):
    """Schema for creating a paper in the database."""

    arxiv_id: str
    title: str
    authors: List[str]
    abstract: str
    categories: List[str]
    published_date: datetime
    pdf_url: str

    # PDF content (added after parsing)
    raw_text: Optional[str] = None
    sections: Optional[List[Dict[str, Any]]] = None
    pdf_processed: bool = False
    pdf_processing_date: Optional[datetime] = None


class PaperResponse(BaseModel):
    """Schema for paper API responses."""

    id: UUID
    arxiv_id: str
    title: str
    authors: List[str]
    abstract: str
    categories: List[str]
    published_date: datetime
    pdf_url: str
    raw_text: Optional[str] = None
    sections: Optional[List[Dict[str, Any]]] = None
    pdf_processed: bool = False
    pdf_processing_date: Optional[datetime] = None
    is_embedded: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaperSearchResponse(BaseModel):
    """Schema for paginated paper list responses."""

    papers: List[PaperResponse]
    total: int
