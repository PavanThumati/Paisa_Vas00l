import feedparser
import requests
import asyncio
import os
from telegram import Bot
from datetime import datetime
import pyshorteners

# -----------------------------
# ENV VARIABLES
# -----------------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID", "-100xxxxxxxxxx")
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
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.head(short_url, allow_redirects=True, headers=headers, timeout=10)
        return response.url.split('?')[0] 
    except:
        return short_url

def generate_cuelinks_url(raw_url):
    return f"https://links.cuelinks.com/v/?macid={CUELINKS_MACID}&url={raw_url}"

# -----------------------------
# RSS INTERCEPTOR (ENHANCED)
# -----------------------------
async def hunt_and_post():
    rss_url = "https://www.desidime.com/new.rss"
    posted_deals = get_posted_deals()
    
    try:
        feed = feedparser.parse(rss_url)
    except Exception as e:
        print(f"⚠️ RSS parsing failed: {e}")
        return

    # Expanded list of stores supported by Cuelinks
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
            
        title = entry.title
        raw_community_link = entry.link
        
        clean_url = get_clean_destination_url(raw_community_link)
        
        if any(store in clean_url.lower() for store in supported_stores):
            new_finds += 1
            print(f"🎯 NEW MATCH: {title[:50]}...")
            
            monetized_link = generate_cuelinks_url(clean_url)

            try:
                tiny_url = shortener.tinyurl.short(monetized_link)
            except:
                tiny_url = monetized_link

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
                await asyncio.sleep(4) 
            except Exception as e:
                print(f"❌ Telegram Error: {e}")
        else:
            skipped_store += 1

    # Verbose logging to show the bot is actively working
    print(f"📊 Scan Complete | Posted: {new_finds} | Ignored (Already Posted): {skipped_old} | Ignored (Unsupported Store): {skipped_store}")

# -----------------------------
# MAIN LOOP
# -----------------------------
async def run_bot():
    while True:
        print(f"\n⚡ [{datetime.now().strftime('%H:%M:%S')}] Fetching latest deals...")
        await hunt_and_post()
        
        # Reduced sleep time for highly aggressive polling
        print("⏳ Waiting 60 seconds...\n")
        await asyncio.sleep(60) 

if __name__ == "__main__":
    print("🚀 Enhanced Cuelinks Interceptor Bot Started!")
    asyncio.run(run_bot())
