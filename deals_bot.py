import requests
import asyncio
from aiogram import Bot
import time
import os
import random
from bs4 import BeautifulSoup
from datetime import datetime

BOT_TOKEN = os.getenv('BOT_TOKEN')
channel_id_str = os.getenv('CHANNEL_ID')
AMAZON_TAG = os.getenv('AMAZON_TAG', 'indiafindsao7-21')  # Your Amazon tag

if not BOT_TOKEN or not channel_id_str:
    print("❌ Required vars missing!")
    exit(1)
CHANNEL_ID = int(channel_id_str)
print(f"✅ Bot ready: {CHANNEL_ID} | Amazon Tag: {AMAZON_TAG}")

bot = Bot(token=BOT_TOKEN)

def get_amazon_search_deals(query="mobiles under 15000"):

    url = f"https://www.amazon.in/s?k={query.replace(' ', '+')}&tag={AMAZON_TAG}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
        "Accept-Language": "en-IN,en;q=0.9"
    }
    try:
        time.sleep(random.uniform(2,4))
        resp = requests.get(url, headers=headers, timeout=25)
        print(f"   Status: {resp.status_code} | Size: {len(resp.text)//1000}KB")

        soup = BeautifulSoup(resp.text, 'html.parser')
        deals = []












        # Multiple Amazon product container strategies
        product_containers = (
            soup.find_all('div', {'data-component-type': 's-search-result'}) or
            soup.find_all('div', {'data-asin': True}) or
            soup.find_all('h2', class_=lambda x: x and 'a-size' in str(x)) or
            soup.select('.s-result-item[data-asin]')
        )
        
        print(f"   Found {len(product_containers)} potential products")
        
        for i, p in enumerate(product_containers[:4]):
            # Title - multiple selectors
            title = None
            for selector in ['h2 a span', '.a-text-normal', 'h2']:
                title_elem = p.select_one(selector)
                if title_elem and title_elem.text.strip():
                    title = title_elem.text.strip()[:120]
                    break
            
            # Price - multiple selectors  
            price = None
            for selector in ['.a-price-whole', '.a-price .a-offscreen', '[data-testid*="price"]']:
                price_elem = p.select_one(selector)
                if price_elem:
                    price_text = price_elem.text.strip()
                    if '₹' in price_text or price_text.replace('.', '').isdigit():
                        price = price_text
                        break
            
            # Link
            link_elem = p.select_one('a.a-link-normal')
            link = "https://amazon.in" + link_elem['href'] if link_elem and link_elem.get('href') else url
            
            if title and len(title) > 10:
                deals.append((title, price or "₹Check", link))
                print(f"   ✅ #{i+1}: {title[:50]}...")
                break  # First good deal only
        
        return deals if deals else []
        
    except Exception as e:
        print(f"   ❌ Amazon error: {e}")
        return []

def get_desidime_deals():
    """DesiDime public deals (proven loot source)"""
    try:
        url = "https://www.desidime.com/latest?category=deals"
        resp = requests.get(url, timeout=15)
        soup = BeautifulSoup(resp.text, 'html.parser')

        deals = []
        for item in soup.find_all('div', class_='deal-box')[:3]:
            title = item.find('h3').text.strip()
            link = item.find('a')['href']
            price = item.find(class_='deal-price')
            price = price.text.strip() if price else 'Check Deal'

            deals.append((title, price, "https://desidime.com" + link))
        return deals
    except:
        return []

async def post_deals(deals, source):
    for title, price, url in deals:
        message = f"🔥 *{source} LOOT DEAL*\n\n{title}\n💰 `{price}`\n\n🛒 {url}\n\n*Affiliate | Cashback Available*"
        try:
            await bot.send_message(CHANNEL_ID, message, parse_mode='Markdown', disable_web_page_preview=True)
            print(f"✅ Posted {source}: {title[:30]}")
            time.sleep(2)
        except Exception as e:
            print(f"❌ Post error: {e}")

def monitor_loop():
    # Hyderabad/India TOP categories (2026 best-sellers)
    categories = [
        # Electronics (40% sales)
        "mobiles under 15000", "smartwatch under 2000", "earphones under 1000", "powerbank 10000mah", 
        "bluetooth speaker under 1000", "led tv under 15000",

        # Home & Kitchen (top growing)
        "mixer grinder under 2000", "pressure cooker 5l", "water bottle steel", "induction cooktop", 
        "air fryer under 5000", "room heater under 1500", "electric kettle 1.5l",

        # Fashion & Daily
        "tshirt men pack of 4", "socks pack of 6", "briefs pack of 5", "saree under 1000", 
        "kurti women cotton",

        # Beauty & Personal Care
        "facewash men", "shampoo 650ml", "body lotion 500ml", "hair oil 200ml",

        # Grocery & Essentials
        "atta 5kg", "rice 5kg", "oil 5l", "detergent powder 4kg",

        # Baby & Health
        "diaper pack", "baby wipes", "protein powder 1kg"
    ]

    while True:
        print(f"\n🚀 Cycle: {datetime.now().strftime('%H:%M')} | {len(categories)} categories")

        # Rotate 8-12 categories per cycle (avoid spam)
        random.shuffle(categories)
        cycle_cats = categories[:10]  # 10 per cycle

        for query in cycle_cats:
            print(f"📦 Searching: '{query}'")
            deals = get_amazon_search_deals(query)
            if deals:
                asyncio.run(post_deals(deals, "Amazon"))
                time.sleep(5)  # Telegram rate limit

        # DesiDime bonus
        desi_deals = get_desidime_deals()
        if desi_deals:
            asyncio.run(post_deals(desi_deals, "DesiDime"))

        print(f"✅ Cycle done | Next in 4min")
        time.sleep(240)  # 4min cycles = 360 deals/day

if __name__ == "__main__":
    print("🚀 Amazon + DesiDime Deals Bot!")
    monitor_loop()
