import feedparser
import requests
import cloudscraper
import asyncio
import os
import re
import urllib.parse
from bs4 import BeautifulSoup
from telegram import Bot
from datetime import datetime

# -----------------------------
# ENV VARIABLES
# -----------------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID", "-100xxxxxxxxxx")
CUELINKS_API_TOKEN = os.getenv("CUELINKS_API_TOKEN", "your_api_token_here")
AMAZON_TAG = os.getenv("AMAZON_TAG", "yourtag-21") # Crucial for direct Amazon links

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
# LINK PROCESSING & ROUTING
# -----------------------------
def get_clean_destination_url(url):
    """Unwraps blog redirectors (like visit.php?go=) and gets the pure URL."""
    try:
        # 1. Unwrap redirect parameters from deal blogs
        if "go=" in url or "url=" in url:
            parsed = urllib.parse.urlparse(url)
            qs = urllib.parse.parse_qs(parsed.query)
            for param in ['go', 'url']:
                if param in qs:
                    url = qs[param][0]
                    break
        
        # 2. Follow shortlinks (amzn.to, fkrt.it) to their final destination
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.head(url, allow_redirects=True, headers=headers, timeout=10)
        clean_url = response.url.split('?')[0] # Strip existing tracking garbage
        return clean_url
    except:
        return url

def generate_amazon_affiliate_url(raw_url):
    """Bypasses Cuelinks to give you 100% direct Amazon commission."""
    match = re.search(r'/([A-Z0-9]{10})(?:[/?]|$)', raw_url)
    if match:
        asin = match.group(1)
        return f"https://www.amazon.in/dp/{asin}?tag={AMAZON_TAG}"
    return raw_url

def generate_cuelinks_api_url(raw_url):
    """Fallback for Flipkart, Myntra, etc."""
    api_endpoint = "https://www.cuelinks.com/api/v2/get_link"
    headers = {"token": CUELINKS_API_TOKEN, "Content-Type": "application/json"}
    payload = {"url": raw_url}
    
    try:
        response = requests.post(api_endpoint, headers=headers, json=payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get('short_url') or data.get('affiliate_url', raw_url)
        return raw_url
    except:
        return raw_url

def get_tiny_url(long_url):
    """Creates a shortlink natively without extra libraries."""
    try:
        res = requests.get(f"https://tinyurl.com/api-create.php?url={long_url}", timeout=10)
        if res.status_code == 200:
            return res.text
    except:
        pass
    return long_url

# -----------------------------
# DATA EXTRACTION
# -----------------------------
def extract_price(text):
    """Hunts for Rs. or ₹ in the title."""
    match = re.search(r'(?:Rs\.?|₹)\s*([\d,]+)', text, re.IGNORECASE)
    if match:
        return f"₹{match.group(1)}"
    return "₹Check Link"

# -----------------------------
# RSS INTERCEPTOR (THE ENGINE)
# -----------------------------
async def hunt_and_post():
    rss_sources = [
        "https://indiafreestuff.in/feed/",
        "https://www.savemoneyindia.com/feed/"
    ]
    
    posted_deals = get_posted_deals()
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True})
    
    supported_stores = [
        'amazon.in', 'amzn.to', 'flipkart.com', 'fkrt.it', 'myntra.com', 
        'ajio.com', 'tatacliq.com', 'croma.com', 'nykaa.com'
    ]

    new_finds = 0

    for rss_url in rss_sources:
        try:
            response = scraper.get(rss_url, timeout=20)
            feed = feedparser.parse(response.content)
            if not feed.entries: continue
        except:
            continue

        for entry in feed.entries:
            deal_id = entry.id if hasattr(entry, 'id') else entry.link
            if deal_id in posted_deals: continue
            
            title = entry.title
            deal_page_url = entry.link
            target_url = None
            image_url = None
            price = extract_price(title)

            # Deep Scrape: Visit the deal page
            try:
                page_res = scraper.get(deal_page_url, timeout=15)
                soup = BeautifulSoup(page_res.text, "html.parser")
                
                # 1. Grab the product image
                img_tag = soup.find('img')
                if img_tag and img_tag.get('src'):
                    image_url = img_tag['src']
                
                # 2. Grab the store link
                for a_tag in soup.find_all('a', href=True):
                    href = a_tag['href']
                    # Check the un-encoded version of the link just in case
                    unwrapped = urllib.parse.unquote(href)
                    if any(store in unwrapped.lower() for store in supported_stores):
                        target_url = unwrapped
                        break 
                        
            except Exception as e:
                print(f"⚠️ Failed to scrape page: {e}")
                continue

            if target_url and image_url:
                clean_url = get_clean_destination_url(target_url)
                
                # ROUTING LOGIC: Amazon vs Cuelinks
                if 'amazon.in' in clean_url.lower() or 'amzn.to' in clean_url.lower():
                    print(f"🎯 AMAZON DEAL FOUND! Generating direct Amazon Tag...")
                    affiliated_long_url = generate_amazon_affiliate_url(clean_url)
                else:
                    print(f"🎯 OTHER DEAL FOUND! Routing to Cuelinks API...")
                    affiliated_long_url = generate_cuelinks_api_url(clean_url)

                # Generate the Shortlink
                short_link = get_tiny_url(affiliated_long_url)

                # Format the message exactly like the requested screenshot
                # Generic description formatting maintained
                msg = f"🔥🔥 {title}\n\n"
                msg += f"🎁 Deal Price : {price}\n\n"
                msg += f"Buy Here : {short_link}\n\n"
                msg += f"⚡⚡ Apply Coupon (If applicable)\n"

                try:
                    # Send as an Image Post
                    await bot.send_photo(
                        chat_id=CHANNEL_ID,
                        photo=image_url,
                        caption=msg,
                        parse_mode="HTML"
                    )
                    print(f"✅ Posted successfully!")
                    save_posted_deal(deal_id)
                    new_finds += 1
                    await asyncio.sleep(4) 
                except Exception as e:
                    print(f"❌ Telegram Error (Photo might be invalid): {e}")
            else:
                # Mark as scanned even if no valid store links were found
                save_posted_deal(deal_id)

    if new_finds > 0:
        print(f"📊 Scan Complete | New Deals Posted: {new_finds}")

# -----------------------------
# MAIN LOOP
# -----------------------------
async def run_bot():
    while True:
        print(f"\n⚡ [{datetime.now().strftime('%H:%M:%S')}] Scanning feeds & deep-scraping pages...")
        await hunt_and_post()
        print("⏳ Waiting 60 seconds...\n")
        await asyncio.sleep(60) 

if __name__ == "__main__":
    print("🚀 Auto-Deal Bot Started (Direct Amazon + Cuelinks Fallback)!")
    asyncio.run(run_bot())
    
