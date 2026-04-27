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
AMAZON_TAG = os.getenv("AMAZON_TAG", "yourtag-21") 

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
def is_valid_product_link(url):
    """Strictly filters out category/store pages to ensure we only post specific products."""
    url_lower = url.lower()
    
    # Block these generic sale/category indicators completely
    invalid_patterns = ['/b?', '/stores/', '/h/rewards/', '/offers-list/', '/category/']
    if any(pattern in url_lower for pattern in invalid_patterns):
        return False
        
    # Must contain a specific product identifier
    valid_patterns = ['/dp/', '/gp/product/', 'amzn.to', '/p/', 'fkrt.it']
    if any(pattern in url_lower for pattern in valid_patterns):
        return True
        
    return False

def get_clean_destination_url(url):
    """Unwraps blog redirectors and gets the pure URL."""
    try:
        # Unwrap parameters like visit.php?go=
        if "go=" in url or "url=" in url:
            parsed = urllib.parse.urlparse(url)
            qs = urllib.parse.parse_qs(parsed.query)
            for param in ['go', 'url']:
                if param in qs:
                    url = qs[param][0]
                    break
        
        # Follow network redirects to find the real destination
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.head(url, allow_redirects=True, headers=headers, timeout=10)
        return response.url.split('?')[0] 
    except:
        return url

def generate_amazon_affiliate_url(raw_url):
    """Bypasses Cuelinks for 100% direct Amazon commission."""
    match = re.search(r'/([A-Z0-9]{10})(?:[/?]|$)', raw_url)
    if match:
        asin = match.group(1)
        return f"https://www.amazon.in/dp/{asin}?tag={AMAZON_TAG}"
    return raw_url

def generate_cuelinks_api_url(raw_url):
    """Fallback for Flipkart, Myntra, etc. via Cuelinks."""
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
# RSS INTERCEPTOR 
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

            try:
                page_res = scraper.get(deal_page_url, timeout=15)
                soup = BeautifulSoup(page_res.text, "html.parser")
                
                # 1. SMART IMAGE TARGETING: Skip the site logo, look inside the article body
                content_area = soup.find('div', class_=re.compile(r'entry-content|post-content|content', re.IGNORECASE))
                if content_area:
                    for img in content_area.find_all('img'):
                        src = img.get('src', '')
                        if src and 'logo' not in src.lower() and not src.startswith('data:image'):
                            image_url = src
                            break
                
                if not image_url:
                    for img in soup.find_all('img'):
                        src = img.get('src', '')
                        if src and 'logo' not in src.lower() and not src.startswith('data:image'):
                            image_url = src
                            break

                # 2. Grab and strictly validate the store link
                for a_tag in soup.find_all('a', href=True):
                    href = a_tag['href']
                    unwrapped = urllib.parse.unquote(href)
                    
                    if any(store in unwrapped.lower() for store in supported_stores):
                        if is_valid_product_link(unwrapped):
                            target_url = unwrapped
                            break 
                        
            except Exception as e:
                print(f"⚠️ Failed to scrape page: {e}")
                continue

            # Only proceed if we found BOTH a valid product link and an image
            if target_url and image_url:
                clean_url = get_clean_destination_url(target_url)
                store_name = "Store"
                
                # Monetization Routing
                if 'amazon.in' in clean_url.lower() or 'amzn.to' in clean_url.lower():
                    print(f"🎯 AMAZON PRODUCT FOUND! Generating direct tag...")
                    affiliated_long_url = generate_amazon_affiliate_url(clean_url)
                    store_name = "Amazon"
                else:
                    print(f"🎯 OTHER PRODUCT FOUND! Routing to Cuelinks API...")
                    affiliated_long_url = generate_cuelinks_api_url(clean_url)
                    if 'flipkart' in clean_url.lower() or 'fkrt' in clean_url.lower():
                        store_name = "Flipkart"
                    elif 'myntra' in clean_url.lower():
                        store_name = "Myntra"

                # Trust-building Telegram formatting (Hidden Hyperlink)
                msg = f"🔥🔥 {title}\n\n"
                msg += f"🎁 Deal Price : {price}\n\n"
                msg += f"🛒 <a href='{affiliated_long_url}'><b>Grab Deal on {store_name}</b></a>\n\n"
                msg += f"⚡⚡ Apply Coupon (If applicable)\n"

                try:
                    await bot.send_photo(
                        chat_id=CHANNEL_ID,
                        photo=image_url,
                        caption=msg,
                        parse_mode="HTML"
                    )
                    print(f"✅ Posted actual product successfully!")
                    save_posted_deal(deal_id)
                    new_finds += 1
                    await asyncio.sleep(4) 
                except Exception as e:
                    print(f"❌ Telegram Error (Photo might be invalid): {e}")
                    save_posted_deal(deal_id)
            else:
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
    print("🚀 Master Auto-Deal Bot Started (Hidden Links + Dual Routing)!")
    asyncio.run(run_bot())
