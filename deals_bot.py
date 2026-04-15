import requests
from bs4 import BeautifulSoup
import os
import random
import asyncio
import time
from datetime import datetime
from telegram import Bot

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
# AMAZON SCRAPER
# -----------------------------
def get_amazon_deals(query):
    url = f"https://www.amazon.in/s?k={query.replace(' ', '+')}&tag={AMAZON_TAG}"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-IN,en;q=0.9"
    }

    try:
        time.sleep(random.uniform(2, 4))  # avoid blocking
        res = requests.get(url, headers=headers, timeout=20)
        soup = BeautifulSoup(res.text, "lxml")

        products = soup.find_all("div", {"data-component-type": "s-search-result"})[:3]

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
# TELEGRAM SENDER (HTML SAFE)
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
                parse_mode="HTML",  # ✅ no errors
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
        # Electronics
        "mobiles under 15000", "smartwatch under 2000",
        "earphones under 1000", "bluetooth speaker under 1000",
        "powerbank 10000mah",

        # Home
        "mixer grinder", "pressure cooker 5 litre",
        "electric kettle", "air fryer under 5000",

        # Fashion
        "tshirt men pack", "shirts for men", "jeans for men",

        # Grocery
        "rice 5kg", "atta 5kg", "tea powder 1kg",

        # Beauty
        "face wash men", "shampoo 650ml", "hair oil"
    ]

    while True:
        print(f"\n🚀 {datetime.now().strftime('%H:%M')}")

        selected = random.sample(categories, 6)

        for query in selected:
            print(f"🔍 {query}")

            deals = get_amazon_deals(query)
            if deals:
                await send_deals(deals)

        print("😴 Sleeping 5 minutes...\n")
        await asyncio.sleep(300)


# -----------------------------
# START
# -----------------------------
if __name__ == "__main__":
    print("🚀 Deals Bot Started")
    asyncio.run(run_bot())
