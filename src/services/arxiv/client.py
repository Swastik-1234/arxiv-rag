import asyncio
import logging
import time
import xml.etree.ElementTree as ET
from typing import List, Optional
from urllib.parse import quote, urlencode

import httpx

from src.exceptions import ArxivAPIException, ArxivAPITimeoutError, ArxivParseError
from src.schemas.arxiv.paper import ArxivPaper

logger = logging.getLogger(__name__)

BASE_URL = "https://export.arxiv.org/api/query"
NAMESPACES = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
}
RATE_LIMIT_DELAY = 3.0  # seconds between requests


class ArxivClient:
    """Client for fetching papers from arXiv API."""

    def __init__(self, categories: str, max_results: int = 50):
        self.categories = categories.split(",")
        self.max_results = max_results
        self._last_request_time: Optional[float] = None

    async def fetch_papers(self, max_results: Optional[int] = None) -> List[ArxivPaper]:
        """Fetch latest papers from arXiv for configured categories."""
        if max_results is None:
            max_results = self.max_results

        all_papers = []
        for category in self.categories:
            papers = await self._fetch_category(category.strip(), max_results)
            all_papers.extend(papers)

        logger.info(f"Fetched {len(all_papers)} papers total")
        return all_papers

    async def _fetch_category(
        self, category: str, max_results: int
    ) -> List[ArxivPaper]:
        """Fetch papers for a single category."""
        params = {
            "search_query": f"cat:{category}",
            "start": 0,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }

        url = f"{BASE_URL}?{urlencode(params, quote_via=quote, safe=':+[]')}"

        try:
            await self._rate_limit()

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()

            papers = self._parse_response(response.text)
            logger.info(f"Fetched {len(papers)} papers for {category}")
            return papers

        except httpx.TimeoutException as e:
            raise ArxivAPITimeoutError(f"arXiv API timed out: {e}")
        except httpx.HTTPStatusError as e:
            raise ArxivAPIException(f"arXiv API error {e.response.status_code}: {e}")
        except Exception as e:
            raise ArxivAPIException(f"Unexpected error: {e}")

    async def _rate_limit(self):
        """Respect arXiv rate limit of 3 seconds between requests."""
        if self._last_request_time is not None:
            elapsed = time.time() - self._last_request_time
            if elapsed < RATE_LIMIT_DELAY:
                await asyncio.sleep(RATE_LIMIT_DELAY - elapsed)
        self._last_request_time = time.time()

    def _parse_response(self, xml_data: str) -> List[ArxivPaper]:
        """Parse arXiv XML response into ArxivPaper objects."""
        try:
            root = ET.fromstring(xml_data)
            entries = root.findall("atom:entry", NAMESPACES)
            papers = []
            for entry in entries:
                paper = self._parse_entry(entry)
                if paper:
                    papers.append(paper)
            return papers
        except ET.ParseError as e:
            raise ArxivParseError(f"Failed to parse XML: {e}")

    def _parse_entry(self, entry: ET.Element) -> Optional[ArxivPaper]:
        """Parse a single entry from arXiv XML."""
        try:
            # ID
            id_elem = entry.find("atom:id", NAMESPACES)
            if id_elem is None or id_elem.text is None:
                return None
            arxiv_id = id_elem.text.split("/")[-1]

            # Title
            title_elem = entry.find("atom:title", NAMESPACES)
            title = (
                title_elem.text.strip().replace("\n", " ")
                if title_elem is not None
                else ""
            )

            # Authors
            authors = []
            for author in entry.findall("atom:author", NAMESPACES):
                name_elem = author.find("atom:name", NAMESPACES)
                if name_elem is not None and name_elem.text:
                    authors.append(name_elem.text.strip())

            # Abstract
            summary_elem = entry.find("atom:summary", NAMESPACES)
            abstract = (
                summary_elem.text.strip().replace("\n", " ")
                if summary_elem is not None
                else ""
            )

            # Published date
            published_elem = entry.find("atom:published", NAMESPACES)
            published = (
                published_elem.text.strip() if published_elem is not None else ""
            )

            # Categories
            categories = []
            for cat in entry.findall("atom:category", NAMESPACES):
                term = cat.get("term")
                if term:
                    categories.append(term)

            # PDF URL
            pdf_url = ""
            for link in entry.findall("atom:link", NAMESPACES):
                if link.get("type") == "application/pdf":
                    pdf_url = link.get("href", "")
                    break

            return ArxivPaper(
                arxiv_id=arxiv_id,
                title=title,
                authors=authors,
                abstract=abstract,
                categories=categories,
                published_date=published,
                pdf_url=pdf_url,
            )

        except Exception as e:
            logger.error(f"Failed to parse entry: {e}")
            return None
