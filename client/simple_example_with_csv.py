"""
Simple example: Process URLs from CSV file.

This example reads URLs from a CSV and sends them to the API.
Just update the CSV_FILE path and run!
"""

import requests
import csv
import os

# Configuration
API_URL = "https://urltohtml-production.up.railway.app/api/v1/fetch-batch"
CSV_FILE = "product_page_urls_rows.csv"  # Update this path

# Read URLs from CSV
urls = []
if os.path.exists(CSV_FILE):
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            url = row.get('product_page_url', '').strip()
            if url and url.startswith('http'):
                urls.append(url)
    
    # Limit to 100 URLs (optional)
    urls = urls[:100]
    
    print(f"Read {len(urls)} URLs from {CSV_FILE}")
else:
    print(f"CSV file not found: {CSV_FILE}")
    print("Using example URLs instead...")
    urls = [
        "https://example.com/page1",
        "https://example.com/page2",
        "https://example.com/page3"
    ]

# Make the request
print(f"\nSending {len(urls)} URLs to API...")
print(f"API: {API_URL}\n")

response = requests.post(
    API_URL,
    json={"urls": urls},
    timeout=3600  # 1 hour timeout
)

# Process response
if response.status_code == 200:
    data = response.json()
    summary = data["summary"]
    
    print("=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"Total: {summary['total']}")
    print(f"Successful: {summary['success']}")
    print(f"Failed: {summary['failed']}")
    print(f"Time: {summary['total_time']:.2f}s")
    print()
    
    # Save successful results to files (optional)
    successful = [r for r in data["results"] if r["status"] == "success"]
    if successful:
        os.makedirs("outputs", exist_ok=True)
        for i, result in enumerate(successful, 1):
            filename = f"outputs/result_{i}.html"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(result.get("html", ""))
        print(f"Saved {len(successful)} HTML files to 'outputs/' directory")
    
else:
    print(f"Error: {response.status_code}")
    print(response.text)

