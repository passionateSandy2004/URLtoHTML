"""
Example demonstrating multiple concurrent clients using the production API.

This shows how the API handles multiple clients each requesting hundreds of URLs.
"""

import sys
import os
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

# Add parent directory to path to import client
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client import URLToHTMLClient

def process_client(client_id, urls, base_url):
    """Process a batch of URLs for a single client."""
    client = URLToHTMLClient(
        base_url=base_url,
        timeout=3600
    )
    
    try:
        start_time = time.time()
        print(f"[Client {client_id}] Starting {len(urls)} URLs...")
        
        response = client.fetch_batch(urls)
        
        elapsed = time.time() - start_time
        
        print(f"[Client {client_id}] ✓ Completed in {elapsed:.2f}s")
        print(f"           Success: {response.summary.success}/{response.summary.total}")
        print(f"           Methods: {response.summary.by_method}")
        
        return {
            "client_id": client_id,
            "total": response.summary.total,
            "success": response.summary.success,
            "failed": response.summary.failed,
            "time": elapsed,
            "by_method": response.summary.by_method
        }
    except Exception as e:
        print(f"[Client {client_id}] ✗ Error: {e}")
        return {
            "client_id": client_id,
            "error": str(e)
        }
    finally:
        client.close()

def main():
    # Configuration
    BASE_URL = "https://urltohtml-production.up.railway.app"
    NUM_CLIENTS = 10
    URLS_PER_CLIENT = 100
    
    print("=" * 70)
    print("CONCURRENT CLIENTS TEST")
    print("=" * 70)
    print(f"API: {BASE_URL}")
    print(f"Number of Clients: {NUM_CLIENTS}")
    print(f"URLs per Client: {URLS_PER_CLIENT}")
    print(f"Total URLs: {NUM_CLIENTS * URLS_PER_CLIENT}")
    print()
    
    # Generate URLs for each client
    all_urls = [
        f"https://example.com/page{i}" 
        for i in range(NUM_CLIENTS * URLS_PER_CLIENT)
    ]
    
    # Split into batches for each client
    client_batches = [
        all_urls[i:i + URLS_PER_CLIENT]
        for i in range(0, len(all_urls), URLS_PER_CLIENT)
    ]
    
    print("Starting all clients simultaneously...")
    print("-" * 70)
    print()
    
    start_time = time.time()
    
    # Process all clients concurrently using ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=NUM_CLIENTS) as executor:
        futures = [
            executor.submit(process_client, i + 1, batch, BASE_URL)
            for i, batch in enumerate(client_batches)
        ]
        
        # Wait for all to complete
        results = [future.result() for future in futures]
    
    total_time = time.time() - start_time
    
    # Summary
    print()
    print("=" * 70)
    print("SUMMARY - ALL CLIENTS")
    print("=" * 70)
    
    successful_clients = [r for r in results if "error" not in r]
    failed_clients = [r for r in results if "error" in r]
    
    if successful_clients:
        total_urls = sum(r["total"] for r in successful_clients)
        total_success = sum(r["success"] for r in successful_clients)
        total_failed = sum(r["failed"] for r in successful_clients)
        
        # Aggregate methods
        all_methods = {}
        for r in successful_clients:
            for method, count in r.get("by_method", {}).items():
                all_methods[method] = all_methods.get(method, 0) + count
        
        print(f"Successful Clients: {len(successful_clients)}/{NUM_CLIENTS}")
        print(f"Failed Clients: {len(failed_clients)}")
        print()
        print(f"Total URLs Processed: {total_urls}")
        print(f"Total Successful: {total_success}")
        print(f"Total Failed: {total_failed}")
        print(f"Overall Success Rate: {(total_success/total_urls*100):.2f}%")
        print()
        print("Results by Method (across all clients):")
        for method, count in sorted(all_methods.items()):
            percentage = (count / total_urls) * 100 if total_urls > 0 else 0
            print(f"  {method:15s}: {count:5d} ({percentage:5.2f}%)")
        print()
        print(f"Total Time (all clients): {total_time:.2f} seconds")
        print(f"Average Time per Client: {total_time / NUM_CLIENTS:.2f} seconds")
        print(f"URLs per Second (overall): {total_urls / total_time:.2f}")
    
    if failed_clients:
        print()
        print("Failed Clients:")
        for r in failed_clients:
            print(f"  Client {r['client_id']}: {r['error']}")
    
    print()
    print("=" * 70)
    print("CAPACITY ANALYSIS")
    print("=" * 70)
    print()
    print("Current Setup:")
    print(f"  - Custom JS Services: 13")
    print(f"  - Custom JS Capacity: 260 URLs simultaneously")
    print(f"  - Static/XHR Concurrency: 100 per request")
    print()
    print(f"With {NUM_CLIENTS} clients × {URLS_PER_CLIENT} URLs:")
    print(f"  - Total URLs: {NUM_CLIENTS * URLS_PER_CLIENT}")
    print(f"  - Static/XHR: {NUM_CLIENTS * 100} concurrent (per request)")
    print(f"  - Custom JS: Shared pool, 260 at a time")
    print(f"  - Estimated Time: ~6-8 minutes (with 13 services)")
    print()
    print("To Scale Further:")
    print("  - Add more custom JS services (50-100 for better throughput)")
    print("  - Increase API_WORKERS for CPU-bound operations")
    print("  - Deploy multiple API instances for horizontal scaling")

if __name__ == "__main__":
    main()

