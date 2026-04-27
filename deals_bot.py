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
# GLOBAL SCRAPER
# -----------------------------
scraper = cloudscraper.create_scraper()

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/120 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15"
]

# -----------------------------
# AMAZON SCRAPER (RETRY + SAFE)
# -----------------------------
def get_amazon_deals(query):
    url = f"https://www.amazon.in/s?k={query.replace(' ', '+')}&tag={AMAZON_TAG}"

    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "en-IN,en;q=0.9",
        "Connection": "keep-alive"
    }

    try:
        # Human-like delay
        time.sleep(random.uniform(6, 12))

        res = None

        # 🔁 Retry logic
        for attempt in range(2):
            res = scraper.get(url, headers=headers, timeout=20)

            if res.status_code == 200:
                break
            else:
                print(f"⚠️ Blocked ({res.status_code}) → retry {attempt+1}")
                time.sleep(random.uniform(5, 10))

        # ❌ Still blocked
        if not res or res.status_code != 200:
            print("❌ Skipping blocked query")
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
        # (KEEPING ALL YOUR CATEGORIES SAME)
        "smartphones under 20000","smartphones under 15000",
        "gaming laptops under 60000","laptop under 50000",
        "wireless earbuds anc","bluetooth earphones under 1000",
        "smartwatch under 2000","smartwatch under 3000",
        "gaming mouse rgb","mechanical keyboard wireless",
        "monitor 24 inch ips","tablet under 20000",
        "power bank 10000mah fast charging","power bank 20000mah",
        "usb c hub multiport adapter","wifi router dual band",
        "bluetooth speaker under 1000","trimmer for men",

        "mixer grinder 750w","pressure cooker 5 litre",
        "induction cooktop 2000w","electric kettle 1.5 litre",
        "air fryer under 5000","gas stove 2 burner",
        "water purifier ro uv","chimney kitchen auto clean",
        "non stick cookware set","dinner set 24 pieces",

        "tshirt men pack of 3","shirts for men cotton",
        "jeans for men slim fit","kurti for women cotton",
        "saree under 1000","leggings combo pack",

        "face wash men","shampoo 650ml","hair oil 200ml",
        "perfume for men","deodorant combo",

        "atta 5kg","rice 5kg","tea powder 1kg",
        "coffee powder 500g","dry fruits combo",

        "diapers large pack","baby wipes","protein powder 1kg",

        "office chair ergonomic","study table folding",
        "laptop stand adjustable","keyboard mouse combo",

        "yoga mat 8mm","dumbbells set 10kg",
        "resistance bands heavy","skipping rope",

        "extension board","wall clock modern",
        "bedsheet double","blanket winter",

        "mini cooler portable","handheld vacuum cleaner",
        "portable juicer blender","mobile stand adjustable",
        "tripod stand for phone","gaming headset under 2000"
    ]

    while True:
        print(f"\n🚀 {datetime.now().strftime('%H:%M')}")

        # Keep categories, reduce frequency
        selected = random.sample(categories, 2)

        for query in selected:
            print(f"🔍 {query}")

            deals = get_amazon_deals(query)
            if deals:
                await send_deals(deals)

            # 👇 extra delay between queries
            await asyncio.sleep(random.uniform(10, 20))

        print("😴 Sleeping 10 minutes...\n")
        await asyncio.sleep(600)

# -----------------------------
# START
# -----------------------------
if __name__ == "__main__":
    print("🚀 Deals Bot Started")
    asyncio.run(run_bot())
