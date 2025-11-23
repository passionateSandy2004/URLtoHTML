# API Capacity FAQ

## Q: How many URLs can the API handle at a time?

**A**: The API can handle **unlimited concurrent requests**, but total throughput depends on:

1. **Custom JS Services** (main bottleneck):
   - Current: 13 services = **260 URLs simultaneously**
   - With 50 services: **1,000 URLs simultaneously**
   - With 100 services: **2,000 URLs simultaneously**

2. **Per-Request Limits**:
   - Static/XHR: 100 concurrent per request (configurable to 500)
   - Decodo: 3 concurrent per request

## Q: What happens when 10 clients each request 100 URLs?

**A**: Here's what happens:

### Request Flow

```
10 Clients → API Server
├─ Client 1: 100 URLs
├─ Client 2: 100 URLs
├─ Client 3: 100 URLs
...
└─ Client 10: 100 URLs

Total: 1,000 URLs
```

### Processing

1. **All 10 requests start simultaneously** (FastAPI async handles this)
2. **Static/XHR Phase**:
   - Each request: 100 concurrent
   - Total: 1,000 parallel static/XHR fetches
   - ✅ **No bottleneck** - processes quickly
3. **Custom JS Phase**:
   - Shared pool: 13 services
   - Capacity: 260 URLs at a time
   - First 260 URLs processed immediately
   - Remaining 740 URLs **queue and wait**
   - Processed in waves (260 at a time, 2-min cooldown)
   - ⏱️ **Total time**: ~6-8 minutes
4. **Decodo Fallback**:
   - Each request: 3 concurrent
   - Total: 30 concurrent Decodo requests
   - ✅ **No bottleneck**

### Result

✅ **Yes, it handles it!** But custom JS phase creates a queue.

**With 13 services**: ~6-8 minutes total
**With 50 services**: ~4-5 minutes total
**With 100 services**: ~2-3 minutes total

## Q: What's the maximum capacity?

**A**: Depends on your setup:

| Custom JS Services | Simultaneous Capacity | Example Load |
|-------------------|----------------------|--------------|
| 13 (current) | 260 URLs | 10 clients × 100 URLs ✅ |
| 50 | 1,000 URLs | 50 clients × 100 URLs ✅ |
| 100 | 2,000 URLs | 100 clients × 100 URLs ✅ |
| 200 | 4,000 URLs | 200 clients × 100 URLs ✅ |

## Q: Will requests block each other?

**A**: **No!** Each request is processed independently:

- ✅ Requests don't block each other
- ✅ Each request has its own async processing
- ✅ Static/XHR phase is independent per request
- ⚠️ Custom JS services are **shared** (but requests queue, don't block)

## Q: What are the bottlenecks?

**A**: Main bottlenecks:

1. **Custom JS Services** (shared resource)
   - **Solution**: Add more services
   
2. **Memory** (per request)
   - 100 URLs ≈ 10MB
   - 1,000 URLs ≈ 100MB
   - **Solution**: Monitor and limit request size
   
3. **Network Connections**
   - Per request: 100 concurrent
   - 10 requests: 1,000 concurrent
   - **Solution**: Usually fine (OS handles 65K+)

4. **API Workers** (CPU)
   - Default: 1 worker
   - **Solution**: Increase `API_WORKERS` to match CPU cores

## Q: How to scale for 100+ concurrent clients?

**A**: Recommended setup:

1. **Add Custom JS Services**: 100-200 services
2. **Increase API Workers**: `API_WORKERS=4-8`
3. **Horizontal Scaling**: Deploy multiple API instances
4. **Load Balancer**: Distribute requests across instances

## Q: Real-world example?

**A**: Scenario: **50 clients, each requesting 200 URLs**

- **Total URLs**: 10,000
- **Static/XHR**: 50 requests × 100 concurrent = 5,000 parallel ✅
- **Custom JS**: 
  - With 13 services: Very long queue (~1-2 hours)
  - With 50 services: ~20-30 minutes
  - With 100 services: ~10-15 minutes

**Recommendation**: Use 50-100 custom JS services for this load.

## Summary

✅ **API handles multiple concurrent requests** (async architecture)
✅ **Each request processes independently**
✅ **Scales by adding more custom JS services**
⚠️ **Custom JS services are shared** (main scaling factor)

**Current capacity**: 10-20 clients × 100 URLs = ✅ Works well
**For 50+ clients**: Add more custom JS services (50-100 recommended)

