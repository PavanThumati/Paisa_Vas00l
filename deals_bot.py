import requests
from bs4 import BeautifulSoup
import os
import time
import random
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
        soup = BeautifulSoup(res.text, "html.parser")

        products = soup.find_all("div", {"data-component-type": "s-search-result"})[:3]

        deals = []
        for p in products:
            # Title
            title_tag = p.find("h2")
            title = title_tag.text.strip() if title_tag else None

            # Price
            price_tag = p.find("span", class_="a-price-whole")
            price = f"₹{price_tag.text}" if price_tag else "₹Check"

            # Link
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
def send_deals(deals):
    for title, price, link in deals:
        msg = f"🔥 *Amazon Deal*\n\n{title}\n`{price}`\n\n🛒 {link}"

        try:
            bot.send_message(
                chat_id=CHANNEL_ID,
                text=msg,
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
            print(f"✅ Posted: {title[:40]}")
            time.sleep(3)  # prevent rate limit

        except Exception as e:
            print(f"❌ Telegram error: {e}")


# -----------------------------
# MAIN LOOP
# -----------------------------
def run_bot():
    categories = [
        # Electronics
        "mobiles under 15000", "smartwatch under 2000", "earphones under 1000",
        "bluetooth speaker under 1000", "powerbank 10000mah", "trimmer for men",
        "gaming mouse", "wifi router",

        # Home & Kitchen
        "mixer grinder", "pressure cooker 5 litre", "induction stove",
        "electric kettle 1.5 litre", "water bottle steel", "tiffin box",
        "air fryer under 5000",

        # Fashion
        "tshirt men pack", "shirts for men", "jeans for men",
        "kurti for women", "saree under 1000", "shoes for men",

        # Beauty
        "face wash men", "shampoo 650ml", "hair oil",
        "body lotion", "perfume for men",

        # Grocery
        "atta 5kg", "rice 5kg", "cooking oil 1 litre",
        "detergent powder", "tea powder 1kg",

        # Baby & Health
        "diapers", "baby wipes", "protein powder",

        # Utility
        "extension board", "wall clock", "bedsheet double"
    ]

    while True:
        print(f"\n🚀 {datetime.now().strftime('%H:%M')}")

        # Pick random 8 categories per cycle
        selected = random.sample(categories, 8)

        for query in selected:
            print(f"🔍 {query}")

            deals = get_amazon_deals(query)
            if deals:
                send_deals(deals)

        print("😴 Sleeping 5 minutes...\n")
        time.sleep(300)


# -----------------------------
# START
# -----------------------------
if __name__ == "__main__":
    print("🚀 Deals Bot Started")
    run_bot()
