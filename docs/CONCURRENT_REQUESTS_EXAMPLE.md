# Concurrent Requests Example

This document demonstrates how the API handles multiple concurrent requests.

## Test Scenario

**10 clients** each requesting **100 URLs** simultaneously = **1,000 total URLs**

## How It Works

### Architecture

```
Client 1 (100 URLs) ──┐
Client 2 (100 URLs) ──┤
Client 3 (100 URLs) ──┤
...                   ├──> API Server (FastAPI - Async)
Client 10 (100 URLs) ─┘

Each request processed independently:
├─ Request 1: 100 URLs → Static/XHR (100 concurrent) → Custom JS (shared pool)
├─ Request 2: 100 URLs → Static/XHR (100 concurrent) → Custom JS (shared pool)
├─ Request 3: 100 URLs → Static/XHR (100 concurrent) → Custom JS (shared pool)
...
└─ Request 10: 100 URLs → Static/XHR (100 concurrent) → Custom JS (shared pool)
```

### Processing Flow

1. **All 10 requests arrive simultaneously**
2. **Each request starts processing independently**:
   - Static/XHR phase: 100 concurrent per request
   - Total: 1,000 parallel static/XHR fetches
3. **Custom JS phase (shared pool)**:
   - 13 services available
   - 260 URLs processed simultaneously
   - Requests queue and wait for available services
4. **Decodo fallback**:
   - Each request: 3 concurrent
   - Total: 30 concurrent Decodo requests

### Capacity Breakdown

| Phase | Per Request | Total (10 requests) | Status |
|-------|-------------|---------------------|--------|
| Static/XHR | 100 concurrent | 1,000 concurrent | ✅ Excellent |
| Custom JS | Shared pool | 260 at a time | ⚠️ Queue forms |
| Decodo | 3 concurrent | 30 concurrent | ✅ Good |

## Example Code: Multiple Concurrent Clients

```python
import asyncio
from client import URLToHTMLClient

async def process_batch(client_id, urls):
    """Process a batch of URLs for a client."""
    client = URLToHTMLClient(
        base_url="https://urltohtml-production.up.railway.app",
        timeout=3600
    )
    
    try:
        print(f"Client {client_id}: Starting {len(urls)} URLs...")
        response = client.fetch_batch(urls)
        print(f"Client {client_id}: Completed - {response.summary.success} successful")
        return response
    finally:
        client.close()

async def main():
    # 10 clients, each with 100 URLs
    urls_per_client = 100
    num_clients = 10
    
    # Generate URLs for each client
    all_urls = [
        f"https://example.com/page{i}" 
        for i in range(num_clients * urls_per_client)
    ]
    
    # Split into batches for each client
    client_batches = [
        all_urls[i:i + urls_per_client]
        for i in range(0, len(all_urls), urls_per_client)
    ]
    
    # Process all clients concurrently
    print(f"Starting {num_clients} concurrent clients...")
    print(f"Total URLs: {num_clients * urls_per_client}")
    print()
    
    tasks = [
        process_batch(i + 1, batch)
        for i, batch in enumerate(client_batches)
    ]
    
    # Wait for all to complete
    results = await asyncio.gather(*tasks)
    
    # Summary
    total_success = sum(r.summary.success for r in results)
    total_failed = sum(r.summary.failed for r in results)
    total_time = max(r.summary.total_time for r in results)
    
    print()
    print("=" * 60)
    print("ALL CLIENTS COMPLETED")
    print("=" * 60)
    print(f"Total URLs: {num_clients * urls_per_client}")
    print(f"Successful: {total_success}")
    print(f"Failed: {total_failed}")
    print(f"Total Time: {total_time:.2f}s")

if __name__ == "__main__":
    asyncio.run(main())
```

## Expected Behavior

### With 13 Custom JS Services

- **Static/XHR**: All 1,000 URLs processed quickly (parallel)
- **Custom JS**: 
  - First 260 URLs processed immediately
  - Remaining 740 URLs queue
  - Processed in waves (260 at a time, 2-minute cooldown)
  - **Total time**: ~6-8 minutes

### With 50 Custom JS Services

- **Static/XHR**: All 1,000 URLs processed quickly
- **Custom JS**:
  - First 1,000 URLs processed in ~2 waves
  - **Total time**: ~4-5 minutes

### With 100 Custom JS Services

- **Static/XHR**: All 1,000 URLs processed quickly
- **Custom JS**:
  - All 1,000 URLs processed in 1-2 waves
  - **Total time**: ~2-3 minutes

## Recommendations

1. **For 10 clients × 100 URLs**: Current setup works ✅
2. **For 50+ clients × 100 URLs**: Add more custom JS services (50-100)
3. **For 100+ clients**: Consider horizontal scaling (multiple API instances)

## Monitoring

Watch for:
- Custom JS service queue times
- Memory usage (should stay reasonable)
- API response times
- Failed requests

