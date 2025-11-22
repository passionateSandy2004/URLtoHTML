"""
JS rendering via external REST API (Decodo).
"""

import logging
import os
import requests
import urllib3
from typing import Optional, Dict
from .exceptions import JSRenderError, TimeoutError

# Disable SSL warnings for Decodo proxy
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Decodo API credentials (loaded from environment variables)
DECODO_USERNAME = os.getenv("DECODO_USERNAME", "U0000325820")
DECODO_PASSWORD = os.getenv("DECODO_PASSWORD", "PW_19849a2d58cbbf2af5e39e3a38693d1ba")
DECODO_API_ENDPOINT = os.getenv("DECODO_API_ENDPOINT", "https://unblock.decodo.com:60000")
# IMPORTANT: Decodo can only process 3 URLs concurrently at a time
DECODO_MAX_CONCURRENT = 3

logger = logging.getLogger(__name__)


def JSrend(
    url: str,
    api_endpoint: Optional[str] = None,
    api_key: Optional[str] = None,
    timeout: int = 180,
    headers: Optional[Dict[str, str]] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    headless_mode: str = "html",
    location: Optional[str] = None,
    language: Optional[str] = None
) -> str:
    """
    Render JavaScript content via Decodo proxy API.
    
    Args:
        url: URL to render
        api_endpoint: Decodo proxy endpoint (default: https://unblock.decodo.com:60000)
        api_key: Not used (kept for compatibility)
        timeout: Request timeout in seconds (default: 180)
        headers: Additional headers to include
        username: Decodo username (required if api_endpoint is provided)
        password: Decodo password (required if api_endpoint is provided)
        headless_mode: Rendering mode - "html", "screenshot", etc. (default: "html")
        location: Geographic location (e.g., "us")
        language: Language locale (e.g., "en-US")
        
    Returns:
        Rendered HTML content as string
        
    Raises:
        JSRenderError: If rendering fails
        TimeoutError: If request times out
    """
    # Use default Decodo API endpoint if not provided
    if api_endpoint is None:
        api_endpoint = DECODO_API_ENDPOINT
    
    # Use hardcoded credentials if not provided
    if username is None:
        username = DECODO_USERNAME
    if password is None:
        password = DECODO_PASSWORD
    
    # Final check if credentials are still missing
    if not username or not password:
        print("JS rendering")
        logger.info("JS rendering required but credentials not configured")
        raise JSRenderError(
            "JS rendering required but Decodo credentials not configured. "
            "Please provide username and password parameters or configure them in the fetcher settings.",
            url=url,
            api_endpoint=api_endpoint
        )
    
    logger.info(f"Attempting JS rendering via Decodo for: {url}")
    
    # Build headers
    request_headers = {
        "X-SU-Headless": headless_mode,
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/128.0 Safari/537.36"
        ),
    }
    
    if location:
        request_headers["X-SU-Geo"] = location
    
    if language:
        request_headers["X-SU-Locale"] = language
    
    if headers:
        request_headers.update(headers)
    
    # Build proxy URL with authentication
    proxy_auth_url = f"https://{username}:{password}@unblock.decodo.com:60000"
    proxies = {
        "http": proxy_auth_url,
        "https": proxy_auth_url,
    }
    
    try:
        # Make GET request through Decodo proxy
        response = requests.get(
            url,
            headers=request_headers,
            proxies=proxies,
            timeout=timeout,
            verify=False  # Decodo uses self-signed certificates
        )
        
        response.raise_for_status()
        
        html = response.text
        logger.info(f"JS rendering successful: {len(html)} bytes")
        return html
    
    except requests.exceptions.Timeout:
        logger.error(f"JS rendering timeout for: {url}")
        raise TimeoutError(f"JS rendering request to {url} timed out after {timeout}s", url=url, timeout=timeout)
    
    except requests.exceptions.HTTPError as e:
        error_msg = f"JS rendering API returned status {e.response.status_code}"
        try:
            error_text = e.response.text[:200]
            if error_text:
                error_msg += f": {error_text}"
        except:
            pass
        logger.error(error_msg)
        raise JSRenderError(error_msg, url=url, api_endpoint=api_endpoint)
    
    except requests.exceptions.RequestException as e:
        logger.error(f"JS rendering request failed: {e}")
        raise JSRenderError(f"JS rendering request failed: {e}", url=url, api_endpoint=api_endpoint)
    
    except Exception as e:
        logger.error(f"JS rendering failed: {e}")
        raise JSRenderError(f"JS rendering failed: {e}", url=url, api_endpoint=api_endpoint)

