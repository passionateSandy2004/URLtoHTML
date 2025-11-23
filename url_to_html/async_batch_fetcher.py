"""
Main async batch fetcher that orchestrates all three phases.
"""

import logging
import time
import os
from typing import List, Dict, Optional
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
    
    logger.info(f"Phase 1 completed: {len(successful_urls)} successful, {len(js_urls)} need JS rendering")
    
    if not js_urls:
        # All URLs succeeded in Phase 1
        total_time = time.time() - start_time
        return aggregator.get_final_result(total_time)
    
    # Phase 2: Custom JS Rendering (Multi-Service)
    logger.info("=" * 80)
    logger.info("PHASE 2: Custom JS Rendering (Multi-Service)")
    logger.info("=" * 80)
    
    # Use multi-service renderer for parallel processing
    custom_js_renderer = AsyncMultiServiceJSRenderer(
        service_endpoints=config.custom_js_service_endpoints,
        batch_size=config.custom_js_batch_size,
        cooldown_seconds=config.custom_js_cooldown_seconds,
        timeout=config.custom_js_timeout
    )
    
    logger.info(f"Using {len(config.custom_js_service_endpoints)} services for parallel processing")
    
    phase2_results = await custom_js_renderer.process_urls(js_urls)
    
    # Separate successful and failed URLs
    # Also check successful results for skeleton content
    custom_js_successful = []
    decodo_urls = []
    
    # Initialize content analyzer for skeleton detection
    content_analyzer = ContentAnalyzer()
    
    for result in phase2_results:
        if result["status"] == "success":
            # Check if successful result is actually skeleton content
            if result["html"]:
                is_skeleton, skeleton_reason = content_analyzer.is_custom_js_skeleton(result["html"])
                if is_skeleton:
                    logger.info(f"Custom JS result for {result['url']} detected as skeleton: {skeleton_reason}")
                    decodo_urls.append(result["url"])
                    continue
            
            # Valid result, add to successful
            custom_js_successful.append(result)
            # Save output if configured
            if config.save_outputs and result["html"]:
                _save_html_to_file(
                    result["html"],
                    result["url"],
                    "custom_js",
                    config.output_dir
                )
        else:
            decodo_urls.append(result["url"])
    
    # Add successful custom JS results to aggregator
    for result in custom_js_successful:
        aggregator.add_result(
            url=result["url"],
            html=result["html"],
            method="custom_js",
            status="success",
            error=None
        )
    
    logger.info(f"Phase 2 completed: {len(custom_js_successful)} successful, {len(decodo_urls)} failed")
    
    if not decodo_urls or not config.decodo_enabled:
        # All URLs succeeded or Decodo disabled
        # Add failed URLs to aggregator
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

