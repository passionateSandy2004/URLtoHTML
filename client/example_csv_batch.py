"""
Example: Fetch 100 URLs from CSV file using the production API.

This script reads URLs from product_page_urls_rows.csv and processes
the first 100 URLs through the API in a single batch request.
"""

import sys
import os
import csv
import time

# Add parent directory to path to import client
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client import URLToHTMLClient

def read_urls_from_csv(csv_path):
    """Read URLs from CSV file."""
    urls = []
    
    print(f"Reading URLs from {csv_path}...")
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            url = row.get('product_page_url', '').strip()
            if url and url.startswith('http'):
                urls.append(url)
    
    print(f"Found {len(urls)} URLs")
    return urls

def main():
    # Configuration
    BASE_URL = "https://urltohtml-production.up.railway.app"
    CSV_FILE = os.path.join(os.path.dirname(__file__), "product_page_urls_rows.csv")
    
    print("=" * 70)
    print("BATCH PROCESSING FROM CSV")
    print("=" * 70)
    print(f"CSV File: {CSV_FILE}")
    print(f"API: {BASE_URL}")
    print()
    
    # Read URLs from CSV
    if not os.path.exists(CSV_FILE):
        print(f"Error: CSV file not found at {CSV_FILE}")
        return
    
    all_urls = read_urls_from_csv(CSV_FILE)
    
    if not all_urls:
        print("Error: No URLs found in CSV file")
        return
    
    # Limit to 100 URLs
    urls = all_urls[:100]
    
    print(f"Total URLs in CSV: {len(all_urls)}")
    print(f"Processing first {len(urls)} URLs (limited to 100)")
    print()
    print("Starting batch request...")
    print("-" * 70)
    print()
    
    # Initialize client
    client = URLToHTMLClient(
        base_url=BASE_URL,
        timeout=3600,  # 1 hour timeout for 100 URLs
        verify_ssl=True
    )
    
    try:
        start_time = time.time()
        
        # Process URLs in a single batch
        print(f"Sending request for {len(urls)} URLs...")
        print("(This may take several minutes depending on custom JS service capacity)")
        print()
        
        response = client.fetch_batch(
            urls,
            static_xhr_concurrency=200,  # Higher concurrency for large batch
        )
        
        elapsed_time = time.time() - start_time
        
        # Display results
        print()
        print("=" * 70)
        print("RESULTS")
        print("=" * 70)
        print()
        print(f"Total URLs: {response.summary.total}")
        print(f"Successful: {response.summary.success}")
        print(f"Failed: {response.summary.failed}")
        print(f"Success Rate: {response.summary.success_rate:.2f}%")
        print(f"Total Time: {elapsed_time:.2f} seconds ({elapsed_time/60:.2f} minutes)")
        print()
        
        # Results by method
        print("Results by Method:")
        for method, count in sorted(response.summary.by_method.items()):
            percentage = (count / response.summary.total) * 100 if response.summary.total > 0 else 0
            print(f"  {method:15s}: {count:5d} ({percentage:5.2f}%)")
        print()
        
        # Show some successful examples
        successful = response.get_successful()
        if successful:
            print(f"Successful URLs (showing first 10):")
            for i, result in enumerate(successful[:10], 1):
                html_size = len(result.html) if result.html else 0
                print(f"  {i:2d}. {result.url[:60]:60s} [{result.method:12s}] {html_size:>8,} bytes")
            if len(successful) > 10:
                print(f"  ... and {len(successful) - 10} more successful URLs")
            print()
        
        # Show failed examples
        failed = response.get_failed()
        if failed:
            print(f"Failed URLs (showing first 10):")
            for i, result in enumerate(failed[:10], 1):
                error = result.error[:60] if result.error else "Unknown error"
                print(f"  {i:2d}. {result.url[:50]:50s} - {error}")
            if len(failed) > 10:
                print(f"  ... and {len(failed) - 10} more failed URLs")
            print()
        
        # Performance metrics
        print("=" * 70)
        print("PERFORMANCE METRICS")
        print("=" * 70)
        print(f"URLs per Second: {response.summary.total / elapsed_time:.2f}")
        print(f"Average Time per URL: {elapsed_time / response.summary.total:.2f}s")
        print()
        
        # Capacity analysis
        print("=" * 70)
        print("CAPACITY ANALYSIS")
        print("=" * 70)
        print()
        print(f"With {len(urls)} URLs:")
        print(f"  - Static/XHR Phase: Processed {response.summary.by_method.get('static', 0) + response.summary.by_method.get('xhr', 0)} URLs")
        print(f"  - Custom JS Phase: Processed {response.summary.by_method.get('custom_js', 0)} URLs")
        print(f"  - Decodo Phase: Processed {response.summary.by_method.get('decodo', 0)} URLs")
        print()
        print("Current Setup:")
        print("  - Custom JS Services: 13")
        print("  - Custom JS Capacity: 260 URLs simultaneously")
        print(f"  - Estimated Custom JS Time: ~2-3 minutes for {len(urls)} URLs")
        print()
        print("To Scale Further:")
        print("  - Add more custom JS services (50-100 for better throughput)")
        print("  - Increase static_xhr_concurrency for faster initial phase")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()
        print()
        print("=" * 70)
        print("COMPLETED")
        print("=" * 70)

if __name__ == "__main__":
    main()

