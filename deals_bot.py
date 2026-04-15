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
    """Amazon search scraper (easier than PAAPI)"""
    url = f"https://www.amazon.in/s?k={query.replace(' ', '+')}&tag={AMAZON_TAG}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=20)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        deals = []
        products = soup.find_all('div', {'data-component-type': 's-search-result'})[:4]
        for p in products:
            title = p.find('h2')
            if title:
                title = title.text.strip()[:100]
                price = p.find('span', 'a-price-whole')
                price = price.text.strip() + p.find('span', 'a-price-fraction') if price else '₹N/A'
                link = p.find('a', 'a-link-normal')['href']
                link = "https://amazon.in" + link if link else url
                
                deals.append((title, price, link))
        
        return deals
    except:
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
    queries = ["mobiles under 15000", "earphones under 1000", "powerbank deals"]
    
    while True:
        print(f"\n🚀 Cycle: {datetime.now().strftime('%H:%M')}")
        
        # Amazon rotating queries
        for query in queries:
            print(f"📦 Amazon: {query}")
            deals = get_amazon_search_deals(query)
            if deals:
                asyncio.run(post_deals(deals, "Amazon"))
        
        # DesiDime
        print("🏷️ DesiDime deals...")
        desi_deals = get_desidime_deals()
        if desi_deals:
            asyncio.run(post_deals(desi_deals, "DesiDime"))
        
        print("😴 5min sleep...")
        time.sleep(300)

if __name__ == "__main__":
    print("🚀 Amazon + DesiDime Deals Bot!")
    monitor_loop()
