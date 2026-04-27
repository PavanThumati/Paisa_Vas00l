import requests
from bs4 import BeautifulSoup
import os
import random
import asyncio
import time
from datetime import datetime
from telegram import Bot
import cloudscraper

# -----------------------------
# ENV VARIABLES
# -----------------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "-100xxxxxxxxxx"))
AMAZON_TAG = os.getenv("AMAZON_TAG", "yourtag-21")

if not BOT_TOKEN:
    print("❌ BOT_TOKEN missing")
    exit()

bot = Bot(token=BOT_TOKEN)

# -----------------------------
# GLOBAL SCRAPER (IMPORTANT FIX)
# -----------------------------
scraper = cloudscraper.create_scraper()

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/120 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15"
]

# -----------------------------
# AMAZON SCRAPER (IMPROVED)
# -----------------------------
def get_amazon_deals(query):
    url = f"https://www.amazon.in/s?k={query.replace(' ', '+')}&tag={AMAZON_TAG}"

    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "en-IN,en;q=0.9",
        "Connection": "keep-alive"
    }

    try:
        # Slower requests = less blocking
        time.sleep(random.uniform(6, 12))

        res = scraper.get(url, headers=headers, timeout=20)

        if res.status_code == 503:
            print("⚠️ Amazon blocked (503). Skipping...")
            return []

        soup = BeautifulSoup(res.text, "html.parser")

        products = soup.find_all("div", {"data-component-type": "s-search-result"})[:3]

        if not products:
            print("⚠️ No products found (soft block)")
            return []

        deals = []
        for p in products:
            title_tag = p.find("h2")
            title = title_tag.text.strip() if title_tag else None

            price_tag = p.find("span", class_="a-price-whole")
            price = f"₹{price_tag.text}" if price_tag else "₹Check"

            link_tag = p.find("a", class_="a-link-normal")
            link = "https://amazon.in" + link_tag["href"] if link_tag else url

            if title:
                deals.append((title[:100], price, link))

        return deals

    except Exception as e:
        print(f"❌ Scrape error: {e}")
        return []

# -----------------------------
# TELEGRAM SENDER
# -----------------------------
async def send_deals(deals):
    for title, price, link in deals:
        try:
            msg = f"""🔥 <b>Amazon Deal</b>

{title}
<b>{price}</b>

🛒 <a href="{link}">Buy Now</a>
"""

            await bot.send_message(
                chat_id=CHANNEL_ID,
                text=msg,
                parse_mode="HTML",
                disable_web_page_preview=False
            )

            print(f"✅ Posted: {title[:40]}")
            await asyncio.sleep(3)

        except Exception as e:
            print(f"❌ Telegram error: {e}")

# -----------------------------
# MAIN LOOP
# -----------------------------
async def run_bot():
    categories = [
        "smartphones under 15000", "smartwatch under 2000",
        "earphones under 1000", "bluetooth speaker under 1000",
        "powerbank 10000mah", "tshirt men pack",
        "rice 5kg", "atta 5kg", "tea powder 1kg",
        "face wash men", "shampoo 650ml",
        "pressure cooker 5 litre", "mixer grinder"
    ]

    while True:
        print(f"\n🚀 {datetime.now().strftime('%H:%M')}")

        # Reduce load (IMPORTANT)
        selected = random.sample(categories, 3)

        for query in selected:
            print(f"🔍 {query}")

            deals = get_amazon_deals(query)
            if deals:
                await send_deals(deals)

        print("😴 Sleeping 10 minutes...\n")
        await asyncio.sleep(200)

# -----------------------------
# START
# -----------------------------
if __name__ == "__main__":
    print("🚀 Deals Bot Started")
    asyncio.run(run_bot())
