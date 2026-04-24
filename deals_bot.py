import feedparser
import requests
import asyncio
import os
import re
from telegram import Bot
from datetime import datetime
import pyshorteners

# -----------------------------
# ENV VARIABLES
# -----------------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID", "-100xxxxxxxxxx")

# Your Cuelinks MACID (e.g., 123456T789012)
CUELINKS_MACID = os.getenv("CUELINKS_MACID", "your_macid_here")

bot = Bot(token=BOT_TOKEN)
shortener = pyshorteners.Shortener()
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
    """Follows redirects to bypass community tracking links and get the raw URL."""
    try:
        # We use a standard User-Agent so we don't get blocked during the redirect hop
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.head(short_url, allow_redirects=True, headers=headers, timeout=10)
        
        # Strip out any existing affiliate tags attached to the raw URL
        clean_url = response.url.split('?')[0] 
        return clean_url
    except:
        return short_url

def generate_cuelinks_url(raw_url):
    """Wraps the clean URL in your Cuelinks tracking structure."""
    # Cuelinks standard redirect format
    tracking_link = f"https://links.cuelinks.com/v/?macid={CUELINKS_MACID}&url={raw_url}"
    return tracking_link

# -----------------------------
# RSS INTERCEPTOR
# -----------------------------
async def hunt_and_post():
    # DesiDime's front page RSS feed 
    rss_url = "https://www.desidime.com/new.rss"
    
    posted_deals = get_posted_deals()
    
    try:
        feed = feedparser.parse(rss_url)
    except Exception as e:
        print(f"⚠️ RSS parsing failed: {e}")
        return

    for entry in feed.entries:
        deal_id = entry.id if hasattr(entry, 'id') else entry.link
        
        if deal_id in posted_deals:
            continue
            
        title = entry.title
        raw_community_link = entry.link
        
        # 1. Clean the link to find the true destination
        clean_url = get_clean_destination_url(raw_community_link)
        
        # 2. Verify it's a supported e-commerce site before posting
        supported_stores = ['amazon.in', 'flipkart.com', 'myntra.com', 'ajio.com', 'tatacliq.com']
        
        if any(store in clean_url.lower() for store in supported_stores):
            print(f"🔄 Processing: {title[:50]}...")
            
            # 3. Monetize via Cuelinks tracking structure
            monetized_link = generate_cuelinks_url(clean_url)

            # 4. Shorten the final Cuelinks URL so it looks clean in Telegram
            try:
                tiny_url = shortener.tinyurl.short(monetized_link)
            except:
                tiny_url = monetized_link

            # 5. Construct Telegram Message
            msg = f"🔥 <b>Trending Loot Alert!</b>\n\n"
            msg += f"📦 {title}\n\n"
            msg += f"🛒 <b>Grab it here:</b> {tiny_url}"

            try:
                await bot.send_message(
                    chat_id=CHANNEL_ID,
                    text=msg,
                    parse_mode="HTML",
                    disable_web_page_preview=False
                )
                print(f"✅ Posted successfully!")
                save_posted_deal(deal_id)
                
                # Crucial anti-spam pause to protect your Telegram bot token
                await asyncio.sleep(4) 
            except Exception as e:
                print(f"❌ Telegram Error: {e}")

# -----------------------------
# MAIN LOOP
# -----------------------------
async def run_bot():
    while True:
        print(f"⚡ [{datetime.now().strftime('%H:%M:%S')}] Scanning RSS Feeds...")
        await hunt_and_post()
        
        # Sleep for 3 minutes before checking for new deals again
        print("⏳ Waiting 3 minutes...\n")
        await asyncio.sleep(180) 

if __name__ == "__main__":
    print("🚀 Cuelinks + RSS Interceptor Bot Started!")
    asyncio.run(run_bot())
