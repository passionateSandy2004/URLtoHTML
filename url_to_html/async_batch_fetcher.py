"""
Main async batch fetcher that orchestrates all three phases.
"""

import logging
import time
import os
from typing import List, Dict, Optional
from urllib.parse import urlparse
from .async_static_xhr_processor import AsyncStaticXHRProcessor
from .async_multi_service_js_renderer import AsyncMultiServiceJSRenderer
from .async_decodo_fallback import AsyncDecodoFallback
from .result_aggregator import ResultAggregator
from .batch_config import BatchFetcherConfig
from .content_analyzer import ContentAnalyzer

logger = logging.getLogger(__name__)


def _save_html_to_file(html_content: str, url: str, method: str, output_dir: str = "outputs") -> str:
    """Save HTML content to a file for verification."""
    os.makedirs(output_dir, exist_ok=True)
    
    from urllib.parse import urlparse
    parsed = urlparse(url)
    domain = parsed.netloc.replace('.', '_')
    path = parsed.path.replace('/', '_').strip('_') or 'index'
    query = parsed.query.replace('&', '_').replace('=', '_') if parsed.query else ''
    
    filename_base = f"{domain}_{path}"
    if query:
        filename_base += f"_{query[:50]}"
    filename_base = filename_base[:100]
    
    timestamp = int(time.time())
    filename = f"{method}_{filename_base}_{timestamp}.html"
    filename = "".join(c for c in filename if c.isalnum() or c in ('_', '-', '.'))
    
    filepath = os.path.join(output_dir, filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        logger.debug(f"Saved {method} output to: {filepath}")
        return filepath
    except Exception as e:
        logger.warning(f"Failed to save {method} output: {e}")
        return ""


def _extract_hostname(url: str) -> str:
    """Return normalized hostname (without www.) from URL."""
    parsed = urlparse(url)
    hostname = (parsed.netloc or parsed.path).lower()
    if hostname.startswith("www."):
        hostname = hostname[4:]
    return hostname


def _should_skip_custom_js(url: str, excluded_domains: Optional[List[str]]) -> bool:
    """Determine if URL should bypass custom JS based on configured domains."""
    if not excluded_domains:
        return False
    hostname = _extract_hostname(url)
    return any(
        hostname == domain or hostname.endswith(f".{domain}")
        for domain in excluded_domains
    )


async def async_fetch_batch(
    urls: List[str],
    config: Optional[BatchFetcherConfig] = None
) -> Dict[str, any]:
    """
    Process a batch of URLs with three-tier fallback strategy.
    
    Strategy:
    1. Phase 1: Static + XHR (high concurrency)
    2. Phase 2: Custom JS rendering (batches of 20, 2-min cooldown)
    3. Phase 3: Decodo fallback (3 concurrent, only for failed URLs)
    
    Args:
        urls: List of URLs to process
        config: BatchFetcherConfig instance (optional)
        
    Returns:
        Dictionary with results and summary
    """
    if config is None:
        config = BatchFetcherConfig()
    
    if config.enable_logging:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    start_time = time.time()
    aggregator = ResultAggregator()
    
    logger.info(f"Starting batch processing for {len(urls)} URLs")
    
    # Phase 1: Static + XHR Processing
    logger.info("=" * 80)
    logger.info("PHASE 1: Static + XHR Processing")
    logger.info("=" * 80)
    
    static_xhr_processor = AsyncStaticXHRProcessor(
        timeout=config.static_xhr_timeout,
        headers=config.static_xhr_headers,
        max_concurrent=config.static_xhr_concurrency
    )
    
    phase1_results = await static_xhr_processor.process_batch(urls)
    
    # Separate successful and URLs needing JS rendering
    successful_urls = []
    js_urls = []
    
    for result in phase1_results:
        if result["needs_js"]:
            js_urls.append(result["url"])
        else:
            successful_urls.append(result)
            # Save output if configured
            if config.save_outputs and result["html"]:
                _save_html_to_file(
                    result["html"],
                    result["url"],
                    result["method"],
                    config.output_dir
                )
    
    # Add successful results to aggregator
    for result in successful_urls:
        aggregator.add_result(
            url=result["url"],
            html=result["html"],
            method=result["method"],
            status="success",
            error=None
        )
    
    decodo_direct_urls = []
    if config.custom_js_skip_domains:
        filtered_js_urls = []
        for url in js_urls:
            if _should_skip_custom_js(url, config.custom_js_skip_domains):
                decodo_direct_urls.append(url)
            else:
                filtered_js_urls.append(url)
        js_urls = filtered_js_urls
    
    logger.info(f"Phase 1 completed: {len(successful_urls)} successful, {len(js_urls)} need JS rendering")
    if decodo_direct_urls:
        logger.info(f"{len(decodo_direct_urls)} URL(s) are configured to skip custom JS and will go directly to Decodo.")
    
    if not js_urls and not decodo_direct_urls:
        # All URLs succeeded in Phase 1
        total_time = time.time() - start_time
        return aggregator.get_final_result(total_time)
    
    custom_js_successful = []
    phase2_results = []
    decodo_urls = decodo_direct_urls.copy()
    
    if js_urls:
        # Phase 2: Custom JS Rendering (Multi-Service) with Retry
        logger.info("=" * 80)
        logger.info("PHASE 2: Custom JS Rendering (Multi-Service) with Retry")
        logger.info("=" * 80)
        
        # Use multi-service renderer for parallel processing
        custom_js_renderer = AsyncMultiServiceJSRenderer(
            service_endpoints=config.custom_js_service_endpoints,
            batch_size=config.custom_js_batch_size,
            cooldown_seconds=config.custom_js_cooldown_seconds,
            timeout=config.custom_js_timeout
        )
        
        logger.info(f"Using {len(config.custom_js_service_endpoints)} services for parallel processing")
        
        # Initialize content analyzer for skeleton detection
        content_analyzer = ContentAnalyzer()
        
        # Retry logic: up to N attempts for failed/skeleton URLs
        max_retries = config.custom_js_max_retries
        urls_to_process = js_urls.copy()
        
        for attempt in range(1, max_retries + 1):
            if not urls_to_process:
                break
            
            logger.info(f"Custom JS rendering attempt {attempt}/{max_retries} for {len(urls_to_process)} URLs")
            
            # Process current batch of URLs
            phase2_results = await custom_js_renderer.process_urls(urls_to_process)
            
            # Track URLs that need retry
            retry_urls = []
            
            for result in phase2_results:
                if result["status"] == "success":
                    # Check if successful result is actually skeleton content
                    if result["html"]:
                        is_skeleton, skeleton_reason = content_analyzer.is_custom_js_skeleton(
                            result["html"], 
                            url=result["url"]
                        )
                        if is_skeleton:
                            logger.info(f"Custom JS result for {result['url']} detected as skeleton: {skeleton_reason}")
                            retry_urls.append(result["url"])
                            continue
                    
                    # Valid result, add to successful
                    custom_js_successful.append(result)
                    logger.debug(f"Custom JS success for {result['url']} on attempt {attempt}")
                    
                    # Save output if configured
                    if config.save_outputs and result["html"]:
                        _save_html_to_file(
                            result["html"],
                            result["url"],
                            "custom_js",
                            config.output_dir
                        )
                else:
                    # Failed, add to retry list
                    logger.debug(f"Custom JS failed for {result['url']} on attempt {attempt}: {result.get('error', 'Unknown error')}")
                    retry_urls.append(result["url"])
            
            # Update URLs to process for next iteration
            urls_to_process = retry_urls
            
            if urls_to_process:
                logger.info(f"Attempt {attempt} completed: {len(custom_js_successful)} successful so far, {len(urls_to_process)} need retry")
            else:
                logger.info(f"All URLs succeeded after {attempt} attempts")
                break
        
        # After all retries, remaining failed URLs go to Decodo along with any direct-skip URLs
        decodo_urls.extend(urls_to_process)
    else:
        logger.info("Skipping custom JS rendering phase because no eligible URLs remain after applying exclusion rules.")
    
    # Add successful custom JS results to aggregator
    for result in custom_js_successful:
        aggregator.add_result(
            url=result["url"],
            html=result["html"],
            method="custom_js",
            status="success",
            error=None
        )
    
    if decodo_urls:
        logger.info(f"Phase 2 completed: {len(custom_js_successful)} successful, {len(decodo_urls)} queued for Decodo")
    else:
        logger.info(f"Phase 2 completed: {len(custom_js_successful)} successful, 0 failed")
    
    if not decodo_urls:
        # All URLs succeeded after custom JS
        for result in phase2_results:
            if result["status"] == "failed":
                aggregator.add_result(
                    url=result["url"],
                    html=None,
                    method="custom_js",
                    status="failed",
                    error=result["error"]
                )
        total_time = time.time() - start_time
        return aggregator.get_final_result(total_time)
    
    if not config.decodo_enabled:
        # Decodo disabled - mark remaining URLs as failed
        for result in phase2_results:
            if result["status"] == "failed":
                aggregator.add_result(
                    url=result["url"],
                    html=None,
                    method="custom_js",
                    status="failed",
                    error=result["error"]
                )
        logger.warning("Decodo fallback is disabled, but some URLs require Decodo processing. Marking them as failed.")
        for url in decodo_urls:
            aggregator.add_result(
                url=url,
                html=None,
                method="decodo",
                status="failed",
                error="Decodo fallback disabled"
            )
        total_time = time.time() - start_time
        return aggregator.get_final_result(total_time)
    
    # Phase 3: Decodo Fallback (only for failed URLs)
    logger.info("=" * 80)
    logger.info("PHASE 3: Decodo Fallback (only for failed URLs)")
    logger.info("=" * 80)
    
    decodo_fallback = AsyncDecodoFallback(
        timeout=config.decodo_timeout,
        headless_mode=config.decodo_headless_mode,
        location=config.decodo_location,
        language=config.decodo_language,
        target=config.decodo_target,
        device_type=config.decodo_device_type,
        api_endpoint=config.decodo_api_endpoint,
        results_endpoint=config.decodo_results_endpoint,
        max_concurrent=config.decodo_max_concurrent,
        poll_interval=config.decodo_poll_interval,
        max_poll_attempts=config.decodo_max_poll_attempts
    )
    
    phase3_results = await decodo_fallback.process_urls(decodo_urls)
    
    # Add Decodo results to aggregator
    for result in phase3_results:
        aggregator.add_result(
            url=result["url"],
            html=result["html"],
            method="decodo" if result["status"] == "success" else "custom_js",
            status=result["status"],
            error=result["error"]
        )
        
        # Save output if successful and configured
        if result["status"] == "success" and config.save_outputs and result["html"]:
            _save_html_to_file(
                result["html"],
                result["url"],
                "decodo",
                config.output_dir
            )
    
    logger.info(f"Phase 3 completed: {len(phase3_results)} URLs processed")
    
    # Final summary
    total_time = time.time() - start_time
    final_result = aggregator.get_final_result(total_time)
    
    logger.info("=" * 80)
    logger.info("BATCH PROCESSING COMPLETED")
    logger.info("=" * 80)
    logger.info(f"Total URLs: {final_result['summary']['total']}")
    logger.info(f"Successful: {final_result['summary']['success']}")
    logger.info(f"Failed: {final_result['summary']['failed']}")
    logger.info(f"By method: {final_result['summary']['by_method']}")
    logger.info(f"Total time: {final_result['summary']['total_time']:.2f}s")
    
    return final_result

