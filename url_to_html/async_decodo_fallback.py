"""
Async Decodo Web Scraping API fallback processor.
Only processes URLs that failed in custom JS rendering service.
Uses Web Scraping API Advanced batch endpoint.
"""

import logging
import os
import asyncio
import aiohttp
import base64
from typing import List, Dict, Optional
from .exceptions import JSRenderError, TimeoutError

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Decodo API credentials (loaded from environment variables)
DECODO_USERNAME = os.getenv("DECODO_USERNAME")
DECODO_PASSWORD = os.getenv("DECODO_PASSWORD")
DECODO_BASIC_AUTH_TOKEN = os.getenv("DECODO_BASIC_AUTH_TOKEN")  # Optional: pre-encoded Basic Auth token
DECODO_API_ENDPOINT = os.getenv(
    "DECODO_API_ENDPOINT",
    "https://scraper-api.decodo.com/v2/task/batch"
)
DECODO_RESULTS_ENDPOINT = os.getenv(
    "DECODO_RESULTS_ENDPOINT",
    "https://scraper-api.decodo.com/v2/task"
)
DECODO_MAX_CONCURRENT = int(os.getenv("DECODO_MAX_CONCURRENT", "50"))
DECODO_POLL_INTERVAL = int(os.getenv("DECODO_POLL_INTERVAL", "2"))
DECODO_MAX_POLL_ATTEMPTS = int(os.getenv("DECODO_MAX_POLL_ATTEMPTS", "30"))

logger = logging.getLogger(__name__)


class AsyncDecodoFallback:
    """Async processor for Decodo Web Scraping API fallback (only for failed URLs from custom service)."""
    
    def __init__(
        self,
        timeout: int = 180,
        headless_mode: str = "html",  # Not directly used by new API, but kept for compatibility
        location: Optional[str] = None,
        language: Optional[str] = None,
        target: str = "universal",
        device_type: str = "desktop",
        api_endpoint: Optional[str] = None,
        results_endpoint: Optional[str] = None,
        poll_interval: int = DECODO_POLL_INTERVAL,
        max_poll_attempts: int = DECODO_MAX_POLL_ATTEMPTS,
        max_concurrent: int = DECODO_MAX_CONCURRENT
    ):
        """
        Initialize Decodo Web Scraping API fallback processor.
        
        Args:
            timeout: Request timeout in seconds
            headless_mode: Not used (kept for compatibility)
            location: Geographic location (e.g., "United States")
            language: Language locale (e.g., "en-us")
            target: Scraping target template (default: "universal")
            device_type: Device type (default: "desktop")
            api_endpoint: Batch API endpoint (default: from env or scraper-api.decodo.com/v2/task/batch)
            results_endpoint: Results API endpoint (default: from env or scraper-api.decodo.com/v2/task)
            poll_interval: Time in seconds to wait between polling attempts
            max_poll_attempts: Maximum number of polling attempts
            max_concurrent: Max concurrent polling requests (default: 50)
        """
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.location = location
        self.language = language
        self.target = target
        self.device_type = device_type
        self.api_endpoint = api_endpoint or DECODO_API_ENDPOINT
        self.results_endpoint = results_endpoint or DECODO_RESULTS_ENDPOINT
        self.poll_interval = poll_interval
        self.max_poll_attempts = max_poll_attempts
        self.max_concurrent = max_concurrent
        
        # Get credentials - support both username:password and Basic Auth Token
        self.username = DECODO_USERNAME
        self.password = DECODO_PASSWORD
        self.basic_auth_token = DECODO_BASIC_AUTH_TOKEN
        
        # Validate credentials
        if self.basic_auth_token:
            logger.debug("Using Basic Auth Token for Decodo authentication")
        elif self.username and self.password:
            logger.debug("Using username:password for Decodo authentication")
        else:
            logger.warning("Decodo credentials not configured. Web Scraping API will not work.")
            raise JSRenderError("Decodo credentials not configured. Please set DECODO_USERNAME/DECODO_PASSWORD or DECODO_BASIC_AUTH_TOKEN in .env")
    
    def _get_auth_header(self) -> str:
        """
        Get Authorization header for Decodo API.
        Supports both Basic Auth Token (pre-encoded) and username:password.
        
        Returns:
            Authorization header string (e.g., "Basic <token>")
        """
        if self.basic_auth_token:
            # Use pre-encoded Basic Auth Token directly
            return f"Basic {self.basic_auth_token}"
        elif self.username and self.password:
            # Generate Basic Auth from username:password
            credentials = f"{self.username}:{self.password}"
            encoded = base64.b64encode(credentials.encode()).decode()
            return f"Basic {encoded}"
        else:
            raise JSRenderError("No Decodo credentials available")
    
    async def _submit_batch(
        self,
        session: aiohttp.ClientSession,
        urls: List[str]
    ) -> Dict[str, any]:
        """
        Submit batch of URLs to Decodo Web Scraping API.
        
        Args:
            session: aiohttp session
            urls: List of URLs to process
            
        Returns:
            Batch response dictionary
        """
        # Build batch payload according to working test script format
        payload = {
            "url": urls,  # Array of URLs (note: "url" not "urls" as per working script)
            "target": self.target,
            "render_js": True,  # Force JS rendering
            "device_type": self.device_type,
            # Try to add wait/load parameters (may need Decodo support confirmation)
            "wait_for": "networkidle",  # Wait for network requests to finish (if supported)
            "timeout": 30000,  # 30 second timeout for rendering (if supported)
        }
        
        # Add optional parameters
        if self.location:
            payload["geo"] = self.location
        if self.language:
            payload["locale"] = self.language
        
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": self._get_auth_header()
            }
            
            logger.info(f"Submitting batch of {len(urls)} URLs to Decodo Web Scraping API")
            
            async with session.post(
                self.api_endpoint,
                json=payload,
                headers=headers,
                timeout=self.timeout,
                ssl=False
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"Decodo batch submission failed: status {response.status}, {error_text[:200]}")
                    return {"error": f"Status {response.status}: {error_text[:200]}"}
                    
        except asyncio.TimeoutError:
            logger.error("Decodo batch submission timeout")
            return {"error": "Request timeout"}
        except Exception as e:
            logger.error(f"Decodo batch submission error: {e}")
            return {"error": str(e)}
    
    def _extract_task_ids(self, batch_response: Dict[str, any]) -> Dict[str, Optional[str]]:
        """
        Extract task IDs from batch response and map them to URLs.
        Handles various response formats as shown in the working test script.
        
        Args:
            batch_response: Response from batch endpoint
            
        Returns:
            Dictionary mapping task_id (str) -> url (str or None)
        """
        task_map = {}
        
        # Handle different response formats
        task_entries = []
        if isinstance(batch_response, dict):
            if "queries" in batch_response and isinstance(batch_response["queries"], list):
                task_entries = batch_response["queries"]
            elif "tasks" in batch_response and isinstance(batch_response["tasks"], list):
                task_entries = batch_response["tasks"]
            elif isinstance(batch_response.get("id"), (str, int)) and "url" in batch_response:
                # single-task response fallback
                task_entries = [batch_response]
        elif isinstance(batch_response, list):
            task_entries = batch_response
        
        # Build mapping: task_id -> url
        for entry in task_entries:
            if isinstance(entry, dict):
                tid = entry.get("id") or entry.get("task_id") or entry.get("query_id")
                url_field = entry.get("url") or entry.get("query") or None
                if tid:
                    task_map[str(tid)] = url_field
            elif isinstance(entry, str):
                # sometimes API returns list of ids as strings
                task_map[entry] = None
        
        return task_map
    
    async def _poll_task_result(
        self,
        session: aiohttp.ClientSession,
        task_id: str,
        original_url: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Poll task result until completed or failed with robust error handling.
        Based on the working test script polling logic.
        
        Args:
            session: aiohttp session
            task_id: Task ID from batch submission
            original_url: Original URL (for mapping result)
            
        Returns:
            Result dictionary with status, html, and error fields
        """
        result_url = f"{self.results_endpoint}/{task_id}/results"
        headers = {"Authorization": self._get_auth_header()}
        
        waited = 0.0
        interval = float(self.poll_interval)
        max_wait = self.timeout.total
        consecutive_errors = 0
        max_consecutive_errors = 5  # Stop after 5 consecutive errors
        
        while waited < max_wait:
            try:
                async with session.get(
                    result_url,
                    headers=headers,
                    timeout=self.timeout,
                    ssl=False
                ) as response:
                    # Handle "not ready yet" status codes
                    if response.status in (404, 204):
                        # 404 = task not found yet, 204 = no content (still processing)
                        if waited == 0:
                            logger.debug(f"Task {task_id} not ready yet (status {response.status}), starting polling...")
                        consecutive_errors = 0  # Reset error counter on expected status
                        await asyncio.sleep(interval)
                        waited += interval
                        interval = min(interval * 1.2, 10.0)
                        continue
                    
                    # Handle server errors (500-599) with retry
                    if 500 <= response.status < 600:
                        error_text = await response.text()
                        consecutive_errors += 1
                        logger.warning(f"Server error for task {task_id} (consecutive #{consecutive_errors}): status {response.status}")
                        
                        if consecutive_errors >= max_consecutive_errors:
                            logger.error(f"Too many consecutive server errors ({consecutive_errors}) for task {task_id}, giving up")
                            return {
                                "url": original_url or "",
                                "html": None,
                                "status": "failed",
                                "error": f"Server error {response.status} after {consecutive_errors} attempts: {error_text[:100]}"
                            }
                        await asyncio.sleep(interval)
                        waited += interval
                        interval = min(interval * 1.5, 10.0)
                        continue
                    
                    # Handle client errors (400-499, except 404)
                    if 400 <= response.status < 500:
                        error_text = await response.text()
                        logger.error(f"Client error for task {task_id}: status {response.status}, {error_text[:200]}")
                        return {
                            "url": original_url or "",
                            "html": None,
                            "status": "failed",
                            "error": f"Client error {response.status}: {error_text[:200]}"
                        }
                    
                    # Handle unexpected status codes
                    if response.status != 200:
                        error_text = await response.text()
                        consecutive_errors += 1
                        logger.warning(f"Unexpected status {response.status} for task {task_id} (consecutive #{consecutive_errors})")
                        
                        if consecutive_errors >= max_consecutive_errors:
                            return {
                                "url": original_url or "",
                                "html": None,
                                "status": "failed",
                                "error": f"Unexpected status {response.status} after {consecutive_errors} attempts: {error_text[:200]}"
                            }
                        await asyncio.sleep(interval)
                        waited += interval
                        interval = min(interval * 1.5, 10.0)
                        continue
                    
                    # Try to parse JSON response
                    try:
                        data = await response.json()
                        consecutive_errors = 0  # Reset on successful parse
                    except aiohttp.ContentTypeError as e:
                        consecutive_errors += 1
                        logger.warning(f"Task {task_id}: Invalid JSON content type (consecutive #{consecutive_errors})")
                        
                        if consecutive_errors >= max_consecutive_errors:
                            return {
                                "url": original_url or "",
                                "html": None,
                                "status": "failed",
                                "error": f"Invalid JSON response after {consecutive_errors} attempts"
                            }
                        await asyncio.sleep(interval)
                        waited += interval
                        interval = min(interval * 1.5, 10.0)
                        continue
                    except Exception as e:
                        consecutive_errors += 1
                        logger.warning(f"Task {task_id}: JSON parse error (consecutive #{consecutive_errors}): {type(e).__name__}")
                        
                        if consecutive_errors >= max_consecutive_errors:
                            return {
                                "url": original_url or "",
                                "html": None,
                                "status": "failed",
                                "error": f"JSON parse error after {consecutive_errors} attempts: {type(e).__name__}"
                            }
                        await asyncio.sleep(interval)
                        waited += interval
                        interval = min(interval * 1.5, 10.0)
                        continue
                    
                    # Check task status
                    status = None
                    if isinstance(data, dict):
                        status = data.get("status") or data.get("state")
                    
                    # Check if task explicitly failed
                    if status in ("failed", "error"):
                        error_msg = None
                        if isinstance(data.get("error"), dict):
                            error_msg = data["error"].get("message") or data["error"].get("error")
                        elif isinstance(data.get("error"), str):
                            error_msg = data["error"]
                        error_msg = error_msg or data.get("message") or "Task failed (no error message)"
                        
                        logger.warning(f"Task {task_id} failed on Decodo side: {error_msg}")
                        return {
                            "url": original_url or data.get("url", ""),
                            "html": None,
                            "status": "failed",
                            "error": f"Decodo task failed: {error_msg}"
                        }
                    
                    # Check if task completed (status "done" or result fields present)
                    if status == "done" or "results" in data or "result" in data or "data" in data:
                        # Extract HTML from various possible response formats
                        html = None
                        
                        # Format 1: results array (most common for batch API)
                        if isinstance(data, dict) and "results" in data:
                            results_list = data["results"]
                            if results_list and isinstance(results_list, list) and len(results_list) > 0:
                                r0 = results_list[0]
                                html = r0.get("content") or r0.get("html") or r0.get("text")
                                # Check individual result status
                                result_status = r0.get("status")
                                if result_status == "failed":
                                    error_msg = r0.get("error") or "Result failed"
                                    logger.warning(f"Task {task_id} result failed: {error_msg}")
                                    return {
                                        "url": original_url or r0.get("url", ""),
                                        "html": None,
                                        "status": "failed",
                                        "error": f"Result failed: {error_msg}"
                                    }
                        
                        # Format 2: direct content/html/text fields
                        if not html and isinstance(data, dict):
                            html = data.get("html") or data.get("content") or data.get("text")
                        
                        # Success: HTML found
                        if html and len(html) > 0:
                            logger.debug(f"Task {task_id} completed successfully: {len(html)} bytes")
                            return {
                                "url": original_url or data.get("url", ""),
                                "html": html,
                                "status": "success",
                                "error": None
                            }
                        else:
                            # Task completed but no HTML
                            error_msg = data.get("error", {}).get("message") if isinstance(data.get("error"), dict) else data.get("error")
                            error_msg = error_msg or "Task completed but response contains no HTML content"
                            logger.warning(f"Task {task_id} completed but no HTML found for {original_url}")
                            return {
                                "url": original_url or data.get("url", ""),
                                "html": None,
                                "status": "failed",
                                "error": error_msg
                            }
                    
                    # Task still processing - wait and retry
                    logger.debug(f"Task {task_id} status: {status or 'unknown'}, waiting {interval:.1f}s...")
                    await asyncio.sleep(interval)
                    waited += interval
                    interval = min(interval * 1.2, 10.0)
                    
            except asyncio.TimeoutError:
                consecutive_errors += 1
                logger.warning(f"Polling timeout for task {task_id} (consecutive #{consecutive_errors})")
                
                if consecutive_errors >= max_consecutive_errors:
                    return {
                        "url": original_url or "",
                        "html": None,
                        "status": "failed",
                        "error": f"Request timeout after {consecutive_errors} attempts"
                    }
                
                await asyncio.sleep(interval)
                waited += interval
                interval = min(interval * 1.5, 10.0)
                
            except aiohttp.ClientError as e:
                consecutive_errors += 1
                logger.warning(f"Network error polling task {task_id} (consecutive #{consecutive_errors}): {type(e).__name__}: {str(e)[:100]}")
                
                if consecutive_errors >= max_consecutive_errors:
                    return {
                        "url": original_url or "",
                        "html": None,
                        "status": "failed",
                        "error": f"Network error after {consecutive_errors} attempts: {type(e).__name__}"
                    }
                
                await asyncio.sleep(interval)
                waited += interval
                interval = min(interval * 1.5, 10.0)
                
            except Exception as e:
                logger.error(f"Unexpected error polling task {task_id} for {original_url}: {type(e).__name__}: {str(e)[:200]}")
                return {
                    "url": original_url or "",
                    "html": None,
                    "status": "failed",
                    "error": f"Unexpected error: {type(e).__name__}: {str(e)[:200]}"
                }
        
        # Max wait time reached without completion
        logger.warning(f"Task {task_id} for {original_url} did not complete within {max_wait}s (waited: {waited:.1f}s)")
        return {
            "url": original_url or "",
            "html": None,
            "status": "failed",
            "error": f"Polling timeout: task did not complete within {max_wait}s"
        }
    
    async def process_urls(
        self,
        urls: List[str]
    ) -> List[Dict[str, any]]:
        """
        Process failed URLs through Decodo Web Scraping API (batch processing with polling).
        
        Args:
            urls: List of URLs that failed in custom JS service
            
        Returns:
            List of result dictionaries
        """
        if not urls:
            return []
        
        # Check credentials (either username:password or Basic Auth Token)
        if not self.basic_auth_token and (not self.username or not self.password):
            logger.error("Decodo credentials not configured. Cannot process URLs.")
            return [
                {
                    "url": url,
                    "html": None,
                    "status": "failed",
                    "error": "Decodo credentials not configured"
                }
                for url in urls
            ]
        
        logger.info(f"Processing {len(urls)} failed URLs through Decodo Web Scraping API (max {self.max_concurrent} concurrent polls)")
        
        # Create session for batch submission and polling
        connector = aiohttp.TCPConnector(limit=self.max_concurrent, ssl=False)
        
        async with aiohttp.ClientSession(
            timeout=self.timeout,
            connector=connector
        ) as session:
            # Step 1: Submit batch request
            batch_response = await self._submit_batch(session, urls)
            
            if "error" in batch_response:
                error_msg = batch_response.get("error", "Failed to submit batch to Decodo API")
                logger.error(f"Failed to submit batch to Decodo API: {error_msg}")
                return [
                    {
                        "url": url,
                        "html": None,
                        "status": "failed",
                        "error": error_msg
                    }
                    for url in urls
                ]
            
            # Step 2: Extract task IDs from batch response
            task_map = self._extract_task_ids(batch_response)
            
            if not task_map:
                logger.error("No task IDs received from Decodo batch submission")
                logger.debug(f"Batch response: {batch_response}")
                return [
                    {
                        "url": url,
                        "html": None,
                        "status": "failed",
                        "error": "No task IDs received from batch submission"
                    }
                    for url in urls
                ]
            
            logger.info(f"Received {len(task_map)} task IDs, starting polling")
            
            # Step 3: Poll results concurrently
            semaphore = asyncio.Semaphore(self.max_concurrent)
            
            async def poll_with_semaphore(task_id: str, url: Optional[str]):
                async with semaphore:
                    return await self._poll_task_result(session, task_id, url)
            
            # Create polling tasks
            polling_tasks = [
                poll_with_semaphore(task_id, url)
                for task_id, url in task_map.items()
            ]
            
            # Execute all polling tasks concurrently
            poll_results = await asyncio.gather(*polling_tasks, return_exceptions=True)
            
            # Map poll results back to URLs
            task_id_to_result = {
                task_id: result
                for task_id, result in zip(task_map.keys(), poll_results)
            }
            
            # Build final results list, ensuring all URLs have results
            processed_results = []
            url_to_task_id = {url: tid for tid, url in task_map.items() if url}
            
            for url in urls:
                task_id = url_to_task_id.get(url)
                if task_id and task_id in task_id_to_result:
                    result = task_id_to_result[task_id]
                    if isinstance(result, Exception):
                        logger.error(f"Error polling task {task_id} for {url}: {result}")
                        processed_results.append({
                            "url": url,
                            "html": None,
                            "status": "failed",
                            "error": str(result)
                        })
                    else:
                        # Update URL in result to match original
                        result["url"] = url
                        processed_results.append(result)
                else:
                    # URL didn't get a task ID or result
                    processed_results.append({
                        "url": url,
                        "html": None,
                        "status": "failed",
                        "error": "No task ID assigned for this URL"
                    })
        
        successful = sum(1 for r in processed_results if r["status"] == "success")
        failed = len(processed_results) - successful
        logger.info(f"Decodo Web Scraping API fallback completed: {successful} successful, {failed} failed")
        
        return processed_results
