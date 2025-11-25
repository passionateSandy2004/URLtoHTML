"""
Pydantic models for API request/response validation.
"""

from typing import List, Optional, Dict, Any, Union
try:
    from pydantic import BaseModel, Field, HttpUrl, field_validator
    PYDANTIC_V2 = True
except ImportError:
    from pydantic import BaseModel, Field, HttpUrl, validator as field_validator
    PYDANTIC_V2 = False


class BatchRequestConfig(BaseModel):
    """Optional configuration for batch processing."""
    
    # Static/XHR processing
    static_xhr_concurrency: Optional[int] = Field(default=None, ge=1, le=500, description="Max concurrent static/XHR requests (1-500)")
    static_xhr_timeout: Optional[int] = Field(default=None, ge=5, le=300, description="Timeout for static/XHR requests in seconds")
    
    # Custom JS Service
    custom_js_service_endpoints: Optional[List[str]] = Field(default=None, description="List of custom JS rendering service endpoints")
    custom_js_batch_size: Optional[int] = Field(default=None, ge=1, le=100, description="URLs per batch for custom JS (1-100)")
    custom_js_cooldown_seconds: Optional[int] = Field(default=None, ge=0, le=600, description="Cooldown between batches in seconds")
    custom_js_timeout: Optional[int] = Field(default=None, ge=30, le=600, description="Timeout for custom JS batch requests")
    custom_js_max_retries: Optional[int] = Field(default=None, ge=1, le=20, description="Max retry attempts for failed/skeleton URLs (1-20)")
    custom_js_skip_domains: Optional[List[str]] = Field(
        default=None,
        description="Domains that should skip custom JS entirely and go straight to Decodo"
    )
    
    # Decodo (fallback)
    decodo_enabled: Optional[bool] = Field(default=None, description="Whether to use Decodo as fallback")
    decodo_timeout: Optional[int] = Field(default=None, ge=30, le=600, description="Timeout for Decodo requests")
    
    # Content analyzer
    min_content_length: Optional[int] = Field(default=None, ge=100, description="Minimum content length threshold")
    min_text_length: Optional[int] = Field(default=None, ge=50, description="Minimum text length threshold")
    
    # General
    save_outputs: Optional[bool] = Field(default=None, description="Whether to save HTML outputs to disk")
    enable_logging: Optional[bool] = Field(default=None, description="Whether to enable detailed logging")


class BatchRequest(BaseModel):
    """Request model for batch URL fetching."""
    
    urls: List[Union[HttpUrl, str]] = Field(..., min_items=1, max_items=10000, description="List of URLs to fetch (1-10000 URLs)")
    config: Optional[BatchRequestConfig] = Field(default=None, description="Optional configuration overrides")
    
    if PYDANTIC_V2:
        @field_validator('urls')
        @classmethod
        def validate_urls(cls, v):
            """Validate URL list size."""
            if len(v) > 10000:
                raise ValueError("Maximum 10000 URLs per request")
            return v
    else:
        @field_validator('urls')
        def validate_urls(cls, v):
            """Validate URL list size."""
            if len(v) > 10000:
                raise ValueError("Maximum 10000 URLs per request")
            return v


class URLResult(BaseModel):
    """Individual URL result."""
    
    url: str = Field(..., description="The requested URL")
    html: Optional[str] = Field(default=None, description="Fetched HTML content (None if failed)")
    method: Optional[str] = Field(default=None, description="Method used: 'static', 'xhr', 'custom_js', or 'decodo'")
    status: str = Field(..., description="Status: 'success' or 'failed'")
    error: Optional[str] = Field(default=None, description="Error message if status is 'failed'")


class BatchSummary(BaseModel):
    """Summary statistics for batch processing."""
    
    total: int = Field(..., description="Total number of URLs processed")
    success: int = Field(..., description="Number of successful fetches")
    failed: int = Field(..., description="Number of failed fetches")
    by_method: Dict[str, int] = Field(..., description="Count of URLs by method used")
    total_time: float = Field(..., description="Total processing time in seconds")


class BatchResponse(BaseModel):
    """Response model for batch URL fetching."""
    
    results: List[URLResult] = Field(..., description="List of results for each URL")
    summary: BatchSummary = Field(..., description="Summary statistics")
    success: bool = Field(..., description="Whether the batch processing completed successfully")


class ErrorResponse(BaseModel):
    """Error response model."""
    
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(default=None, description="Detailed error information")
    status_code: int = Field(..., description="HTTP status code")


class HealthResponse(BaseModel):
    """Health check response."""
    
    status: str = Field(..., description="Service status: 'healthy' or 'unhealthy'")
    version: str = Field(..., description="API version")
    uptime: Optional[float] = Field(default=None, description="Service uptime in seconds")


class APIInfoResponse(BaseModel):
    """API information response."""
    
    name: str = Field(..., description="API name")
    version: str = Field(..., description="API version")
    description: str = Field(..., description="API description")
    endpoints: Dict[str, str] = Field(..., description="Available endpoints")

