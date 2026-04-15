import requests
from bs4 import BeautifulSoup
import asyncio
from aiogram import Bot
import time
import threading
import os

BOT_TOKEN = os.getenv('BOT_TOKEN')
channel_id_str = os.getenv('CHANNEL_ID')
if not BOT_TOKEN:
    print("❌ BOT_TOKEN missing! Set in Railway Variables.")
    exit(1)
if not channel_id_str:
    print("❌ CHANNEL_ID missing! Forward channel msg to @userinfobot, copy negative ID to Railway Variables.")
    exit(1)
CHANNEL_ID = int(channel_id_str)
print(f"✅ Bot ready: {CHANNEL_ID}")

bot = Bot(token=BOT_TOKEN)

def scrape_flipkart_category(url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"}
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Current Flipkart search selectors (2026)
        products = soup.find_all('div', {'class': '_13oc-S'})[:5]  # Product containers
        deals = []
        for p in products:
            title_tag = p.find('div', {'class': '_4rR01T'}) or p.find('a', {'class': '_2UzuV9'})
            title = title_tag.text.strip() if title_tag else 'N/A'
            
            price_tag = p.find('div', {'class': '_30jeq3 _1_WHN1'}) or p.find('_25b18c')
            price = price_tag.text.strip() if price_tag else 'N/A'
            
            link_tag = p.find('a', href=True)
            link = "https://www.flipkart.com" + link_tag['href'] if link_tag else url
            
            if '₹' in price and title != 'N/A' and len(title) > 5:
                print(f"Found: {title[:50]}... {price}")
                deals.append((title, price, link))
        return deals
    except Exception as e:
        print(f"Scrape error: {e}")
        return []

async def post_deals(deals):
    for title, price, url in deals:
        message = f"🔥 HOT DEAL\n{title}\n{price}\n{url}"
        try:
            await bot.send_message(CHANNEL_ID, message)
            print(f"Posted: {title}")
        except Exception as e:
            print(f"Post error: {e}")

def monitor_loop():
    categories = [
        "https://www.flipkart.com/search?q=mobiles&otracker=search",
        "https://www.flipkart.com/search?q=electronics&otracker=search"
    ]
    while True:
        for cat in categories:
            deals = scrape_flipkart_category(cat)
            if deals:
                asyncio.run(post_deals(deals))
        print("Cycle complete, sleeping 90s...")
        time.sleep(90)  # 1.5min rapid cycle

if __name__ == "__main__":
    print("Starting Deals Bot...")
    monitor_loop()
