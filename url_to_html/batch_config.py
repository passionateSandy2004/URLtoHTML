"""
Configuration for batch processing.
"""

from typing import Optional, Dict, List


class BatchFetcherConfig:
    """Configuration for batch URL fetching."""
    
    def __init__(
        self,
        # Static/XHR processing
        static_xhr_concurrency: int = 50,
        static_xhr_timeout: int = 30,
        static_xhr_headers: Optional[Dict[str, str]] = None,
        
        # Custom JS Service (Multi-Service)
        custom_js_service_endpoints: Optional[List[str]] = None,
        custom_js_batch_size: int = 20,
        custom_js_cooldown_seconds: int = 120,  # 2 minutes
        custom_js_timeout: int = 300,  # 5 minutes for batch
        
        # Decodo Web Scraping API (fallback only)
        decodo_enabled: bool = True,
        decodo_max_concurrent: int = 50,
        decodo_timeout: int = 180,
        decodo_headless_mode: str = "html",  # Kept for compatibility, not used
        decodo_location: Optional[str] = None,
        decodo_language: Optional[str] = None,
        decodo_target: str = "universal",
        decodo_device_type: str = "desktop",
        decodo_api_endpoint: Optional[str] = None,
        decodo_results_endpoint: Optional[str] = None,
        decodo_poll_interval: int = 2,
        decodo_max_poll_attempts: int = 30,
        
        # Content analyzer
        min_content_length: int = 1000,
        min_text_length: int = 200,
        min_meaningful_elements: int = 5,
        text_to_markup_ratio: float = 0.001,
        
        # General
        save_outputs: bool = True,
        output_dir: str = "outputs",
        enable_logging: bool = True
    ):
        """
        Initialize batch fetcher configuration.
        
        Args:
            static_xhr_concurrency: Max concurrent static/XHR requests
            static_xhr_timeout: Timeout for static/XHR requests
            static_xhr_headers: Custom headers for static/XHR
            
            custom_js_api_url: Custom JS rendering API endpoint
            custom_js_batch_size: URLs per batch (default: 20)
            custom_js_cooldown_seconds: Cooldown between batches (default: 120)
            custom_js_timeout: Timeout for batch requests
            
            decodo_enabled: Whether to use Decodo as fallback
            decodo_max_concurrent: Max concurrent Decodo polling requests (default: 50)
            decodo_timeout: Timeout for Decodo requests
            decodo_headless_mode: Not used (kept for compatibility)
            decodo_location: Decodo geographic location (e.g., "United States")
            decodo_language: Decodo language locale (e.g., "en-us")
            decodo_target: Scraping target template (default: "universal")
            decodo_device_type: Device type (default: "desktop")
            decodo_api_endpoint: Batch API endpoint (default: from env)
            decodo_results_endpoint: Results API endpoint base (default: from env)
            decodo_poll_interval: Polling interval in seconds (default: 2)
            decodo_max_poll_attempts: Max polling attempts per task (default: 30)
            
            min_content_length: Minimum content length threshold
            min_text_length: Minimum text length threshold
            min_meaningful_elements: Minimum meaningful elements
            text_to_markup_ratio: Text to markup ratio threshold
            
            save_outputs: Whether to save HTML outputs
            output_dir: Directory for saved outputs
            enable_logging: Whether to enable logging
        """
        # Static/XHR
        self.static_xhr_concurrency = static_xhr_concurrency
        self.static_xhr_timeout = static_xhr_timeout
        self.static_xhr_headers = static_xhr_headers or {}
        
        # Custom JS Service (Multi-Service)
        # Default service endpoints if not provided
        if custom_js_service_endpoints is None:
            custom_js_service_endpoints = [
                "easygoing-strength-copy-2-copy-2-production.up.railway.app",
                "easygoing-strength-copy-2-copy-1-production.up.railway.app",
                "easygoing-strength-copy-copy-1-production.up.railway.app",
                "easygoing-strength-copy-2-copy-production.up.railway.app",
                "easygoing-strength-copy-2-production.up.railway.app",
                "easygoing-strength-copy-production.up.railway.app",
                "easygoing-strength-copy-1-production.up.railway.app",
                "easygoing-strength-copy-copy-production.up.railway.app",
                "easygoing-strength-production-d985.up.railway.app",
                "easygoing-strength-copy-3-production.up.railway.app",
                "easygoing-strength-copy-copy-copy-2-production.up.railway.app",
                "easygoing-strength-copy-copy-copy-production.up.railway.app",
                "easygoing-strength-copy-copy-copy-1-production.up.railway.app",
            ]
        self.custom_js_service_endpoints = custom_js_service_endpoints
        self.custom_js_batch_size = custom_js_batch_size
        self.custom_js_cooldown_seconds = custom_js_cooldown_seconds
        self.custom_js_timeout = custom_js_timeout
        
        # Decodo Web Scraping API
        self.decodo_enabled = decodo_enabled
        self.decodo_max_concurrent = decodo_max_concurrent
        self.decodo_timeout = decodo_timeout
        self.decodo_headless_mode = decodo_headless_mode
        self.decodo_location = decodo_location
        self.decodo_language = decodo_language
        self.decodo_target = decodo_target
        self.decodo_device_type = decodo_device_type
        self.decodo_api_endpoint = decodo_api_endpoint
        self.decodo_results_endpoint = decodo_results_endpoint
        self.decodo_poll_interval = decodo_poll_interval
        self.decodo_max_poll_attempts = decodo_max_poll_attempts
        
        # Content analyzer
        self.min_content_length = min_content_length
        self.min_text_length = min_text_length
        self.min_meaningful_elements = min_meaningful_elements
        self.text_to_markup_ratio = text_to_markup_ratio
        
        # General
        self.save_outputs = save_outputs
        self.output_dir = output_dir
        self.enable_logging = enable_logging

