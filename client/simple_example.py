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
        "https://www.sih.gov.in/",
        "https://www.python.org",
        "https://github.com",
        "https://stackoverflow.com",
        "https://www.wikipedia.org",
        "https://www.reddit.com",
        "https://www.amazon.com",
        "https://www.microsoft.com",
        "https://www.apple.com",
        "https://www.google.com",
        "https://www.facebook.com",
        "https://www.twitter.com",
        "https://www.linkedin.com",
        "https://www.instagram.com",
        "https://www.youtube.com",
        "https://www.netflix.com",
        "https://www.spotify.com",
        "https://www.medium.com",
        "https://www.quora.com",
        "https://www.tumblr.com",
        "https://www.pinterest.com",
        "https://www.flickr.com",
        "https://www.imgur.com",
        "https://www.imgflip.com",
        "https://www.giphy.com",
        "https://www.dribbble.com",
        "https://www.behance.net",
        "https://www.deviantart.com",
        "https://www.artstation.com",
        "https://www.codecademy.com",
        "https://www.udemy.com",
        "https://www.coursera.org",
        "https://www.khanacademy.org",
        "https://www.edx.org",
        "https://www.freecodecamp.org",
        "https://www.w3schools.com",
        "https://www.mdn.com",
        "https://www.stackexchange.com",
        "https://www.dev.to",
        "https://www.hashnode.com",
        "https://www.producthunt.com",
        "https://www.hackernews.com",
        "https://www.indiehackers.com",
        "https://www.startupgrind.com",
        "https://www.techcrunch.com",
        "https://www.theverge.com",
        "https://www.engadget.com",
        "https://www.wired.com",
        "https://www.ars-technica.com",
        "https://www.gizmodo.com",
        "https://www.cnet.com",
        "https://www.pcmag.com",
        "https://www.tomshardware.com",
        "https://www.anandtech.com",
        "https://www.gamespot.com",
        "https://www.ign.com",
        "https://www.polygon.com",
        "https://www.kotaku.com",
        "https://www.rockpapershotgun.com",
        "https://www.eurogamer.net",
        "https://www.giantbomb.com",
        "https://www.twitch.tv",
        "https://www.mixer.com",
        "https://www.discord.com",
        "https://www.slack.com",
        "https://www.zoom.us",
        "https://www.skype.com",
        "https://www.whatsapp.com",
        "https://www.telegram.org",
        "https://www.signal.org",
        "https://www.protonmail.com",
        "https://www.tutanota.com",
        "https://www.1password.com",
        "https://www.lastpass.com",
        "https://www.dashlane.com",
        "https://www.bitwarden.com",
        "https://www.notion.so",
        "https://www.evernote.com",
        "https://www.onenote.com",
        "https://www.todoist.com",
        "https://www.asana.com",
        "https://www.trello.com",
        "https://www.monday.com",
        "https://www.clickup.com",
        "https://www.basecamp.com",
        "https://www.jira.com",
        "https://www.confluence.com",
        "https://www.gitlab.com",
        "https://www.bitbucket.org",
        "https://www.sourceforge.net",
        "https://www.codepen.io",
        "https://www.jsfiddle.net",
        "https://www.repl.it",
        "https://www.glitch.com",
        "https://www.codesandbox.io",
        "https://www.stackblitz.com",
        "https://www.heroku.com",
        "https://www.netlify.com",
        "https://www.vercel.com",
        "https://www.cloudflare.com",
        "https://www.digitalocean.com",
        "https://www.linode.com",
        "https://www.vultr.com"
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

