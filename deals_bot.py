import requests
from bs4 import BeautifulSoup
import asyncio
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
import time
import os
import random
from datetime import datetime

BOT_TOKEN = os.getenv('BOT_TOKEN')
channel_id_str = os.getenv('CHANNEL_ID')
AMAZON_TAG = os.getenv('AMAZON_TAG', 'indiafindsao7-21')

if not BOT_TOKEN or not channel_id_str:
    print("❌ Required vars missing!")
    exit(1)

CHANNEL_ID = int(channel_id_str)
print(f"✅ Bot ready: {CHANNEL_ID} | Tag: {AMAZON_TAG}")

# Fix: Persistent bot session
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode='Markdown'))

def get_amazon_search_deals(query):
    url = f"https://www.amazon.in/s?k={query.replace(' ', '+')}&tag={AMAZON_TAG}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=25)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        deals = []
        products = soup.find_all('div', {'data-component-type': 's-search-result'})[:3]
        
        for p in products:
            title_elem = p.find('h2')
            title = title_elem.text.strip()[:100] if title_elem else None
            
            price_elem = p.find('span', class_='a-price-whole')
            price = f"₹{price_elem.text}" if price_elem else "₹Check"
            
            link_elem = p.find('a', 'a-link-normal')
            link = "https://amazon.in" + link_elem['href'] if link_elem else url
            
            if title:
                deals.append((title, price, link))
                print(f"   ✅ {title[:40]}...")
        
        return deals
    except Exception as e:
        print(f"   ❌ {e}")
        return []

async def post_deals(deals, source):
    for title, price, url in deals:
        message = f"🔥 *{source} DEAL*\n\n{title}\n`{price}`\n\n🛒 {url}"
        try:
            await bot.send_message(CHANNEL_ID, message, disable_web_page_preview=True)
            print(f"✅ Posted: {title[:30]}")
            await asyncio.sleep(2)  # Proper async sleep
        except Exception as e:
            print(f"❌ Post failed: {e}")

def monitor_loop():
    categories = [
        "mobiles under 15000", "smartwatch under 2000", "earphones under 1000", 
        "powerbank 10000mah", "tshirt pack", "kitchen mixer", "pressure cooker",
        "facewash men", "shampoo 650ml", "atta 5kg", "rice 5kg"
    ]
    
    while True:
        print(f"\n🚀 Cycle {datetime.now().strftime('%H:%M')}")
        random.shuffle(categories)
        
        for query in categories[:6]:  # 6 per cycle
            print(f"📦 '{query}'")
            deals = get_amazon_search_deals(query)
            if deals:
                asyncio.run_coroutine_threadsafe(post_deals(deals, "Amazon"), asyncio.new_event_loop())
                time.sleep(5)
        
        print("😴 5min sleep...")
        time.sleep(300)

if __name__ == "__main__":
    print("🚀 Fixed Deals Bot - New Token Required!")
    asyncio.run(bot.get_me())  # Test token
    monitor_loop()
