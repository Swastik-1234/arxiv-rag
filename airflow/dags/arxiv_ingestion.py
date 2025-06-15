import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.python import PythonOperator

logger = logging.getLogger(__name__)

default_args = {
    "owner": "arxiv-rag",
    "depends_on_past": False,
    "start_date": datetime(2025, 1, 1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=10),
}

dag = DAG(
    "arxiv_paper_ingestion",
    default_args=default_args,
    description="Daily arXiv paper pipeline: fetch -> parse -> store to PostgreSQL",
    schedule="0 6 * * 1-5",
    max_active_runs=1,
    catchup=False,
    tags=["arxiv", "ingestion"],
)


def fetch_and_store(**context):
    import sys
    sys.path.insert(0, "/opt/airflow")
    import asyncio
    import os
    from datetime import datetime
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import Session
    from src.services.arxiv.client import ArxivClient
    from src.services.arxiv.pdf_parser import PDFParser
    from src.models.paper import Base, Paper

    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://arxiv_user:arxiv_password@postgres:5432/arxiv_db").replace("asyncpg", "psycopg2")
    CATEGORIES = os.getenv("ARXIV_CATEGORIES", "cs.AI,cs.LG,cs.CL")
    MAX_RESULTS = int(os.getenv("ARXIV_MAX_RESULTS", "10"))

    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)

    client = ArxivClient(categories=CATEGORIES, max_results=MAX_RESULTS)
    papers = asyncio.run(client.fetch_papers())
    logger.info(f"Fetched {len(papers)} papers")

    parser = PDFParser()
    cache_dir = Path("/tmp/pdf_cache")
    stored = 0
    skipped = 0

    for paper in papers:
        with Session(engine) as session:
            existing = session.execute(
                text("SELECT id FROM papers WHERE arxiv_id = :arxiv_id"),
                {"arxiv_id": paper.arxiv_id}
            ).fetchone()

            if existing:
                skipped += 1
                continue

            raw_text = None
            sections = None
            pdf_processed = False

            try:
                pdf_path = asyncio.run(parser.download(paper.pdf_url, paper.arxiv_id, cache_dir))
                if pdf_path:
                    result = parser.parse(pdf_path)
                    raw_text = result["raw_text"].replace("\x00", "") if result["raw_text"] else None
                    sections = result["sections"]
                    pdf_processed = True
            except Exception as e:
                logger.warning(f"PDF processing failed for {paper.arxiv_id}: {e}")

            try:
                db_paper = Paper(
                    arxiv_id=paper.arxiv_id,
                    title=paper.title,
                    authors=paper.authors,
                    abstract=paper.abstract,
                    categories=paper.categories,
                    published_date=datetime.fromisoformat(paper.published_date.replace("Z", "+00:00")),
                    pdf_url=paper.pdf_url,
                    raw_text=raw_text,
                    sections=sections,
                    pdf_processed=pdf_processed,
                    pdf_processing_date=datetime.utcnow() if pdf_processed else None,
                )
                session.add(db_paper)
                session.commit()
                stored += 1
            except Exception as e:
                session.rollback()
                logger.warning(f"Failed to store {paper.arxiv_id}: {e}")
                skipped += 1

    logger.info(f"Stored: {stored} | Skipped: {skipped}")
    return {"stored": stored, "skipped": skipped}


def cleanup(**context):
    import os
    cache_dir = Path("/tmp/pdf_cache")
    if not cache_dir.exists():
        return
    now = datetime.utcnow().timestamp()
    removed = 0
    for pdf in cache_dir.glob("*.pdf"):
        if now - pdf.stat().st_mtime > 7 * 24 * 3600:
            pdf.unlink()
            removed += 1
    logger.info(f"Removed {removed} old PDFs")


with dag:
    fetch_task = PythonOperator(
        task_id="fetch_and_store",
        python_callable=fetch_and_store,
    )

    cleanup_task = PythonOperator(
        task_id="cleanup",
        python_callable=cleanup,
    )

    fetch_task >> cleanup_task
