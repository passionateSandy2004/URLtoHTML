"""
Simple example client for URL to HTML Converter API.

This is a standalone example - just copy and use it!
No library imports needed, just 'requests'.
"""

import requests
import json

# Configuration
API_URL = "https://urltohtml-production.up.railway.app/api/v1/fetch-batch"

# Your URLs to process
urls = [
        "https://www.amazon.in/s?k=hoodies"
]

# Make the request
print(f"Sending {len(urls)} URLs to API...")
print(f"API: {API_URL}")
print()

response = requests.post(
    API_URL,
    json={"urls": urls},
    timeout=3600  # 1 hour timeout
)

# Check if request was successful
if response.status_code == 200:
    data = response.json()
    
    # Print summary
    summary = data["summary"]
    print("=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"Total URLs: {summary['total']}")
    print(f"Successful: {summary['success']}")
    print(f"Failed: {summary['failed']}")
    print(f"Success Rate: {summary.get('success_rate', 0):.2f}%")
    print(f"Total Time: {summary['total_time']:.2f} seconds")
    print()
    
    # Print results by method
    print("Results by Method:")
    for method, count in summary.get('by_method', {}).items():
        print(f"  {method}: {count}")
    print()
    
    # Show successful URLs
    successful = [r for r in data["results"] if r["status"] == "success"]
    if successful:
        print(f"Successful URLs ({len(successful)}):")
        for result in successful:
            html_size = len(result.get("html", ""))
            print(f"  ✓ {result['url']}")
            print(f"    Method: {result['method']}, Size: {html_size:,} bytes")
            print()
    
    # Show failed URLs
    failed = [r for r in data["results"] if r["status"] == "failed"]
    if failed:
        print(f"Failed URLs ({len(failed)}):")
        for result in failed:
            print(f"  ✗ {result['url']}")
            print(f"    Error: {result.get('error', 'Unknown error')}")
            print()
    
    # Access HTML content
    print("=" * 60)
    print("HOW TO ACCESS HTML CONTENT")
    print("=" * 60)
    print()
    print("For each successful result:")
    print("  result['html']  # Contains the HTML content")
    print()
    print("Example:")
    if successful:
        first_result = successful[0]
        print(f"  URL: {first_result['url']}")
        print(f"  HTML length: {len(first_result.get('html', ''))} characters")
        print(f"  First 100 chars: {first_result.get('html', '')[:100]}...")
    
else:
    print(f"Error: API returned status {response.status_code}")
    print(f"Response: {response.text}")

