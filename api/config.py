"""
API configuration management.
"""

import os
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class APIConfig:
    """API configuration loaded from environment variables."""
    
    # Server configuration
    HOST: str = os.getenv("API_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("API_PORT", "8000"))
    WORKERS: int = int(os.getenv("API_WORKERS", "1"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # API configuration
    API_TITLE: str = os.getenv("API_TITLE", "URL to HTML Converter API")
    API_VERSION: str = os.getenv("API_VERSION", "1.0.0")
    API_DESCRIPTION: str = os.getenv(
        "API_DESCRIPTION",
        "Production-ready API for fetching HTML content from URLs using progressive fallback strategy"
    )
    
    # CORS configuration
    CORS_ORIGINS: List[str] = os.getenv(
        "CORS_ORIGINS",
        "*"  # Allow all origins by default
    ).split(",") if os.getenv("CORS_ORIGINS") != "*" else ["*"]
    
    # Default batch configuration
    DEFAULT_STATIC_XHR_CONCURRENCY: int = int(os.getenv("DEFAULT_STATIC_XHR_CONCURRENCY", "100"))
    DEFAULT_STATIC_XHR_TIMEOUT: int = int(os.getenv("DEFAULT_STATIC_XHR_TIMEOUT", "30"))
    DEFAULT_CUSTOM_JS_BATCH_SIZE: int = int(os.getenv("DEFAULT_CUSTOM_JS_BATCH_SIZE", "20"))
    DEFAULT_CUSTOM_JS_COOLDOWN: int = int(os.getenv("DEFAULT_CUSTOM_JS_COOLDOWN", "120"))
    DEFAULT_CUSTOM_JS_TIMEOUT: int = int(os.getenv("DEFAULT_CUSTOM_JS_TIMEOUT", "300"))
    DEFAULT_CUSTOM_JS_MAX_RETRIES: int = int(os.getenv("DEFAULT_CUSTOM_JS_MAX_RETRIES", "10"))
    DEFAULT_DECODO_ENABLED: bool = os.getenv("DEFAULT_DECODO_ENABLED", "true").lower() == "true"
    DEFAULT_DECODO_TIMEOUT: int = int(os.getenv("DEFAULT_DECODO_TIMEOUT", "180"))
    DEFAULT_DECODO_MAX_CONCURRENT: int = int(os.getenv("DEFAULT_DECODO_MAX_CONCURRENT", "50"))
    
    # Custom JS service endpoints (comma-separated)
    CUSTOM_JS_SERVICES: Optional[List[str]] = None
    if os.getenv("CUSTOM_JS_SERVICES"):
        CUSTOM_JS_SERVICES = [
            service.strip() 
            for service in os.getenv("CUSTOM_JS_SERVICES").split(",")
            if service.strip()
        ]
    
    # Domains that should skip custom JS entirely and go straight to Decodo
    CUSTOM_JS_SKIP_DOMAINS: Optional[List[str]] = None
    if os.getenv("CUSTOM_JS_SKIP_DOMAINS"):
        CUSTOM_JS_SKIP_DOMAINS = [
            domain.strip()
            for domain in os.getenv("CUSTOM_JS_SKIP_DOMAINS").split(",")
            if domain.strip()
        ]
    else:
        CUSTOM_JS_SKIP_DOMAINS = [
            "jiomart.com",
            "lotuselectronics.com",
            "croma.com",
            "adidas.co.in"
        ]
    
    # Decodo Web Scraping API credentials and configuration
    DECODO_USERNAME: Optional[str] = os.getenv("DECODO_USERNAME")
    DECODO_PASSWORD: Optional[str] = os.getenv("DECODO_PASSWORD")
    DECODO_API_ENDPOINT: Optional[str] = os.getenv(
        "DECODO_API_ENDPOINT",
        "https://scraper-api.decodo.com/v2/task/batch"
    )
    DECODO_RESULTS_ENDPOINT: Optional[str] = os.getenv(
        "DECODO_RESULTS_ENDPOINT",
        "https://scraper-api.decodo.com/v2/task"
    )
    DECODO_TARGET: str = os.getenv("DECODO_TARGET", "universal")
    DECODO_DEVICE_TYPE: str = os.getenv("DECODO_DEVICE_TYPE", "desktop")
    DECODO_POLL_INTERVAL: int = int(os.getenv("DECODO_POLL_INTERVAL", "2"))
    DECODO_MAX_POLL_ATTEMPTS: int = int(os.getenv("DECODO_MAX_POLL_ATTEMPTS", "30"))
    
    # Content analyzer defaults
    DEFAULT_MIN_CONTENT_LENGTH: int = int(os.getenv("DEFAULT_MIN_CONTENT_LENGTH", "1000"))
    DEFAULT_MIN_TEXT_LENGTH: int = int(os.getenv("DEFAULT_MIN_TEXT_LENGTH", "200"))
    
    # General settings
    DEFAULT_SAVE_OUTPUTS: bool = os.getenv("DEFAULT_SAVE_OUTPUTS", "false").lower() == "true"
    DEFAULT_OUTPUT_DIR: str = os.getenv("DEFAULT_OUTPUT_DIR", "outputs")
    DEFAULT_ENABLE_LOGGING: bool = os.getenv("DEFAULT_ENABLE_LOGGING", "true").lower() == "true"
    
    # Rate limiting (optional, for future use)
    MAX_REQUESTS_PER_MINUTE: Optional[int] = None
    if os.getenv("MAX_REQUESTS_PER_MINUTE"):
        MAX_REQUESTS_PER_MINUTE = int(os.getenv("MAX_REQUESTS_PER_MINUTE"))
    
    # Request limits
    MAX_URLS_PER_REQUEST: int = int(os.getenv("MAX_URLS_PER_REQUEST", "10000"))
    MAX_REQUEST_SIZE_MB: int = int(os.getenv("MAX_REQUEST_SIZE_MB", "100"))

