import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSON, UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Paper(Base):
    __tablename__ = "papers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    arxiv_id = Column(String(50), unique=True, nullable=False)
    title = Column(Text, nullable=False)
    authors = Column(ARRAY(String), nullable=False)
    abstract = Column(Text, nullable=False)
    categories = Column(ARRAY(String), nullable=False)
    published_date = Column(DateTime, nullable=False)
    pdf_url = Column(String(500), nullable=False)
    raw_text = Column(Text, nullable=True)
    sections = Column(JSON, nullable=True)
    pdf_processed = Column(Boolean, default=False)
    pdf_processing_date = Column(DateTime, nullable=True)
    is_embedded = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
