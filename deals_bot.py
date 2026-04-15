import requests
from bs4 import BeautifulSoup
import asyncio
from aiogram import Bot
import time
import os
import random
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Env vars
BOT_TOKEN = os.getenv('BOT_TOKEN')
channel_id_str = os.getenv('CHANNEL_ID')
if not BOT_TOKEN:
    print("❌ BOT_TOKEN missing! Set in Railway Variables.")
    exit(1)
if not channel_id_str:
    print("❌ CHANNEL_ID missing! Forward channel msg to @userinfobot.")
    exit(1)
CHANNEL_ID = int(channel_id_str)
print(f"✅ Bot ready: {CHANNEL_ID}")

bot = Bot(token=BOT_TOKEN)

# Session with retries
session = requests.Session()
retry_strategy = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("http://", adapter)
session.mount("https://", adapter)

def scrape_flipkart_category(url):
    # Rotating real browser headers (2026 working)
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
    ]
    headers = {
        "User-Agent": random.choice(user_agents),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,hi;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0"
    }
    
    try:
        time.sleep(random.uniform(3, 6))  # Human-like delay
        resp = session.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        print(f"✅ Page loaded: {len(resp.text)//1000}KB from {url}")
        
        # Multiple selector strategies (2026 Flipkart)
        products = []
        selectors = [
            'div[data-testid="product-tile"]',
            'div._13oc-S',
            'div[class*="_4ddWXP"]',
            'div.col-12-12'
        ]
        
        for selector in selectors:
            products = soup.select(selector)
            if products:
                print(f"✅ Found {len(products)} products with {selector}")
                break
        
        products = products[:5]  # Top 5 only
        deals = []
        
        for p in products:
            # Robust title extraction
            title = None
            title_selectors = ['div._4rR01T', 'a._2UzuV9 span', '[data-testid="product-title"]']
            for ts in title_selectors:
                title_elem = p.select_one(ts)
                if title_elem and title_elem.text.strip():
                    title = title_elem.text.strip()[:100]
                    break
            
            # Robust price extraction
            price = None
            price_selectors = ['div._30jeq3', '._1_WHN1', '._25b18c', '.price']
            for ps in price_selectors:
                price_elem = p.select_one(ps)
                if price_elem and '₹' in price_elem.text:
                    price = price_elem.text.strip()
                    break
            
            link_elem = p.select_one('a[href]')
            link = "https://www.flipkart.com" + link_elem['href'] if link_elem and link_elem.get('href') else url
            
            if title and price and len(title) > 10:
                deals.append((title, price, link))
                print(f"✅ Deal found: {title[:40]}... - {price}")
        
        return deals
        
    except Exception as e:
        print(f"❌ Scrape failed: {e}")
        return []

async def post_deals(deals):
    for title, price, url in deals:
        message = f"🔥 HOT DEAL!\n\n{title}\n{price}\n\n🛒 {url}"
        try:
            await bot.send_message(CHANNEL_ID, message)
            print(f"✅ Posted: {title[:30]}...")
            time.sleep(2)  # Rate limit Telegram
        except Exception as e:
            print(f"❌ Post error: {e}")

def monitor_loop():
    categories = [
        "https://www.flipkart.com/search?q=mobiles&otracker=search&otracker1=search&marketplace=FLIPKART&as-show=on&as=off",
        "https://www.flipkart.com/search?q=electronics&otracker=search&otracker1=search&marketplace=FLIPKART&as-show=on&as=off",
        "https://www.flipkart.com/laptops/~buy-30-off-on-laptops/pr?sid=6bo,b5g"
    ]
    
    while True:
        print(f"\n🚀 Starting scrape cycle ({time.strftime('%H:%M:%S')})")
        for i, cat in enumerate(categories, 1):
            print(f"📱 Scraping category {i}/{len(categories)}: {cat.split('?')[0]}")
            deals = scrape_flipkart_category(cat)
            if deals:
                asyncio.run(post_deals(deals))
            else:
                print("❌ No deals found this category")
        
        print("😴 Cycle complete, sleeping 120s...")
        time.sleep(120)  # 2min cycle for stability

if __name__ == "__main__":
    print("🚀 Starting Deals Bot on Railway...")
    print("💡 Posts every 2min across mobiles/electronics/laptops")
    monitor_loop()
