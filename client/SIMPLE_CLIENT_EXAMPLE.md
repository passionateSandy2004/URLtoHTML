# Simple Client Example

This is a simple, standalone example to use the URL to HTML Converter API.

## Quick Start

### Option 1: Simple Example (3 URLs)

```python
import requests

API_URL = "https://urltohtml-production.up.railway.app/api/v1/fetch-batch"

urls = [
    "https://example.com/page1",
    "https://example.com/page2",
    "https://example.com/page3"
]

response = requests.post(
    API_URL,
    json={"urls": urls},
    timeout=3600
)

if response.status_code == 200:
    data = response.json()
    print(f"Success: {data['summary']['success']}/{data['summary']['total']}")
    
    # Access HTML content
    for result in data["results"]:
        if result["status"] == "success":
            html = result["html"]
            print(f"{result['url']}: {len(html)} bytes")
```

### Option 2: From CSV File

```python
import requests
import csv

API_URL = "https://urltohtml-production.up.railway.app/api/v1/fetch-batch"

# Read URLs from CSV
urls = []
with open('your_file.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        url = row.get('product_page_url', '').strip()
        if url:
            urls.append(url)

# Limit to 100 URLs
urls = urls[:100]

# Send to API
response = requests.post(
    API_URL,
    json={"urls": urls},
    timeout=3600
)

data = response.json()
print(f"Processed: {data['summary']['success']}/{data['summary']['total']}")
```

## Requirements

Just install `requests`:

```bash
pip install requests
```

## API Endpoint

```
POST https://urltohtml-production.up.railway.app/api/v1/fetch-batch
```

## Request Format

```json
{
  "urls": [
    "https://example.com/page1",
    "https://example.com/page2"
  ]
}
```

## Response Format

```json
{
  "results": [
    {
      "url": "https://example.com/page1",
      "html": "<html>...</html>",
      "status": "success",
      "method": "static",
      "error": null
    }
  ],
  "summary": {
    "total": 2,
    "success": 1,
    "failed": 1,
    "total_time": 5.23,
    "by_method": {
      "static": 1,
      "custom_js": 1
    }
  }
}
```

## Full Example Files

- `simple_example.py` - Basic example with 3 URLs
- `simple_example_with_csv.py` - Example reading from CSV file

Just copy and modify as needed!

