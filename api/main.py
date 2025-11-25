"""
FastAPI application for URL to HTML converter API.
"""

import logging
import time
import asyncio
from typing import List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from api.config import APIConfig
from api.models import (
    BatchRequest,
    BatchResponse,
    URLResult,
    BatchSummary,
    ErrorResponse,
    HealthResponse,
    APIInfoResponse
)
from url_to_html.async_batch_fetcher import async_fetch_batch
from url_to_html.batch_config import BatchFetcherConfig

# Configure logging
logging.basicConfig(
    level=getattr(logging, APIConfig.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Track startup time for health checks
startup_time = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    # Startup
    logger.info("Starting URL to HTML Converter API")
    logger.info(f"API Version: {APIConfig.API_VERSION}")
    logger.info(f"Default static/XHR concurrency: {APIConfig.DEFAULT_STATIC_XHR_CONCURRENCY}")
    logger.info(f"Custom JS services: {len(APIConfig.CUSTOM_JS_SERVICES) if APIConfig.CUSTOM_JS_SERVICES else 0}")
    yield
    # Shutdown
    logger.info("Shutting down URL to HTML Converter API")


# Create FastAPI app
app = FastAPI(
    title=APIConfig.API_TITLE,
    version=APIConfig.API_VERSION,
    description=APIConfig.API_DESCRIPTION,
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=APIConfig.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            error="Validation Error",
            detail=str(exc),
            status_code=422
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal Server Error",
            detail=str(exc) if APIConfig.LOG_LEVEL == "DEBUG" else "An error occurred processing the request",
            status_code=500
        ).dict()
    )


@app.get("/", response_model=APIInfoResponse, tags=["Info"])
async def root():
    """Get API information."""
    return APIInfoResponse(
        name=APIConfig.API_TITLE,
        version=APIConfig.API_VERSION,
        description=APIConfig.API_DESCRIPTION,
        endpoints={
            "health": "/health",
            "batch_fetch": "/api/v1/fetch-batch",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    )


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint."""
    uptime = time.time() - startup_time
    return HealthResponse(
        status="healthy",
        version=APIConfig.API_VERSION,
        uptime=uptime
    )


@app.post("/api/v1/fetch-batch", response_model=BatchResponse, tags=["Batch Processing"])
async def fetch_batch(request: BatchRequest):
    """
    Fetch HTML content for a batch of URLs.
    
    Uses progressive fallback strategy:
    1. Static HTTP GET
    2. XHR/API fetch
    3. Custom JS rendering (multi-service parallel)
    4. Decodo fallback (for failed URLs)
    
    Supports massive scaling with configurable concurrency and unlimited custom JS services.
    """
    try:
        # Convert Pydantic HttpUrl to string
        url_strings = [str(url) for url in request.urls]
        
        logger.info(f"Received batch request for {len(url_strings)} URLs")
        
        # Build configuration from request and defaults
        config = BatchFetcherConfig(
            # Set Decodo defaults from APIConfig
            decodo_max_concurrent=APIConfig.DEFAULT_DECODO_MAX_CONCURRENT,
            decodo_target=APIConfig.DECODO_TARGET,
            decodo_device_type=APIConfig.DECODO_DEVICE_TYPE,
            decodo_api_endpoint=APIConfig.DECODO_API_ENDPOINT,
            decodo_results_endpoint=APIConfig.DECODO_RESULTS_ENDPOINT,
            decodo_poll_interval=APIConfig.DECODO_POLL_INTERVAL,
            decodo_max_poll_attempts=APIConfig.DECODO_MAX_POLL_ATTEMPTS
        )
        
        # Apply request config overrides if provided
        if request.config:
            req_config = request.config
            
            if req_config.static_xhr_concurrency is not None:
                config.static_xhr_concurrency = req_config.static_xhr_concurrency
            else:
                config.static_xhr_concurrency = APIConfig.DEFAULT_STATIC_XHR_CONCURRENCY
            
            if req_config.static_xhr_timeout is not None:
                config.static_xhr_timeout = req_config.static_xhr_timeout
            else:
                config.static_xhr_timeout = APIConfig.DEFAULT_STATIC_XHR_TIMEOUT
            
            if req_config.custom_js_service_endpoints is not None:
                config.custom_js_service_endpoints = req_config.custom_js_service_endpoints
            elif APIConfig.CUSTOM_JS_SERVICES:
                config.custom_js_service_endpoints = APIConfig.CUSTOM_JS_SERVICES
            
            if req_config.custom_js_batch_size is not None:
                config.custom_js_batch_size = req_config.custom_js_batch_size
            else:
                config.custom_js_batch_size = APIConfig.DEFAULT_CUSTOM_JS_BATCH_SIZE
            
            if req_config.custom_js_cooldown_seconds is not None:
                config.custom_js_cooldown_seconds = req_config.custom_js_cooldown_seconds
            else:
                config.custom_js_cooldown_seconds = APIConfig.DEFAULT_CUSTOM_JS_COOLDOWN
            
            if req_config.custom_js_timeout is not None:
                config.custom_js_timeout = req_config.custom_js_timeout
            else:
                config.custom_js_timeout = APIConfig.DEFAULT_CUSTOM_JS_TIMEOUT
            
            if req_config.custom_js_max_retries is not None:
                config.custom_js_max_retries = req_config.custom_js_max_retries
            else:
                config.custom_js_max_retries = APIConfig.DEFAULT_CUSTOM_JS_MAX_RETRIES
            
            if req_config.custom_js_skip_domains is not None:
                config.set_custom_js_skip_domains(req_config.custom_js_skip_domains)
            elif APIConfig.CUSTOM_JS_SKIP_DOMAINS:
                config.set_custom_js_skip_domains(APIConfig.CUSTOM_JS_SKIP_DOMAINS)
            
            if req_config.decodo_enabled is not None:
                config.decodo_enabled = req_config.decodo_enabled
            else:
                config.decodo_enabled = APIConfig.DEFAULT_DECODO_ENABLED
            
            if req_config.decodo_timeout is not None:
                config.decodo_timeout = req_config.decodo_timeout
            else:
                config.decodo_timeout = APIConfig.DEFAULT_DECODO_TIMEOUT
            
            if req_config.min_content_length is not None:
                config.min_content_length = req_config.min_content_length
            else:
                config.min_content_length = APIConfig.DEFAULT_MIN_CONTENT_LENGTH
            
            if req_config.min_text_length is not None:
                config.min_text_length = req_config.min_text_length
            else:
                config.min_text_length = APIConfig.DEFAULT_MIN_TEXT_LENGTH
            
            if req_config.save_outputs is not None:
                config.save_outputs = req_config.save_outputs
            else:
                config.save_outputs = APIConfig.DEFAULT_SAVE_OUTPUTS
            
            if req_config.enable_logging is not None:
                config.enable_logging = req_config.enable_logging
            else:
                config.enable_logging = APIConfig.DEFAULT_ENABLE_LOGGING
        else:
            # Use all defaults from APIConfig
            config.static_xhr_concurrency = APIConfig.DEFAULT_STATIC_XHR_CONCURRENCY
            config.static_xhr_timeout = APIConfig.DEFAULT_STATIC_XHR_TIMEOUT
            config.custom_js_batch_size = APIConfig.DEFAULT_CUSTOM_JS_BATCH_SIZE
            config.custom_js_cooldown_seconds = APIConfig.DEFAULT_CUSTOM_JS_COOLDOWN
            config.custom_js_timeout = APIConfig.DEFAULT_CUSTOM_JS_TIMEOUT
            config.custom_js_max_retries = APIConfig.DEFAULT_CUSTOM_JS_MAX_RETRIES
            if APIConfig.CUSTOM_JS_SKIP_DOMAINS:
                config.set_custom_js_skip_domains(APIConfig.CUSTOM_JS_SKIP_DOMAINS)
            config.decodo_enabled = APIConfig.DEFAULT_DECODO_ENABLED
            config.decodo_timeout = APIConfig.DEFAULT_DECODO_TIMEOUT
            config.min_content_length = APIConfig.DEFAULT_MIN_CONTENT_LENGTH
            config.min_text_length = APIConfig.DEFAULT_MIN_TEXT_LENGTH
            config.save_outputs = APIConfig.DEFAULT_SAVE_OUTPUTS
            config.enable_logging = APIConfig.DEFAULT_ENABLE_LOGGING
            
            if APIConfig.CUSTOM_JS_SERVICES:
                config.custom_js_service_endpoints = APIConfig.CUSTOM_JS_SERVICES
        
        # Process batch
        result = await async_fetch_batch(url_strings, config)
        
        # Convert results to response model
        url_results = [
            URLResult(
                url=r["url"],
                html=r.get("html"),
                method=r.get("method"),
                status=r["status"],
                error=r.get("error")
            )
            for r in result["results"]
        ]
        
        summary = BatchSummary(
            total=result["summary"]["total"],
            success=result["summary"]["success"],
            failed=result["summary"]["failed"],
            by_method=result["summary"]["by_method"],
            total_time=result["summary"]["total_time"]
        )
        
        logger.info(f"Batch processing completed: {summary.success} successful, {summary.failed} failed in {summary.total_time:.2f}s")
        
        return BatchResponse(
            results=url_results,
            summary=summary,
            success=summary.failed == 0
        )
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing batch: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

