"""
Simple example to use ONLY the custom JS rendering service.

This script directly calls the custom JS rendering service,
bypasses all fallbacks, and saves the HTML result.
"""

import requests
import json
import os
import re
from urllib.parse import urlparse

# Configuration
CUSTOM_JS_SERVICE_URL = "https://easygoing-strength-copy-2-copy-2-production.up.railway.app/render"

# Your URLs to process (62 URLs from CSV with {query} replaced by "Glasses")
urls = [
    "https://somethingsbrewing.in/search?options%5Bprefix%5D=last&q=stove",
    "https://shop.ttkprestige.com/catalogsearch/result/?q=stove",
    "https://www.croma.com/searchB?q=phone",
    "https://www.carysilshop.com/search?q=phone",
    "https://lovebeautyandplanet.in/pages/search?q=phone",
    "https://www.nykaa.com/?search-suggestions-nykaa=phone",
    "https://www.reliancedigital.in/collection/phone",
    "https://www.sangeethamobiles.com/search-result/phone",
    "https://www.wonderchef.com/search?q=stove",
    "https://www.domesticappliances.philips.co.in/pages/searchtap-search?q=stove",
    "https://agarolifestyle.com/pages/expertrec-search?q=stove",
    "https://wwxw.naaptol.com/search.html?type=srch_catlg&kw=stove",
    "https://rbzone.com/catalogsearch/result/?q=phone",
    "https://www.adidas.co.in/running-shoes",
]

# Function to save HTML to file
def save_html(url, html_content):
    """Save HTML content to a file in the examples folder."""
    # Create a safe filename from the URL
    parsed = urlparse(url)
    domain = parsed.netloc.replace('www.', '').replace('.', '_')
    path = parsed.path.strip('/').replace('/', '_')
    if not path:
        path = 'index'
    
    # Add query parameters if present
    if parsed.query:
        query_part = parsed.query[:30].replace('=', '_').replace('&', '_')
        query_part = re.sub(r'[^\w\-_]', '_', query_part)
        path = f"{path}_{query_part}"
    
    # Remove any special characters
    filename = re.sub(r'[^\w\-_]', '_', f"custom_js_{domain}_{path}")
    filename = f"{filename}.html"
    
    # Save to examples folder (same directory as this script)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(script_dir, filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"    💾 Saved to: {filename}")
        return filepath
    except Exception as e:
        print(f"    ❌ Failed to save: {e}")
        return None


# Main processing
print("=" * 60)
print("CUSTOM JS RENDERING SERVICE TEST")
print("=" * 60)
print(f"Service: {CUSTOM_JS_SERVICE_URL}")
print(f"Processing {len(urls)} URLs...\n")

# Prepare the request payload
payload = {
    "urls": urls
}

try:
    # Make the request to custom JS service
    print("Sending request to custom JS service...")
    response = requests.post(
        CUSTOM_JS_SERVICE_URL,
        json=payload,
        timeout=300  # 5 minutes timeout
    )
    
    print(f"Response status: {response.status_code}")
    
    # Save raw response to file for inspection
    script_dir = os.path.dirname(os.path.abspath(__file__))
    raw_response_file = os.path.join(script_dir, "raw_response.json")
    with open(raw_response_file, 'w', encoding='utf-8') as f:
        f.write(response.text)
    print(f"\nRaw response saved to: {raw_response_file}")
    print(f"Response length: {len(response.text):,} characters\n")
    
    # Check if request was successful
    if response.status_code == 200:
        # Try to parse as JSON first
        try:
            data = response.json()
        except:
            # If JSON parsing fails, treat entire response as HTML
            print("Response is not JSON, treating as direct HTML content")
            data = response.text
        
        # Process results
        print("=" * 60)
        print("RESULTS")
        print("=" * 60)
        
        successful = 0
        failed = 0
        
        # Handle different response formats
        results_list = None
        
        if isinstance(data, str):
            # Direct HTML response
            results_list = [{"url": urls[0], "html": data}]
            
        elif isinstance(data, list):
            # Direct list of results
            results_list = data
            
        elif isinstance(data, dict):
            # Check if it's a wrapper object with "results" key
            if "results" in data:
                results_list = data["results"]
            else:
                # Single result object
                results_list = [data]
        
        # Process all results
        if results_list:
            for result in results_list:
                if isinstance(result, dict):
                    url = result.get("url", urls[0] if len(urls) > 0 else "Unknown URL")
                    html = result.get("html", result.get("content", ""))
                    error = result.get("error")
                    status = result.get("status", "unknown")
                    
                    print(f"\nURL: {url}")
                    print(f"  Status: {status}")
                    
                    if html and not error:
                        html_size = len(html)
                        print(f"  SUCCESS")
                        print(f"  Size: {html_size:,} bytes")
                        save_html(url, html)
                        successful += 1
                    else:
                        print(f"  FAILED")
                        print(f"  Error: {error or 'No HTML returned'}")
                        failed += 1
                        
                elif isinstance(result, str):
                    # Direct HTML string
                    print(f"\nURL: {urls[0] if len(urls) > 0 else 'Unknown'}")
                    html_size = len(result)
                    print(f"  SUCCESS (direct string)")
                    print(f"  Size: {html_size:,} bytes")
                    save_html(urls[0] if len(urls) > 0 else "unknown", result)
                    successful += 1
        
        # Summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"Total URLs: {len(urls)}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        
        if successful > 0:
            print(f"\n SUCCESS {successful} HTML file(s) saved in the examples folder!")
        
    else:
        print(f"❌ Error: Service returned status {response.status_code}")
        print(f"Response: {response.text[:500]}")

except requests.exceptions.Timeout:
    print("❌ Error: Request timed out after 5 minutes")
except requests.exceptions.ConnectionError:
    print("❌ Error: Could not connect to the service")
    print("   Make sure the service URL is correct and accessible")
except Exception as e:
    print(f"❌ Error: {type(e).__name__}: {e}")

print("\n" + "=" * 60)
print("DONE")
print("=" * 60)