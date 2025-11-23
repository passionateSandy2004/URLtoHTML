# API Scaling and Concurrency Guide

## Current Architecture

The API is built with **FastAPI** which uses **async/await** for handling concurrent requests. Each request is processed independently and asynchronously.

## How Concurrent Requests Work

### Request Independence

Each API request is **completely independent**:
- Each request has its own async event loop
- Each request processes its URLs in parallel
- Requests don't block each other
- No shared state between requests

### Example Scenario

If **10 clients** each send **100 URLs** simultaneously:

```
Request 1: 100 URLs → Processes independently
Request 2: 100 URLs → Processes independently
Request 3: 100 URLs → Processes independently
...
Request 10: 100 URLs → Processes independently
```

**Total**: 1,000 URLs being processed concurrently across all requests.

## Current Capacity

### Per-Request Limits

Each request can process:
- **Static/XHR Phase**: 100 concurrent requests (configurable up to 500)
- **Custom JS Phase**: 13 services × 20 URLs = 260 URLs simultaneously
- **Decodo Phase**: 3 concurrent requests

### Total System Capacity

With **N concurrent API requests**, each processing **M URLs**:

**Static/XHR Phase**:
- Per request: 100 concurrent
- Total across all requests: **N × 100** concurrent static/XHR fetches

**Custom JS Phase**:
- Services are shared across requests
- Service pool manager distributes batches across available services
- With 13 services: **260 URLs** can be processed simultaneously (shared)
- If services are busy, requests queue and wait for available services

**Decodo Phase**:
- Per request: 3 concurrent
- Total: **N × 3** concurrent Decodo requests

## Bottlenecks and Limits

### 1. Custom JS Services (Shared Resource)

**Bottleneck**: Custom JS services are **shared** across all requests.

- **13 services** = 260 URLs simultaneously (shared)
- If 10 requests each need 100 URLs:
  - Total: 1,000 URLs need custom JS rendering
  - Capacity: 260 URLs at a time
  - **Queue**: Requests wait for available services

**Solution**: Add more custom JS services to increase capacity.

### 2. Memory

Each request holds all HTML content in memory until response:
- 100 URLs × average 100KB = ~10MB per request
- 10 concurrent requests = ~100MB
- 100 concurrent requests = ~1GB

**Limit**: Depends on server memory.

### 3. Network Connections

Each static/XHR fetch creates a network connection:
- Per request: 100 concurrent connections
- 10 requests: 1,000 concurrent connections
- 100 requests: 10,000 concurrent connections

**Limit**: OS and network stack limits (typically 65,000+ connections).

### 4. API Server Workers

Default: **1 worker** (single process)
- Can handle many concurrent requests (async)
- Limited by CPU cores

**Recommendation**: Use multiple workers for CPU-bound operations.

## Real-World Capacity Examples

### Scenario 1: 10 Clients, 100 URLs Each

- **Total URLs**: 1,000
- **Static/XHR**: 10 requests × 100 concurrent = 1,000 parallel fetches ✅
- **Custom JS**: Shared pool, processes 260 at a time
  - First wave: 260 URLs
  - Remaining: 740 URLs queue
  - **Time**: ~6-8 minutes (with 2-minute cooldowns)
- **Memory**: ~100MB
- **Status**: ✅ **Handles well**

### Scenario 2: 50 Clients, 200 URLs Each

- **Total URLs**: 10,000
- **Static/XHR**: 50 requests × 100 concurrent = 5,000 parallel fetches ✅
- **Custom JS**: 260 URLs at a time
  - **Queue**: Very long wait times
  - **Time**: ~1-2 hours
- **Memory**: ~2GB
- **Status**: ⚠️ **Needs more custom JS services**

### Scenario 3: 100 Clients, 100 URLs Each

- **Total URLs**: 10,000
- **Static/XHR**: 100 requests × 100 concurrent = 10,000 parallel fetches ✅
- **Custom JS**: 260 URLs at a time
  - **Queue**: Extremely long wait times
  - **Time**: ~2-3 hours
- **Memory**: ~2GB
- **Status**: ⚠️ **Needs more custom JS services and workers**

## Recommendations for Massive Scale

### 1. Add More Custom JS Services

**Current**: 13 services = 260 URLs simultaneously
**Recommended**: 
- **50 services** = 1,000 URLs simultaneously
- **100 services** = 2,000 URLs simultaneously
- **200 services** = 4,000 URLs simultaneously

### 2. Increase API Workers

```bash
# Set environment variable
export API_WORKERS=4  # Match CPU cores

# Or in docker-compose.yml
environment:
  - API_WORKERS=4
```

### 3. Increase Static/XHR Concurrency Per Request

For large batches, increase per-request concurrency:

```python
response = client.fetch_batch(
    urls,
    static_xhr_concurrency=200  # Instead of default 100
)
```

### 4. Use Request Queuing (Optional)

For very high load, implement request queuing:
- Redis queue
- Message broker (RabbitMQ, Kafka)
- Process requests in batches

### 5. Horizontal Scaling

Deploy multiple API instances:
- Load balancer (nginx, HAProxy)
- Multiple Railway/Render instances
- Kubernetes with auto-scaling

## Current Maximum Capacity

### With Default Configuration

- **Concurrent API Requests**: Unlimited (async handles many)
- **URLs per Request**: 10,000 (hard limit)
- **Total URLs (all requests)**: Limited by:
  1. **Custom JS services**: 260 URLs at a time (shared)
  2. **Memory**: ~100MB per 100 URLs
  3. **Network**: OS connection limits

### With 50 Custom JS Services

- **Custom JS capacity**: 1,000 URLs simultaneously
- **Can handle**: 10 clients × 100 URLs = 1,000 URLs efficiently
- **Can handle**: 50 clients × 100 URLs = 5,000 URLs (with queuing)

### With 100 Custom JS Services

- **Custom JS capacity**: 2,000 URLs simultaneously
- **Can handle**: 20 clients × 100 URLs = 2,000 URLs efficiently
- **Can handle**: 100 clients × 100 URLs = 10,000 URLs (with queuing)

## Monitoring Recommendations

1. **Track Custom JS Service Usage**
   - Monitor service pool availability
   - Alert when all services are busy

2. **Monitor Memory Usage**
   - Track per-request memory
   - Set memory limits

3. **Track Request Queue Times**
   - Monitor wait times for custom JS services
   - Alert on long queues

4. **Monitor API Response Times**
   - Track end-to-end processing time
   - Alert on slow requests

## Summary

**Current Capacity**:
- ✅ **Handles multiple concurrent requests** (async architecture)
- ✅ **Each request processes independently**
- ⚠️ **Custom JS services are shared** (main bottleneck)
- ✅ **Scales by adding more custom JS services**

**For 10 clients × 100 URLs = 1,000 URLs**:
- ✅ **Works well** with current 13 services
- ⏱️ Processing time: ~6-8 minutes

**For 50+ clients × 100 URLs = 5,000+ URLs**:
- ⚠️ **Needs more custom JS services** (50-100 services recommended)
- ⏱️ Processing time: Depends on service count

**Bottom Line**: The API can handle **unlimited concurrent requests**, but total throughput is limited by the number of custom JS services. Add more services to scale.

