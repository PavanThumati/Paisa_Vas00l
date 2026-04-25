import feedparser
import requests
import cloudscraper
import asyncio
import os
import re
from telegram import Bot
from datetime import datetime

# -----------------------------
# ENV VARIABLES
# -----------------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID", "-100xxxxxxxxxx")
CUELINKS_API_TOKEN = os.getenv("CUELINKS_API_TOKEN", "your_api_token_here")

if not BOT_TOKEN:
    print("❌ BOT_TOKEN missing")
    exit()

bot = Bot(token=BOT_TOKEN)
POSTED_FILE = "posted_deals.txt"

# -----------------------------
# STATE MANAGEMENT
# -----------------------------
def get_posted_deals():
    if os.path.exists(POSTED_FILE):
        with open(POSTED_FILE, "r") as f:
            return set(f.read().splitlines())
    return set()

def save_posted_deal(deal_id):
    with open(POSTED_FILE, "a") as f:
        f.write(f"{deal_id}\n")

# -----------------------------
# LINK PROCESSING
# -----------------------------
def get_clean_destination_url(short_url):
    """Follows deep links and internal redirects to get the raw e-commerce URL."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "en-US,en;q=0.9"
        }
        response = requests.head(short_url, allow_redirects=True, headers=headers, timeout=10)
        return response.url.split('?')[0] 
    except:
        return short_url

def generate_cuelinks_api_url(raw_url):
    """Generates the monetized shortlink via Cuelinks API."""
    api_endpoint = "https://www.cuelinks.com/api/v2/get_link"
    
    headers = {
        "token": CUELINKS_API_TOKEN
    }
    params = {
        "url": raw_url
    }
    
    try:
        response = requests.get(api_endpoint, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return data.get('short_url') or data.get('affiliate_url', raw_url)
        else:
            print(f"⚠️ API Error: {response.text}")
            return raw_url
            
    except Exception as e:
        print(f"⚠️ API Request Failed: {e}")
        return raw_url

# -----------------------------
# RSS INTERCEPTOR (MULTI-SOURCE)
# -----------------------------
async def hunt_and_post():
    # Utilizing much more stable WordPress-based deal feeds
    rss_sources = [
        "https://indiafreestuff.in/feed/",
        "https://www.savemoneyindia.com/feed/"
    ]
    
    posted_deals = get_posted_deals()
    
    scraper = cloudscraper.create_scraper(
        browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
    )
    
    supported_stores = [
        'amazon.in', 'flipkart.com', 'myntra.com', 'ajio.com', 
        'tatacliq.com', 'croma.com', 'reliancedigital.in', 'nykaa.com'
    ]

    new_finds = 0

    for rss_url in rss_sources:
        try:
            response = scraper.get(rss_url, timeout=20)
            feed = feedparser.parse(response.content)
            
            if not feed.entries:
                continue
                
        except Exception as e:
            print(f"⚠️ Feed fetch failed for {rss_url}: {e}")
            continue

        for entry in feed.entries:
            deal_id = entry.id if hasattr(entry, 'id') else entry.link
            
            if deal_id in posted_deals:
                continue
                
            # Combine summary and content to hunt for links
            content_block = entry.description
            if hasattr(entry, 'content'):
                content_block += str(entry.content[0].value)
            
            # Use Regex to extract all href URLs from the post content
            extracted_urls = re.findall(r'href=[\'"]?([^\'" >]+)', content_block)
            
            target_url = None
            for url in extracted_urls:
                # Skip obvious image files to save processing time
                if any(ext in url.lower() for ext in ['.jpg', '.png', '.gif', '.jpeg']):
                    continue
                    
                clean = get_clean_destination_url(url)
                if any(store in clean.lower() for store in supported_stores):
                    target_url = clean
                    break # Stop looking once we find a valid store link
            
            if target_url:
                new_finds += 1
                print(f"🎯 NEW MATCH Found! Generating API link...")
                
                api_short_link = generate_cuelinks_api_url(target_url)

                # Strict generic formatting without brand identifiers
                msg = f"🔥 <b>Trending Loot Alert!</b>\n\n"
                msg += f"📦 Limited Time Deal Unlocked\n\n"
                msg += f"🛒 <b>Grab it here:</b> {api_short_link}"

                try:
                    await bot.send_message(
                        chat_id=CHANNEL_ID,
                        text=msg,
                        parse_mode="HTML",
                        disable_web_page_preview=False
                    )
                    print(f"✅ Posted successfully!")
                    save_posted_deal(deal_id)
                    await asyncio.sleep(4) # Anti-spam pause
                except Exception as e:
                    print(f"❌ Telegram Error: {e}")
            else:
                # If we couldn't find a supported store link, save it so we don't scan it again
                save_posted_deal(deal_id)

    if new_finds > 0:
        print(f"📊 Scan Complete | New Deals Posted: {new_finds}")

# -----------------------------
# MAIN LOOP
# -----------------------------
async def run_bot():
    while True:
        print(f"\n⚡ [{datetime.now().strftime('%H:%M:%S')}] Fetching latest deals...")
        await hunt_and_post()
        print("⏳ Waiting 60 seconds...\n")
        await asyncio.sleep(60) 

if __name__ == "__main__":
    print("🚀 Multi-Source Auto-Deal Bot Started!")
    asyncio.run(run_bot())
    
