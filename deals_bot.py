import requests
from bs4 import BeautifulSoup
import os
import time
import random
from datetime import datetime
import telegram  # pip install python-telegram-bot==20.7

BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID', '-1003919019248'))
AMAZON_TAG = os.getenv('AMAZON_TAG', 'indiafindsao7-21')

if not BOT_TOKEN:
    print("❌ BOT_TOKEN missing!")
    exit(1)

bot = telegram.Bot(token=BOT_TOKEN)

def get_amazon_deals(query):
    url = f"https://www.amazon.in/s?k={query.replace(' ', '+')}&tag={AMAZON_TAG}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        resp = requests.get(url, headers=headers, timeout=20)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        products = soup.find_all('div', {'data-component-type': 's-search-result'})[:2]
        deals = []
        for p in products:
            title = p.h2.text.strip()[:100] if p.h2 else None
            price = p.find('span', class_='a-price-whole')
            price = f"₹{price.text}" if price else "₹Live"
            link = "https://amazon.in" + p.a['href'] if p.a else url
            
            if title:
                deals.append((title, price, link))
        return deals
    except:
        return []

def monitor_loop():
    categories = ["smartwatch under 2000", "powerbank 10000mah", "earphones tws", "kitchen mixer grinder"]
    
    while True:
        print(f"\n🚀 {datetime.now().strftime('%H:%M')}")
        random.shuffle(categories)
        
        for query in categories:
            print(f"🔍 {query}")
            deals = get_amazon_deals(query)
            for title, price, link in deals:
                message = f"🔥 AMAZON DEAL\n\n{title}\n{price}\n\n{link}"
                try:
                    bot.send_message(chat_id=CHANNEL_ID, text=message, disable_web_page_preview=True)
                    print(f"✅ Posted {title[:30]}")
                    time.sleep(3)
                except Exception as e:
                    print(f"❌ {e}")
        
        time.sleep(300)  # 5min

if __name__ == "__main__":
    print("🚀 SIMPLE Deals Bot - NEW TOKEN REQUIRED")
    monitor_loop()
