import requests
from bs4 import BeautifulSoup
import os
import random
import asyncio
import time
from datetime import datetime
from telegram import Bot
import cloudscraper # ⬅️ This was the missing line causing the error!

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
# AMAZON SCRAPER (CLOUDSCRAPER UPGRADE)
# -----------------------------
def get_amazon_deals(query):
    url = f"https://www.amazon.in/s?k={query.replace(' ', '+')}&tag={AMAZON_TAG}"

    try:
        # Random sleep to mimic human behavior
        time.sleep(random.uniform(3, 6))  
        
        # Use cloudscraper instead of basic requests to bypass CAPTCHAs
        scraper = cloudscraper.create_scraper(
            browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
        )
        
        res = scraper.get(url, timeout=20)
        
        # If Amazon throws a 503 Service Unavailable, it means they served a CAPTCHA
        if res.status_code != 200:
            print(f"⚠️ Amazon Blocked Request! Status Code: {res.status_code}")
            return []

        soup = BeautifulSoup(res.text, "html.parser")

        products = soup.find_all("div", {"data-component-type": "s-search-result"})[:3]
        
        if not products:
            print(f"⚠️ Page loaded, but 0 products found. Layout might have changed.")
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
        # 🔥 Electronics (High Earnings)
        "smartphones under 20000", "smartphones under 15000",
        "gaming laptops under 60000", "laptop under 50000",
        "wireless earbuds anc", "bluetooth earphones under 1000",
        "smartwatch under 2000", "smartwatch under 3000",
        "gaming mouse rgb", "mechanical keyboard wireless",
        "monitor 24 inch ips", "tablet under 20000",
        "power bank 10000mah fast charging", "power bank 20000mah",
        "usb c hub multiport adapter", "wifi router dual band",
        "bluetooth speaker under 1000", "trimmer for men",

        # 🏠 Home & Kitchen (Very High Conversion)
        "mixer grinder 750w", "pressure cooker 5 litre",
        "induction cooktop 2000w", "electric kettle 1.5 litre",
        "air fryer under 5000", "gas stove 2 burner",
        "water purifier ro uv", "chimney kitchen auto clean",
        "non stick cookware set", "dinner set 24 pieces",
        "water bottle steel 1 litre", "tiffin box for office",
        "vegetable chopper manual", "storage containers kitchen",

        # 👕 Fashion (Fast Sales)
        "tshirt men pack of 3", "shirts for men cotton",
        "jeans for men slim fit", "kurti for women cotton",
        "saree under 1000", "leggings combo pack",
        "shoes for men running", "slippers for women",
        "socks pack of 5", "wallet for men leather",
        "backpack for college", "travel bag duffle",

        # 💄 Beauty & Personal Care
        "face wash men", "face wash women",
        "shampoo 650ml", "hair oil 200ml",
        "body lotion 500ml", "trimmer women",
        "perfume for men", "deodorant combo",
        "face serum vitamin c", "sunscreen spf 50",

        # 🛒 Grocery (REPEAT BUY = 💰 GOLD)
        "atta 5kg", "rice 5kg", "basmati rice 5kg",
        "cooking oil 1 litre", "sunflower oil 5 litre",
        "detergent powder 4kg", "toothpaste combo pack",
        "biscuits combo pack", "tea powder 1kg",
        "coffee powder 500g", "dry fruits combo",
        "honey 1kg", "ghee 1 litre",

        # 👶 Baby & Health
        "diapers large pack", "baby wipes",
        "protein powder 1kg", "multivitamin tablets",
        "digital thermometer", "bp monitor machine",
        "weighing machine digital", "massager for pain relief",

        # 💼 Office & Study
        "office chair ergonomic", "study table folding",
        "laptop stand adjustable", "keyboard mouse combo",
        "desk organizer", "whiteboard for home",
        "notebooks pack", "gel pens pack",

        # 🏋️ Fitness & Sports
        "yoga mat 8mm", "dumbbells set 10kg",
        "resistance bands heavy", "skipping rope",
        "protein powder whey", "gym gloves",
        "cycling helmet", "badminton racket",

        # 🔌 Daily Utility (Hidden Gems 💰)
        "extension board", "led bulb 9w pack",
        "emergency light rechargeable", "torch led",
        "wall clock modern", "bedsheet double",
        "blanket winter", "curtains for home",
        "umbrella folding", "door mat",

        # 🔥 TRENDING / IMPULSE BUYS (VERY IMPORTANT)
        "mini cooler portable", "handheld vacuum cleaner",
        "portable juicer blender", "car phone holder",
        "mobile stand adjustable", "ring light for mobile",
        "tripod stand for phone", "selfie stick bluetooth",
        "gaming headset under 2000", "led strip lights"
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
