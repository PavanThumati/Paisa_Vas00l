import requests
from bs4 import BeautifulSoup
import os
import time
import random
from datetime import datetime
from telegram import Bot
from telegram.error import TelegramError

BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID', '-1003919019248'))
AMAZON_TAG = os.getenv('AMAZON_TAG', 'indiafindsao7-21')

if not BOT_TOKEN:
    print("❌ BOT_TOKEN missing in Railway Variables!")
    exit(1)

bot = Bot(token=BOT_TOKEN)

def get_amazon_deals(query):
    url = f"https://www.amazon.in/s?k={query.replace(' ', '+')}&tag={AMAZON_TAG}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        resp = requests.get(url, headers=headers, timeout=20)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        products = soup.find_all('div', {'data-component-type': 's-search-result'})[:3]
        deals = []
        for p in products:
            title = p.h2.text.strip()[:100] if p.h2 else None
            price_span = p.find('span', class_='a-price-whole')
            price = f"₹{price_span.text}" if price_span else "₹Live"
            
            link_a = p.find('a', 'a-link-normal')
            link = "https://amazon.in" + link_a['href'] if link_a else url
            
            if title:
                deals.append(f"🔥 *{title}*\n`{price}`\n{link}")
        return deals
    except Exception as e:
        print(f"Scrape error: {e}")
        return []

def send_deals(deals):
    for deal in deals:
        try:
            bot.send_message(chat_id=CHANNEL_ID, text=deal, parse_mode='Markdown', disable_web_page_preview=True)
            print(f"✅ Posted deal")
            time.sleep(3)
        except TelegramError as e:
            print(f"❌ Telegram error: {e}")

categories = [
    "smartwatch under 2000", "powerbank 10000mah", "earphones under 1000",
    "kitchen mixer grinder", "pressure cooker 5l", "tshirt pack of 4",
    "facewash men", "shampoo 650ml", "atta 5kg"
]

while True:
    print(f"\n🚀 {datetime.now().strftime('%H:%M')} | {len(categories)} cats")
    
    random.shuffle(categories)
    for cat in categories[:5]:
        print(f"🔍 {cat}")
        deals = get_amazon_deals(cat)
        if deals:
            send_deals(deals)
    
    print("Sleep 4min...")
    time.sleep(240)
