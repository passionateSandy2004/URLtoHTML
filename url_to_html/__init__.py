"""
URL to HTML Converter Library

A Python library that fetches HTML content from URLs using a progressive
fallback strategy: static fetch → XHR fetch → JS rendering.
"""

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv not installed, skip loading .env file
    pass

from .fetcher import fetch_html, FetcherConfig
from .js_renderer import JSrend
from .async_batch_fetcher import async_fetch_batch
from .batch_config import BatchFetcherConfig
from .exceptions import (
    FetchError,
    BlockedError,
    SkeletonContentError,
    TimeoutError,
    InvalidURLError,
    JSRenderError
)

__version__ = "0.1.0"
__all__ = [
    "fetch_html",
    "JSrend",
    "async_fetch_batch",
    "FetcherConfig",
    "BatchFetcherConfig",
    "FetchError",
    "BlockedError",
    "SkeletonContentError",
    "TimeoutError",
    "InvalidURLError",
    "JSRenderError",
]

