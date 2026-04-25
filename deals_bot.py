import feedparser
import requests
import asyncio
import os
from telegram import Bot
from datetime import datetime

# -----------------------------
# ENV VARIABLES
# -----------------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID", "-100xxxxxxxxxx")
# Replace with your actual Cuelinks API Token from the Resource Centre
CUELINKS_API_TOKEN = os.getenv("CUELINKS_API_TOKEN", "your_api_token_here")

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
    try:
        # Stealth headers to bypass deep-link tracking blocks
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "en-US,en;q=0.9"
        }
        response = requests.head(short_url, allow_redirects=True, headers=headers, timeout=15)
        return response.url.split('?')[0] 
    except:
        return short_url

def generate_cuelinks_api_url(raw_url):
    """Uses the official Cuelinks API to get a shortened, monetized link."""
    api_endpoint = "https://www.cuelinks.com/api/v2/get_link"
    
    # Cuelinks requires the token in the header, not as a parameter
    headers = {
        "token": CUELINKS_API_TOKEN
    }
    params = {
        "url": raw_url
    }
    
    try:
        response = requests.get(api_endpoint, headers=headers, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            # The API typically returns both 'affiliate_url' and 'short_url'. 
            # We grab the short one for a cleaner Telegram post.
            return data.get('short_url') or data.get('affiliate_url', raw_url)
        else:
            print(f"⚠️ API Error (Status {response.status_code}): {response.text}")
            return raw_url
            
    except Exception as e:
        print(f"⚠️ API Request Failed: {e}")
        return raw_url

# -----------------------------
# RSS INTERCEPTOR (STEALTH MODE)
# -----------------------------
async def hunt_and_post():
    rss_url = "https://www.desidime.com/new.rss"
    posted_deals = get_posted_deals()
    
    try:
        # Bypass Cloudflare using a disguised browser request
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Referer": "https://www.google.com/"
        }
        response = requests.get(rss_url, headers=headers, timeout=15)
        feed = feedparser.parse(response.content)
        
        if not feed.entries:
            print("⚠️ No entries found. Feed might be empty or blocked.")
            return
            
    except Exception as e:
        print(f"⚠️ Feed fetch failed: {e}")
        return

    supported_stores = [
        'amazon.in', 'flipkart.com', 'myntra.com', 'ajio.com', 
        'tatacliq.com', 'croma.com', 'reliancedigital.in', 'nykaa.com'
    ]

    new_finds = 0
    skipped_old = 0
    skipped_store = 0

    for entry in feed.entries:
        deal_id = entry.id if hasattr(entry, 'id') else entry.link
        
        if deal_id in posted_deals:
            skipped_old += 1
            continue
            
        raw_community_link = entry.link
        clean_url = get_clean_destination_url(raw_community_link)
        
        if any(store in clean_url.lower() for store in supported_stores):
            new_finds += 1
            print(f"🎯 NEW MATCH Found! Generating API link...")
            
            # Hit the Cuelinks API directly
            api_short_link = generate_cuelinks_api_url(clean_url)

            # Strict generic formatting without brand names
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
                await asyncio.sleep(4) 
            except Exception as e:
                print(f"❌ Telegram Error: {e}")
        else:
            skipped_store += 1

    print(f"📊 Scan Complete | Posted: {new_finds} | Ignored (Already Posted): {skipped_old} | Ignored (Unsupported Store): {skipped_store}")

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
    print("🚀 API-First Cuelinks Interceptor Bot Started!")
    asyncio.run(run_bot())
    
