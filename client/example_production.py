"""
Example using the deployed production API.

This example demonstrates using the client with the production API
deployed at urltohtml-production.up.railway.app
"""

import sys
import os

# Add parent directory to path to import client
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client import URLToHTMLClient
import json

def main():
    # Initialize client with production API URL
    client = URLToHTMLClient(
        base_url="https://urltohtml-production.up.railway.app",
        timeout=3600,  # 1 hour timeout for large batches
        verify_ssl=True
    )
    
    print("=" * 70)
    print("URL to HTML Converter API - Production Example")
    print("=" * 70)
    print()
    
    try:
        # 1. Check API health
        print("1. Checking API health...")
        health = client.health_check()
        print(f"   Status: {health['status']}")
        print(f"   Version: {health['version']}")
        print(f"   Uptime: {health.get('uptime', 0):.2f} seconds")
        print()
        
        # 2. Get API info
        print("2. Getting API information...")
        info = client.get_api_info()
        print(f"   API Name: {info['name']}")
        print(f"   API Version: {info['version']}")
        print(f"   Available Endpoints:")
        for endpoint, path in info['endpoints'].items():
            print(f"     - {endpoint}: {path}")
        print()
        
        # 3. Fetch a batch of URLs
        print("3. Fetching HTML for 100 URLs...")
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
        
        print(f"   URLs to fetch: {len(urls)}")
        print(f"   (Showing first 5 URLs)")
        for url in urls[:5]:
            print(f"     - {url}")
        print(f"     ... and {len(urls) - 5} more URLs")
        print()
        
        response = client.fetch_batch(urls)
        
        # 4. Display results
        print("4. Results:")
        print("-" * 70)
        print(f"   Total URLs: {response.summary.total}")
        print(f"   Successful: {response.summary.success}")
        print(f"   Failed: {response.summary.failed}")
        print(f"   Success Rate: {response.summary.success_rate:.2f}%")
        print(f"   Processing Time: {response.summary.total_time:.2f} seconds")
        print()
        print(f"   Results by Method:")
        for method, count in sorted(response.summary.by_method.items()):
            percentage = (count / response.summary.total) * 100 if response.summary.total > 0 else 0
            print(f"     {method:15s}: {count:3d} ({percentage:5.2f}%)")
        print()
        
        # 5. Show sample results (first 10 successful and first 5 failed)
        print("5. Sample Results:")
        print("-" * 70)
        
        successful = response.get_successful()
        failed = response.get_failed()
        
        if successful:
            print(f"   Successful URLs (showing first 10 of {len(successful)}):")
            for i, result in enumerate(successful[:10], 1):
                print(f"     [{i}] ✓ {result.url}")
                print(f"         Method: {result.method}, Size: {len(result.html):,} bytes")
            if len(successful) > 10:
                print(f"     ... and {len(successful) - 10} more successful URLs")
            print()
        
        if failed:
            print(f"   Failed URLs (showing first 5 of {len(failed)}):")
            for i, result in enumerate(failed[:5], 1):
                print(f"     [{i}] ✗ {result.url}")
                print(f"         Error: {result.error}")
            if len(failed) > 5:
                print(f"     ... and {len(failed) - 5} more failed URLs")
            print()
        
        # 6. Summary
        print("=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"✓ Successfully fetched {response.summary.success} out of {response.summary.total} URLs")
        print(f"✓ Processing completed in {response.summary.total_time:.2f} seconds")
        
        if response.summary.success > 0:
            avg_time = response.summary.total_time / response.summary.total
            print(f"✓ Average time per URL: {avg_time:.2f} seconds")
        
        print()
        print("API is working correctly! 🎉")
        
    except Exception as e:
        print(f"\n❌ Error occurred: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        client.close()

if __name__ == "__main__":
    main()

