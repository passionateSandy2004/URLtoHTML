"""
Async Decodo fallback processor.
Only processes URLs that failed in custom JS rendering service.
Processes 3 URLs at a time (Decodo's limit).
"""

import logging
import os
import asyncio
import aiohttp
import urllib3
from typing import List, Dict, Optional
from .exceptions import JSRenderError, TimeoutError

# Disable SSL warnings for Decodo proxy
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Decodo API credentials (loaded from environment variables)
DECODO_USERNAME = os.getenv("DECODO_USERNAME", "U0000325820")
DECODO_PASSWORD = os.getenv("DECODO_PASSWORD", "PW_19849a2d58cbbf2af5e39e3a38693d1ba")
DECODO_API_ENDPOINT = os.getenv("DECODO_API_ENDPOINT", "https://unblock.decodo.com:60000")
DECODO_MAX_CONCURRENT = 3  # Decodo's hard limit

logger = logging.getLogger(__name__)


class AsyncDecodoFallback:
    """Async processor for Decodo fallback (only for failed URLs from custom service)."""
    
    def __init__(
        self,
        timeout: int = 180,
        headless_mode: str = "html",
        location: Optional[str] = None,
        language: Optional[str] = None
    ):
        """
        Initialize Decodo fallback processor.
        
        Args:
            timeout: Request timeout in seconds
            headless_mode: Rendering mode (default: "html")
            location: Geographic location (optional)
            language: Language locale (optional)
        """
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.headless_mode = headless_mode
        self.location = location
        self.language = language
        self.max_concurrent = DECODO_MAX_CONCURRENT
    
    def _build_headers(self) -> Dict[str, str]:
        """Build headers for Decodo requests."""
        headers = {
            "X-SU-Headless": self.headless_mode,
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/128.0 Safari/537.36"
            ),
        }
        
        if self.location:
            headers["X-SU-Geo"] = self.location
        
        if self.language:
            headers["X-SU-Locale"] = self.language
        
        return headers
    
    async def _process_single_url(
        self,
        session: aiohttp.ClientSession,
        url: str,
        proxy_url: str
    ) -> Dict[str, any]:
        """
        Process a single URL through Decodo proxy.
        
        Args:
            session: aiohttp session configured with proxy
            url: URL to render
            
        Returns:
            Result dictionary
        """
        headers = self._build_headers()
        
        try:
            async with session.get(url, headers=headers, proxy=proxy_url, ssl=False) as response:
                if response.status == 200:
                    html = await response.text()
                    logger.debug(f"Decodo rendering successful for {url}: {len(html)} bytes")
                    return {
                        "url": url,
                        "html": html,
                        "status": "success",
                        "error": None
                    }
                else:
                    error_text = await response.text()
                    error_msg = f"Decodo returned status {response.status}: {error_text[:200]}"
                    logger.warning(f"Decodo rendering failed for {url}: {error_msg}")
                    return {
                        "url": url,
                        "html": None,
                        "status": "failed",
                        "error": error_msg
                    }
                    
        except asyncio.TimeoutError:
            logger.warning(f"Decodo rendering timeout for {url}")
            return {
                "url": url,
                "html": None,
                "status": "failed",
                "error": f"Request timeout after {self.timeout.total}s"
            }
        except Exception as e:
            logger.warning(f"Decodo rendering failed for {url}: {e}")
            return {
                "url": url,
                "html": None,
                "status": "failed",
                "error": str(e)
            }
    
    async def process_urls(
        self,
        urls: List[str]
    ) -> List[Dict[str, any]]:
        """
        Process failed URLs through Decodo (3 at a time).
        
        Args:
            urls: List of URLs that failed in custom JS service
            
        Returns:
            List of result dictionaries
        """
        if not urls:
            return []
        
        logger.info(f"Processing {len(urls)} failed URLs through Decodo (max 3 concurrent)")
        
        # Build proxy URL with authentication
        proxy_url = f"http://{DECODO_USERNAME}:{DECODO_PASSWORD}@unblock.decodo.com:60000"
        
        # Configure connector
        connector = aiohttp.TCPConnector(limit=self.max_concurrent, ssl=False)
        
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def process_with_semaphore(url: str):
            async with semaphore:
                # Create session with proxy for each request
                async with aiohttp.ClientSession(
                    timeout=self.timeout,
                    connector=connector
                ) as session:
                    # Use proxy in the request
                    return await self._process_single_url(session, url, proxy_url)
        
        # Process all URLs with semaphore limiting to 3 concurrent
        tasks = [process_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error processing {urls[i]} through Decodo: {result}")
                processed_results.append({
                    "url": urls[i],
                    "html": None,
                    "status": "failed",
                    "error": str(result)
                })
            else:
                processed_results.append(result)
        
        successful = sum(1 for r in processed_results if r["status"] == "success")
        failed = len(processed_results) - successful
        logger.info(f"Decodo fallback completed: {successful} successful, {failed} failed")
        
        return processed_results

