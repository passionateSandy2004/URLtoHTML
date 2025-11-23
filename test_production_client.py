"""
Quick test script for the production API client.

Run this to test the client with the deployed API.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from client import URLToHTMLClient

def main():
    print("Testing Production API Client")
    print("=" * 60)
    print()
    
    # Initialize client with production API
    client = URLToHTMLClient(
        base_url="https://urltohtml-production.up.railway.app",
        timeout=3600
    )
    
    try:
        # Quick health check
        print("1. Health Check...")
        health = client.health_check()
        print(f"   ✓ API is {health['status']}")
        print()
        
        # Test with 100 URLs
        print("2. Fetching 100 URLs...")
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
        
        print(f"   Processing {len(urls)} URLs...")
        print("   (This may take a few minutes)")
        print()
        
        response = client.fetch_batch(urls)
        
        # Display summary
        print("3. Results Summary:")
        print("-" * 60)
        print(f"   Total URLs: {response.summary.total}")
        print(f"   Successful: {response.summary.success}")
        print(f"   Failed: {response.summary.failed}")
        print(f"   Success Rate: {response.summary.success_rate:.2f}%")
        print(f"   Processing Time: {response.summary.total_time:.2f} seconds")
        print()
        print("   Results by Method:")
        for method, count in sorted(response.summary.by_method.items()):
            percentage = (count / response.summary.total) * 100 if response.summary.total > 0 else 0
            print(f"     {method:15s}: {count:4d} ({percentage:5.2f}%)")
        print()
        
        # Show sample results
        successful = response.get_successful()
        failed = response.get_failed()
        
        if successful:
            print(f"   Sample Successful URLs (first 5 of {len(successful)}):")
            for result in successful[:5]:
                print(f"     ✓ {result.url} - {result.method} - {len(result.html):,} bytes")
            print()
        
        if failed:
            print(f"   Failed URLs ({len(failed)}):")
            for result in failed[:5]:
                print(f"     ✗ {result.url} - {result.error}")
            if len(failed) > 5:
                print(f"     ... and {len(failed) - 5} more")
            print()
        
        print("=" * 60)
        print("✓ Test completed successfully!")
        print(f"✓ Processed {response.summary.total} URLs in {response.summary.total_time:.2f}s")
        print(f"✓ Success rate: {response.summary.success_rate:.2f}%")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()

