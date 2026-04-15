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
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        # Find product tiles (adapt selectors)
        products = soup.find_all('div', {'class': '_1AtVbE col-12-12'})[:5]
        deals = []
        for p in products:
            title = p.find('div', {'class': '_4rR01T'}).text.strip() if p.find('div', {'class': '_4rR01T'}) else 'N/A'
            price = p.find('div', {'class': '_30jeq3 _1_WHN1'}).text.strip() if p.find('div', {'class': '_30jeq3 _1_WHN1'}) else 'N/A'
            if '₹' in price and title != 'N/A':
                deals.append((title, price, url))
        return deals
    except Exception as e:
        print(f"Error: {e}")
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
