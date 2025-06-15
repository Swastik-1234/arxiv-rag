import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import fitz as pymupdf
import httpx

from src.exceptions import PDFDownloadException, PDFParsingException, PDFValidationError

logger = logging.getLogger(__name__)

MAX_FILE_SIZE_MB = 50
MAX_PAGES = 50


class PDFParser:
    """Lightweight PDF parser using PyMuPDF."""

    async def download(
        self, url: str, arxiv_id: str, cache_dir: Path
    ) -> Optional[Path]:
        """Download PDF to local cache."""
        cache_dir.mkdir(parents=True, exist_ok=True)
        safe_name = arxiv_id.replace("/", "_") + ".pdf"
        pdf_path = cache_dir / safe_name

        # return cached if exists
        if pdf_path.exists():
            logger.info(f"Using cached PDF: {safe_name}")
            return pdf_path

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                pdf_path.write_bytes(response.content)
            logger.info(f"Downloaded PDF: {safe_name}")
            return pdf_path
        except httpx.TimeoutException:
            raise PDFDownloadException(f"Timeout downloading PDF: {arxiv_id}")
        except Exception as e:
            raise PDFDownloadException(f"Failed to download PDF {arxiv_id}: {e}")

    def validate(self, pdf_path: Path) -> None:
        """Validate PDF file."""
        if not pdf_path.exists():
            raise PDFValidationError(f"File not found: {pdf_path}")

        if pdf_path.stat().st_size == 0:
            raise PDFValidationError(f"Empty file: {pdf_path}")

        size_mb = pdf_path.stat().st_size / (1024 * 1024)
        if size_mb > MAX_FILE_SIZE_MB:
            raise PDFValidationError(
                f"File too large: {size_mb:.1f}MB > {MAX_FILE_SIZE_MB}MB"
            )

        with open(pdf_path, "rb") as f:
            if not f.read(8).startswith(b"%PDF-"):
                raise PDFValidationError(f"Not a valid PDF: {pdf_path}")

    def parse(self, pdf_path: Path) -> Dict[str, Any]:
        """Extract text and sections from PDF using PyMuPDF."""
        self.validate(pdf_path)

        try:
            doc = pymupdf.open(str(pdf_path))

            if len(doc) > MAX_PAGES:
                logger.warning(
                    f"PDF has {len(doc)} pages, processing first {MAX_PAGES}"
                )

            raw_text = ""
            sections: List[Dict[str, Any]] = []
            current_section = {"title": "Content", "content": ""}

            for page_num in range(min(len(doc), MAX_PAGES)):
                page = doc[page_num]
                blocks = page.get_text("dict")["blocks"]

                for block in blocks:
                    if block.get("type") != 0:  # text blocks only
                        continue
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            text = span.get("text", "").strip()
                            size = span.get("size", 0)

                            if not text:
                                continue

                            raw_text += text + " "

                            # detect headers by font size
                            if size > 12:
                                if current_section["content"].strip():
                                    sections.append(
                                        {
                                            "title": current_section["title"],
                                            "content": current_section[
                                                "content"
                                            ].strip(),
                                        }
                                    )
                                current_section = {"title": text, "content": ""}
                            else:
                                current_section["content"] += text + " "

            # add last section
            if current_section["content"].strip():
                sections.append(
                    {
                        "title": current_section["title"],
                        "content": current_section["content"].strip(),
                    }
                )

            doc.close()

            return {
                "raw_text": raw_text.strip(),
                "sections": sections,
            }

        except Exception as e:
            raise PDFParsingException(f"Failed to parse PDF {pdf_path.name}: {e}")
