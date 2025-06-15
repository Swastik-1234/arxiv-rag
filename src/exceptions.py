class RepositoryException(Exception):
    """Base exception for repository errors."""


class PaperNotFound(RepositoryException):
    """Paper not found in database."""


class PaperNotSaved(RepositoryException):
    """Paper could not be saved."""


class ArxivAPIException(Exception):
    """Base exception for arXiv API errors."""


class ArxivAPITimeoutError(ArxivAPIException):
    """arXiv API request timed out."""


class ArxivParseError(ArxivAPIException):
    """Failed to parse arXiv API response."""


class PDFParsingException(Exception):
    """Base exception for PDF parsing errors."""


class PDFValidationError(PDFParsingException):
    """PDF file validation failed."""


class PDFDownloadException(Exception):
    """Base exception for PDF download errors."""


class PDFDownloadTimeoutError(PDFDownloadException):
    """PDF download timed out."""


class PipelineException(Exception):
    """Exception during pipeline execution."""


class LLMException(Exception):
    """Base exception for LLM errors."""


class ConfigurationError(Exception):
    """Invalid configuration."""
