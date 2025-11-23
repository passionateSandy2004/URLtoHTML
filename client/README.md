# URL to HTML Converter API - Client Libraries

Easy-to-use client libraries for the URL to HTML Converter API.

## Available Clients

- **Python Client** (`python_client.py`) - Full-featured Python client
- **JavaScript Client** (`javascript_client.js`) - Node.js and browser support

## Python Client

### Installation

The Python client requires the `requests` library:

```bash
pip install requests
```

### Quick Start

```python
from client import URLToHTMLClient

# Initialize client
client = URLToHTMLClient(base_url="http://localhost:8000")

# Fetch a batch of URLs
urls = [
    "https://example.com/page1",
    "https://example.com/page2",
    "https://example.com/page3"
]

response = client.fetch_batch(urls)

# Check results
print(f"Total: {response.summary.total}")
print(f"Success: {response.summary.success}")
print(f"Failed: {response.summary.failed}")
print(f"Success Rate: {response.summary.success_rate:.2f}%")
print(f"Processing Time: {response.summary.total_time:.2f}s")

# Get HTML content for successful URLs
for result in response.get_successful():
    print(f"{result.url}: {len(result.html)} bytes via {result.method}")

# Handle failures
for result in response.get_failed():
    print(f"Failed {result.url}: {result.error}")
```

### Advanced Usage

#### Custom Configuration

```python
# Configure for massive scaling
response = client.fetch_batch(
    urls,
    static_xhr_concurrency=200,  # Process 200 URLs in parallel
    custom_js_service_endpoints=[
        "service1.com",
        "service2.com",
        "service3.com",
        # ... add as many services as you have
    ],
    custom_js_batch_size=20,
    decodo_enabled=True
)
```

#### Single URL Fetching

```python
# Fetch a single URL (convenience method)
html = client.fetch_single("https://example.com")
if html:
    print(f"Got {len(html)} bytes of HTML")
```

#### Context Manager

```python
# Use as context manager for automatic cleanup
with URLToHTMLClient() as client:
    response = client.fetch_batch(urls)
    # Session automatically closed
```

#### Health Check

```python
# Check if API is healthy
health = client.health_check()
print(health['status'])  # 'healthy'
print(health['uptime'])  # Uptime in seconds
```

### API Reference

#### `URLToHTMLClient(base_url, timeout, verify_ssl)`

Initialize the client.

**Parameters:**
- `base_url` (str): Base URL of the API (default: "http://localhost:8000")
- `timeout` (int): Request timeout in seconds (default: 3600)
- `verify_ssl` (bool): Whether to verify SSL certificates (default: True)

#### `fetch_batch(urls, **kwargs) -> BatchResponse`

Fetch HTML content for a batch of URLs.

**Parameters:**
- `urls` (List[str]): List of URLs to fetch (1-10000 URLs)
- `static_xhr_concurrency` (int, optional): Max concurrent static/XHR requests
- `custom_js_service_endpoints` (List[str], optional): Custom JS rendering service endpoints
- `custom_js_batch_size` (int, optional): URLs per batch for custom JS
- `custom_js_cooldown_seconds` (int, optional): Cooldown between batches
- `custom_js_timeout` (int, optional): Timeout for custom JS batch requests
- `decodo_enabled` (bool, optional): Whether to use Decodo as fallback
- `decodo_timeout` (int, optional): Timeout for Decodo requests
- `min_content_length` (int, optional): Minimum content length threshold
- `min_text_length` (int, optional): Minimum text length threshold
- `save_outputs` (bool, optional): Whether to save HTML outputs to disk
- `enable_logging` (bool, optional): Whether to enable detailed logging

**Returns:** `BatchResponse` object

**Raises:** `requests.HTTPError` if the API request fails

#### `fetch_single(url, **kwargs) -> Optional[str]`

Fetch HTML content for a single URL.

**Parameters:**
- `url` (str): URL to fetch
- `**kwargs`: Configuration options (same as fetch_batch)

**Returns:** HTML content as string, or None if failed

#### `health_check() -> Dict[str, Any]`

Check API health.

**Returns:** Health status information

#### `get_api_info() -> Dict[str, Any]`

Get API information.

**Returns:** API information including version and endpoints

### Response Objects

#### `BatchResponse`

- `results` (List[URLResult]): List of results for each URL
- `summary` (BatchSummary): Summary statistics
- `success` (bool): Whether all URLs were successful
- `get_successful() -> List[URLResult]`: Get only successful results
- `get_failed() -> List[URLResult]`: Get only failed results
- `get_by_method(method: str) -> List[URLResult]`: Get results by method

#### `URLResult`

- `url` (str): The requested URL
- `html` (Optional[str]): Fetched HTML content
- `method` (Optional[str]): Method used ('static', 'xhr', 'custom_js', or 'decodo')
- `status` (str): Status ('success' or 'failed')
- `error` (Optional[str]): Error message if failed
- `is_success` (bool): Check if successful
- `is_failed` (bool): Check if failed

#### `BatchSummary`

- `total` (int): Total number of URLs processed
- `success` (int): Number of successful fetches
- `failed` (int): Number of failed fetches
- `by_method` (Dict[str, int]): Count of URLs by method used
- `total_time` (float): Total processing time in seconds
- `success_rate` (float): Success rate as percentage

## JavaScript Client

### Installation

For Node.js, no additional dependencies required (uses built-in `fetch` or `node-fetch`).

For browsers, the client works with native `fetch` API.

### Quick Start

#### Node.js

```javascript
const { URLToHTMLClient } = require('./client/javascript_client.js');

// Initialize client
const client = new URLToHTMLClient('http://localhost:8000');

// Fetch a batch of URLs
const urls = [
    'https://example.com/page1',
    'https://example.com/page2',
    'https://example.com/page3'
];

const response = await client.fetchBatch(urls);

// Check results
console.log(`Total: ${response.summary.total}`);
console.log(`Success: ${response.summary.success}`);
console.log(`Failed: ${response.summary.failed}`);

// Get HTML content for successful URLs
response.results
    .filter(r => r.status === 'success')
    .forEach(r => {
        console.log(`${r.url}: ${r.html.length} bytes via ${r.method}`);
    });
```

#### Browser

```html
<script src="javascript_client.js"></script>
<script>
    const client = new URLToHTMLClient('http://localhost:8000');
    
    const urls = ['https://example.com'];
    
    client.fetchBatch(urls)
        .then(response => {
            console.log(`Success: ${response.summary.success}`);
        })
        .catch(error => {
            console.error('Error:', error);
        });
</script>
```

### Advanced Usage

#### Custom Configuration

```javascript
const response = await client.fetchBatch(urls, {
    static_xhr_concurrency: 200,
    custom_js_service_endpoints: [
        'service1.com',
        'service2.com',
        'service3.com'
    ],
    custom_js_batch_size: 20,
    decodo_enabled: true
});
```

#### Single URL Fetching

```javascript
const html = await client.fetchSingle('https://example.com');
if (html) {
    console.log(`Got ${html.length} bytes of HTML`);
}
```

### API Reference

#### `URLToHTMLClient(baseUrl, timeout)`

Initialize the client.

**Parameters:**
- `baseUrl` (string): Base URL of the API (default: 'http://localhost:8000')
- `timeout` (number): Request timeout in milliseconds (default: 3600000)

#### `fetchBatch(urls, config) -> Promise<Object>`

Fetch HTML content for a batch of URLs.

**Parameters:**
- `urls` (string[]): List of URLs to fetch
- `config` (Object, optional): Configuration options

**Returns:** Promise resolving to batch response object

#### `fetchSingle(url, config) -> Promise<string|null>`

Fetch HTML content for a single URL.

**Parameters:**
- `url` (string): URL to fetch
- `config` (Object, optional): Configuration options

**Returns:** Promise resolving to HTML content or null

## Examples

### Example 1: Basic Batch Processing

```python
from client import URLToHTMLClient

client = URLToHTMLClient("http://localhost:8000")

urls = [
    "https://example.com/page1",
    "https://example.com/page2"
]

response = client.fetch_batch(urls)

for result in response.results:
    if result.is_success:
        print(f"✓ {result.url}: {len(result.html)} bytes")
    else:
        print(f"✗ {result.url}: {result.error}")
```

### Example 2: Massive Scaling

```python
from client import URLToHTMLClient

client = URLToHTMLClient("http://localhost:8000")

# Process 1000 URLs with 50 custom JS services
urls = [f"https://example.com/page{i}" for i in range(1000)]

services = [f"service{i}.com" for i in range(50)]

response = client.fetch_batch(
    urls,
    static_xhr_concurrency=200,
    custom_js_service_endpoints=services,
    custom_js_batch_size=20
)

print(f"Processed {response.summary.total} URLs in {response.summary.total_time:.2f}s")
print(f"Success rate: {response.summary.success_rate:.2f}%")
```

### Example 3: Error Handling

```python
from client import URLToHTMLClient
import requests

client = URLToHTMLClient("http://localhost:8000")

try:
    response = client.fetch_batch(["https://example.com"])
    
    if not response.success:
        print("Some URLs failed:")
        for result in response.get_failed():
            print(f"  {result.url}: {result.error}")
    
except requests.HTTPError as e:
    print(f"API error: {e}")
except requests.RequestException as e:
    print(f"Network error: {e}")
```

### Example 4: Processing Results

```python
from client import URLToHTMLClient

client = URLToHTMLClient("http://localhost:8000")

response = client.fetch_batch(urls)

# Group by method
by_method = {}
for result in response.results:
    method = result.method or "unknown"
    if method not in by_method:
        by_method[method] = []
    by_method[method].append(result)

# Print statistics
print("Results by method:")
for method, results in by_method.items():
    success_count = sum(1 for r in results if r.is_success)
    print(f"  {method}: {success_count}/{len(results)} successful")
```

## Scaling Tips

1. **Increase Static/XHR Concurrency**: For large batches, set `static_xhr_concurrency` to 200-500
2. **Add More Custom JS Services**: More services = more parallel processing
   - 13 services = 260 URLs simultaneously
   - 50 services = 1,000 URLs simultaneously
   - 100 services = 2,000 URLs simultaneously
3. **Adjust Batch Sizes**: Larger batches reduce overhead but increase memory usage
4. **Use Appropriate Timeouts**: Large batches may need longer timeouts

## Concurrent Requests Capacity

### How Many URLs Can It Handle?

The API can handle **unlimited concurrent requests**, but total throughput depends on custom JS services:

- **10 clients × 100 URLs = 1,000 URLs**: ✅ Works well with 13 services (~6-8 min)
- **50 clients × 100 URLs = 5,000 URLs**: ⚠️ Needs 50+ services (~20-30 min)
- **100 clients × 100 URLs = 10,000 URLs**: ⚠️ Needs 100+ services (~10-15 min)

### How It Works

- Each request is **independent** and processes asynchronously
- Static/XHR phase: 100 concurrent **per request** (no bottleneck)
- Custom JS phase: **Shared pool** of services (main bottleneck)
- Decodo phase: 3 concurrent **per request** (no bottleneck)

### Example: 10 Concurrent Clients

```python
from concurrent.futures import ThreadPoolExecutor
from client import URLToHTMLClient

def process_client(client_id, urls):
    client = URLToHTMLClient("https://urltohtml-production.up.railway.app")
    response = client.fetch_batch(urls)
    print(f"Client {client_id}: {response.summary.success} successful")
    client.close()

# 10 clients, each with 100 URLs
urls_per_client = 100
client_batches = [generate_urls(i, urls_per_client) for i in range(10)]

with ThreadPoolExecutor(max_workers=10) as executor:
    executor.map(process_client, range(10), client_batches)
```

**Result**: All 10 clients process simultaneously, sharing the custom JS service pool.

See `docs/CAPACITY_FAQ.md` for detailed capacity information.

## Error Handling

The client raises `requests.HTTPError` for API errors. Always handle exceptions:

```python
try:
    response = client.fetch_batch(urls)
except requests.HTTPError as e:
    print(f"API returned error: {e}")
    if e.response:
        error_data = e.response.json()
        print(f"Error details: {error_data}")
except requests.RequestException as e:
    print(f"Network error: {e}")
```

## Best Practices

1. **Use Context Managers**: Always use `with` statement for automatic cleanup
2. **Handle Errors**: Always wrap API calls in try-except blocks
3. **Check Health**: Use `health_check()` before processing large batches
4. **Monitor Progress**: Check `summary.total_time` to monitor performance
5. **Batch Size**: Keep batches reasonable (1000-5000 URLs per request)

