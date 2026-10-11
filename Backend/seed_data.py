import json
from werkzeug.security import generate_password_hash
from database import SessionLocal, init_db, engine
from models import Base, User, Query, Product, Review, AspectAggregate, Comparison, Explanation
from nlp.absa_engine import extract_aspect_sentiments, aggregate_product_aspect_scores
from nlp.preference_extraction import parse_query

def seed_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    print("Seeding Users...")
    user1 = User(
        user_id=101,
        full_name="Rahul Mehta",
        email="rahul.mehta@example.com",
        password_hash=generate_password_hash("rahul123")
    )
    user2 = User(
        user_id=102,
        full_name="Ananya Sharma",
        email="ananya.sharma@example.com",
        password_hash=generate_password_hash("ananya123")
    )
    db.add_all([user1, user2])
    db.commit()

    print("Seeding Multi-Category E-Commerce Products...")
    products_data = [
        # ==========================================
        # 1. SMARTPHONES
        # ==========================================
        {
            "product_id": 301,
            "category": "Smartphone",
            "name": "Phone B (Galaxy Neo 5G)",
            "brand": "Samsung",
            "price": 27999,
            "spec_scores_json": json.dumps({"camera": 0.92, "battery": 0.88, "gaming": 0.81, "performance": 0.85, "display": 0.89}),
            "image_url": "https://images.unsplash.com/photo-1610945265064-0e34e5519bbf?w=500&auto=format&fit=crop&q=60"
        },
        {
            "product_id": 302,
            "category": "Smartphone",
            "name": "OnePlus Nord Pro",
            "brand": "OnePlus",
            "price": 28999,
            "spec_scores_json": json.dumps({"camera": 0.84, "battery": 0.90, "gaming": 0.92, "performance": 0.91, "display": 0.88}),
            "image_url": "https://images.unsplash.com/photo-1598327105666-5b89351aff97?w=500&auto=format&fit=crop&q=60"
        },
        {
            "product_id": 303,
            "category": "Smartphone",
            "name": "Redmi Note Turbo",
            "brand": "Xiaomi",
            "price": 24999,
            "spec_scores_json": json.dumps({"camera": 0.80, "battery": 0.94, "gaming": 0.83, "performance": 0.82, "display": 0.85}),
            "image_url": "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=500&auto=format&fit=crop&q=60"
        },
        {
            "product_id": 304,
            "category": "Smartphone",
            "name": "Pixel 7a",
            "brand": "Google",
            "price": 37999,
            "spec_scores_json": json.dumps({"camera": 0.96, "battery": 0.75, "gaming": 0.78, "performance": 0.86, "display": 0.87}),
            "image_url": "https://images.unsplash.com/photo-1592899677977-9c10ca588bbd?w=500&auto=format&fit=crop&q=60"
        },

        # ==========================================
        # 2. LAPTOPS
        # ==========================================
        {
            "product_id": 305,
            "category": "Laptop",
            "name": "ROG Zephyrus G14",
            "brand": "ASUS",
            "price": 98999,
            "spec_scores_json": json.dumps({"cpu": 0.93, "gpu": 0.95, "battery": 0.76, "display": 0.92, "build": 0.89, "thermals": 0.82}),
            "image_url": "https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=500&auto=format&fit=crop&q=60"
        },
        {
            "product_id": 306,
            "category": "Laptop",
            "name": "MacBook Air M2",
            "brand": "Apple",
            "price": 89900,
            "spec_scores_json": json.dumps({"cpu": 0.91, "gpu": 0.82, "battery": 0.98, "display": 0.94, "build": 0.96, "thermals": 0.90}),
            "image_url": "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=500&auto=format&fit=crop&q=60"
        },
        {
            "product_id": 307,
            "category": "Laptop",
            "name": "Dell XPS 13 Plus",
            "brand": "Dell",
            "price": 104990,
            "spec_scores_json": json.dumps({"cpu": 0.88, "gpu": 0.78, "battery": 0.82, "display": 0.95, "build": 0.94, "thermals": 0.79}),
            "image_url": "https://images.unsplash.com/photo-1593642632823-8f785ba67e45?w=500&auto=format&fit=crop&q=60"
        },

        # ==========================================
        # 3. HEADPHONES & AUDIO
        # ==========================================
        {
            "product_id": 308,
            "category": "Headphones",
            "name": "WH-1000XM5",
            "brand": "Sony",
            "price": 26990,
            "spec_scores_json": json.dumps({"sound": 0.95, "bass": 0.92, "anc": 0.98, "comfort": 0.91, "battery": 0.92, "mic": 0.85}),
            "image_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500&auto=format&fit=crop&q=60"
        },
        {
            "product_id": 309,
            "category": "Headphones",
            "name": "QuietComfort 45",
            "brand": "Bose",
            "price": 24900,
            "spec_scores_json": json.dumps({"sound": 0.90, "bass": 0.84, "anc": 0.96, "comfort": 0.97, "battery": 0.86, "mic": 0.87}),
            "image_url": "https://images.unsplash.com/photo-1546435770-a3e426bf472b?w=500&auto=format&fit=crop&q=60"
        },
        {
            "product_id": 339,
            "category": "Headphones",
            "name": "Airdopes 141 Bluetooth TWS Earbuds",
            "brand": "boAt",
            "price": 999,
            "spec_scores_json": json.dumps({"sound": 0.88, "bass": 0.92, "anc": 0.70, "comfort": 0.87, "battery": 0.94, "mic": 0.84}),
            "image_url": "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=500&auto=format&fit=crop&q=60"
        },
        {
            "product_id": 340,
            "category": "Headphones",
            "name": "Z40 True Wireless Gaming Earbuds",
            "brand": "Boult",
            "price": 999,
            "spec_scores_json": json.dumps({"sound": 0.86, "bass": 0.90, "anc": 0.72, "comfort": 0.89, "battery": 0.95, "mic": 0.85}),
            "image_url": "https://images.unsplash.com/photo-1572536147248-ac59a8abfa4b?w=500&auto=format&fit=crop&q=60"
        },
        {
            "product_id": 341,
            "category": "Headphones",
            "name": "Buds VS102 Wireless Earbuds",
            "brand": "Noise",
            "price": 899,
            "spec_scores_json": json.dumps({"sound": 0.84, "bass": 0.86, "anc": 0.68, "comfort": 0.86, "battery": 0.91, "mic": 0.82}),
            "image_url": "https://images.unsplash.com/photo-1606220588913-b3aacb4d2f46?w=500&auto=format&fit=crop&q=60"
        },
        {
            "product_id": 342,
            "category": "Headphones",
            "name": "Buds T300 with 30dB ANC",
            "brand": "Realme",
            "price": 2199,
            "spec_scores_json": json.dumps({"sound": 0.91, "bass": 0.93, "anc": 0.88, "comfort": 0.90, "battery": 0.90, "mic": 0.86}),
            "image_url": "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=500&auto=format&fit=crop&q=60"
        },
        {
            "product_id": 343,
            "category": "Headphones",
            "name": "AirPods (3rd Generation)",
            "brand": "Apple",
            "price": 14900,
            "spec_scores_json": json.dumps({"sound": 0.94, "bass": 0.88, "anc": 0.85, "comfort": 0.95, "battery": 0.88, "mic": 0.92}),
            "image_url": "https://images.unsplash.com/photo-1600294037681-c80b4cb5b434?w=500&auto=format&fit=crop&q=60"
        },

        # ==========================================
        # 4. SMARTWATCHES
        # ==========================================
        {
            "product_id": 310,
            "category": "Smartwatch",
            "name": "Galaxy Watch 6",
            "brand": "Samsung",
            "price": 19999,
            "spec_scores_json": json.dumps({"battery": 0.80, "display": 0.94, "fitness tracking": 0.92, "build": 0.88, "app ecosystem": 0.90}),
            "image_url": "https://images.unsplash.com/photo-1508685096489-7aacd43bd3b1?w=500&auto=format&fit=crop&q=60"
        },
        {
            "product_id": 311,
            "category": "Smartwatch",
            "name": "Apple Watch Series 9",
            "brand": "Apple",
            "price": 38900,
            "spec_scores_json": json.dumps({"battery": 0.74, "display": 0.96, "fitness tracking": 0.96, "build": 0.95, "app ecosystem": 0.98}),
            "image_url": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=500&auto=format&fit=crop&q=60"
        },
        {
            "product_id": 335,
            "category": "Smartwatch",
            "name": "Limitless FS1 Pro Smartwatch",
            "brand": "Fastrack",
            "price": 1999,
            "spec_scores_json": json.dumps({"battery": 0.88, "display": 0.94, "fitness tracking": 0.89, "build": 0.86, "app ecosystem": 0.85}),
            "image_url": "https://images.unsplash.com/photo-1508685096489-7aacd43bd3b1?w=500&auto=format&fit=crop&q=60"
        },
        {
            "product_id": 336,
            "category": "Smartwatch",
            "name": "Reflex Play Plus Smartwatch",
            "brand": "Fastrack",
            "price": 2495,
            "spec_scores_json": json.dumps({"battery": 0.86, "display": 0.92, "fitness tracking": 0.90, "build": 0.88, "app ecosystem": 0.84}),
            "image_url": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=500&auto=format&fit=crop&q=60"
        },
        {
            "product_id": 337,
            "category": "Smartwatch",
            "name": "ColorFit Pulse 2 Max Smartwatch",
            "brand": "Noise",
            "price": 1499,
            "spec_scores_json": json.dumps({"battery": 0.90, "display": 0.88, "fitness tracking": 0.87, "build": 0.84, "app ecosystem": 0.82}),
            "image_url": "https://images.unsplash.com/photo-1508685096489-7aacd43bd3b1?w=500&auto=format&fit=crop&q=60"
        },
        {
            "product_id": 338,
            "category": "Smartwatch",
            "name": "Ninja Call Pro Plus Smartwatch",
            "brand": "Fire-Boltt",
            "price": 1299,
            "spec_scores_json": json.dumps({"battery": 0.85, "display": 0.87, "fitness tracking": 0.85, "build": 0.82, "app ecosystem": 0.80}),
            "image_url": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=500&auto=format&fit=crop&q=60"
        },

        # ==========================================
        # 5. CAMERAS
        # ==========================================
        {
            "product_id": 312,
            "category": "Camera",
            "name": "Alpha A7 IV",
            "brand": "Sony",
            "price": 198990,
            "spec_scores_json": json.dumps({"image quality": 0.97, "autofocus": 0.98, "low-light": 0.95, "build": 0.90, "video": 0.96}),
            "image_url": "https://images.unsplash.com/photo-1516035069371-29a1b244cc32?w=500&auto=format&fit=crop&q=60"
        },

        # ==========================================
        # 6. AIR CONDITIONERS (AC)
        # ==========================================
        {
            "product_id": 313,
            "category": "Air Conditioner",
            "name": "Voltas 1.4 Ton 3 Star Inverter Split AC",
            "brand": "Voltas",
            "price": 28990,
            "spec_scores_json": json.dumps({"cooling": 0.88, "energy efficiency": 0.78, "noise": 0.80, "durability": 0.89, "installation": 0.85}),
            "image_url": "images/ac_voltas.jpg"
        },
        {
            "product_id": 314,
            "category": "Air Conditioner",
            "name": "LG DUAL Inverter 1.5 Ton 5 Star Split AC",
            "brand": "LG",
            "price": 37490,
            "spec_scores_json": json.dumps({"cooling": 0.95, "energy efficiency": 0.96, "noise": 0.92, "durability": 0.91, "installation": 0.90}),
            "image_url": "images/ac_lg.jpg"
        },
        {
            "product_id": 315,
            "category": "Air Conditioner",
            "name": "Daikin 1.5 Ton 3 Star Inverter Split AC",
            "brand": "Daikin",
            "price": 32990,
            "spec_scores_json": json.dumps({"cooling": 0.92, "energy efficiency": 0.82, "noise": 0.89, "durability": 0.94, "installation": 0.87}),
            "image_url": "images/ac_daikin.jpg"
        },
        {
            "product_id": 316,
            "category": "Air Conditioner",
            "name": "Godrej 1 Ton 3 Star Inverter Split AC",
            "brand": "Godrej",
            "price": 22990,
            "spec_scores_json": json.dumps({"cooling": 0.82, "energy efficiency": 0.75, "noise": 0.78, "durability": 0.84, "installation": 0.80}),
            "image_url": "images/ac_godrej.jpg"
        },

        # ==========================================
        # 7. WASHING MACHINES
        # ==========================================
        {
            "product_id": 317,
            "category": "Washing Machine",
            "name": "Samsung 7 Kg Fully-Automatic Top Load",
            "brand": "Samsung",
            "price": 15990,
            "spec_scores_json": json.dumps({"wash quality": 0.86, "capacity": 0.82, "energy efficiency": 0.80, "spin speed": 0.81, "noise": 0.79}),
            "image_url": "https://images.unsplash.com/photo-1626806787426-5910811b6325?w=500&auto=format&fit=crop&q=60"
        },
        {
            "product_id": 318,
            "category": "Washing Machine",
            "name": "LG 8 Kg 5 Star AI Direct Drive Front Load",
            "brand": "LG",
            "price": 34990,
            "spec_scores_json": json.dumps({"wash quality": 0.96, "capacity": 0.92, "energy efficiency": 0.94, "spin speed": 0.95, "noise": 0.93}),
            "image_url": "https://images.unsplash.com/photo-1582735689369-4fe89db7114c?w=500&auto=format&fit=crop&q=60"
        },
        {
            "product_id": 319,
            "category": "Washing Machine",
            "name": "Bosch 7.5 Kg 5 Star Inverter Front Load",
            "brand": "Bosch",
            "price": 29990,
            "spec_scores_json": json.dumps({"wash quality": 0.94, "capacity": 0.88, "energy efficiency": 0.91, "spin speed": 0.90, "noise": 0.92}),
            "image_url": "https://images.unsplash.com/photo-1604335399105-a0c585fd81a1?w=500&auto=format&fit=crop&q=60"
        },
        {
            "product_id": 320,
            "category": "Washing Machine",
            "name": "Whirlpool 7.5 Kg 5 Star Semi-Automatic",
            "brand": "Whirlpool",
            "price": 10990,
            "spec_scores_json": json.dumps({"wash quality": 0.80, "capacity": 0.85, "energy efficiency": 0.84, "spin speed": 0.86, "noise": 0.72}),
            "image_url": "https://images.unsplash.com/photo-1626806787426-5910811b6325?w=500&auto=format&fit=crop&q=60"
        },

        # ==========================================
        # 8. REFRIGERATORS
        # ==========================================
        {
            "product_id": 321,
            "category": "Refrigerator",
            "name": "Samsung 253L 3 Star Inverter Double Door",
            "brand": "Samsung",
            "price": 24990,
            "spec_scores_json": json.dumps({"cooling": 0.90, "storage": 0.88, "energy efficiency": 0.85, "noise": 0.89, "build": 0.91}),
            "image_url": "https://images.unsplash.com/photo-1584992236310-6edddc08acff?w=500&auto=format&fit=crop&q=60"
        },
        {
            "product_id": 322,
            "category": "Refrigerator",
            "name": "LG 185L 5 Star Inverter Single Door",
            "brand": "LG",
            "price": 16990,
            "spec_scores_json": json.dumps({"cooling": 0.87, "storage": 0.78, "energy efficiency": 0.95, "noise": 0.91, "build": 0.88}),
            "image_url": "https://images.unsplash.com/photo-1571175443880-49e1d25b2bc5?w=500&auto=format&fit=crop&q=60"
        },

        # ==========================================
        # 9. TELEVISIONS (TV)
        # ==========================================
        {
            "product_id": 323,
            "category": "Television",
            "name": "Sony Bravia 55\" 4K Ultra HD Google TV",
            "brand": "Sony",
            "price": 54990,
            "spec_scores_json": json.dumps({"picture quality": 0.97, "sound": 0.92, "smart features": 0.95, "display": 0.96, "connectivity": 0.93}),
            "image_url": "https://images.unsplash.com/photo-1593359677879-a4bb92f829d1?w=500&auto=format&fit=crop&q=60"
        },
        {
            "product_id": 324,
            "category": "Television",
            "name": "Samsung Crystal Vision 43\" 4K UHD Smart TV",
            "brand": "Samsung",
            "price": 28990,
            "spec_scores_json": json.dumps({"picture quality": 0.89, "sound": 0.84, "smart features": 0.88, "display": 0.90, "connectivity": 0.87}),
            "image_url": "https://images.unsplash.com/photo-1577979749830-f1d742b96791?w=500&auto=format&fit=crop&q=60"
        },
        {
            "product_id": 325,
            "category": "Television",
            "name": "Xiaomi 43\" 4K Dolby Vision Smart TV",
            "brand": "Xiaomi",
            "price": 22999,
            "spec_scores_json": json.dumps({"picture quality": 0.85, "sound": 0.82, "smart features": 0.90, "display": 0.86, "connectivity": 0.85}),
            "image_url": "https://images.unsplash.com/photo-1593359677879-a4bb92f829d1?w=500&auto=format&fit=crop&q=60"
        },

        # ==========================================
        # 10. FOOTWEAR & SHOES
        # ==========================================
        {
            "product_id": 326,
            "category": "Footwear",
            "name": "Nike Air Zoom Pegasus 40 Running Shoes",
            "brand": "Nike",
            "price": 7995,
            "spec_scores_json": json.dumps({"comfort": 0.94, "durability": 0.90, "cushioning": 0.95, "grip": 0.91, "style": 0.93}),
            "image_url": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=500&auto=format&fit=crop&q=60"
        },
        {
            "product_id": 327,
            "category": "Footwear",
            "name": "Puma Velocity Nitro 2 Running Shoes",
            "brand": "Puma",
            "price": 4499,
            "spec_scores_json": json.dumps({"comfort": 0.90, "durability": 0.86, "cushioning": 0.89, "grip": 0.92, "style": 0.88}),
            "image_url": "https://images.unsplash.com/photo-1608231387042-66d1773070a5?w=500&auto=format&fit=crop&q=60"
        },
        {
            "product_id": 331,
            "category": "Footwear",
            "name": "Sparx Ultra Mesh Running Shoes",
            "brand": "Sparx",
            "price": 1299,
            "spec_scores_json": json.dumps({"comfort": 0.86, "durability": 0.92, "cushioning": 0.83, "grip": 0.88, "style": 0.82}),
            "image_url": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=500&auto=format&fit=crop&q=60"
        },
        {
            "product_id": 332,
            "category": "Footwear",
            "name": "Campus North High-Cushion Running Shoes",
            "brand": "Campus",
            "price": 1699,
            "spec_scores_json": json.dumps({"comfort": 0.89, "durability": 0.87, "cushioning": 0.91, "grip": 0.85, "style": 0.86}),
            "image_url": "https://images.unsplash.com/photo-1608231387042-66d1773070a5?w=500&auto=format&fit=crop&q=60"
        },
        {
            "product_id": 333,
            "category": "Footwear",
            "name": "Red Tape Athleisure Running Shoes",
            "brand": "Red Tape",
            "price": 2199,
            "spec_scores_json": json.dumps({"comfort": 0.92, "durability": 0.89, "cushioning": 0.88, "grip": 0.86, "style": 0.93}),
            "image_url": "https://images.unsplash.com/photo-1584735935682-2f2b69dff9d2?w=500&auto=format&fit=crop&q=60"
        },
        {
            "product_id": 334,
            "category": "Footwear",
            "name": "Asian Future-01 Sports Running Shoes",
            "brand": "Asian",
            "price": 899,
            "spec_scores_json": json.dumps({"comfort": 0.82, "durability": 0.85, "cushioning": 0.81, "grip": 0.84, "style": 0.80}),
            "image_url": "https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?w=500&auto=format&fit=crop&q=60"
        },

        # ==========================================
        # 11. KITCHEN APPLIANCES
        # ==========================================
        {
            "product_id": 328,
            "category": "Kitchen Appliance",
            "name": "Philips Digital Air Fryer 4.1L",
            "brand": "Philips",
            "price": 6499,
            "spec_scores_json": json.dumps({"performance": 0.93, "build quality": 0.91, "ease of cleaning": 0.94, "capacity": 0.85, "noise": 0.88}),
            "image_url": "https://images.unsplash.com/photo-1585659722983-3a675dabf23d?w=500&auto=format&fit=crop&q=60"
        },

        # ==========================================
        # 12. FURNITURE
        # ==========================================
        {
            "product_id": 329,
            "category": "Furniture",
            "name": "Green Soul Monster Ergonomic Chair",
            "brand": "Green Soul",
            "price": 16990,
            "spec_scores_json": json.dumps({"ergonomics": 0.95, "comfort": 0.94, "build quality": 0.92, "durability": 0.91, "material": 0.90}),
            "image_url": "images/chair_greensoul.jpg"
        },

        # ==========================================
        # 13. PERSONAL CARE
        # ==========================================
        {
            "product_id": 330,
            "category": "Personal Care",
            "name": "Philips Multigroom 7000 All-in-One Trimmer",
            "brand": "Philips",
            "price": 3499,
            "spec_scores_json": json.dumps({"performance": 0.94, "battery": 0.96, "waterproof": 0.95, "ergonomics": 0.90, "build quality": 0.92}),
            "image_url": "https://images.unsplash.com/photo-1621607512214-68297480165e?w=500&auto=format&fit=crop&q=60"
        }
    ]

    for p in products_data:
        prod = Product(**p)
        db.add(prod)
    db.commit()

    print("Seeding Reviews & Running Initial ABSA across all categories...")
    reviews_data = [
        # Smartphones
        {
            "review_id": 401,
            "product_id": 301,
            "review_text": "Camera is fantastic but battery drains quickly.",
            "rating": 4.0
        },
        {
            "review_id": 402,
            "product_id": 301,
            "review_text": "Photos in daylight are crisp and stunning. Gaming is smooth without fps drops.",
            "rating": 4.5
        },
        {
            "review_id": 403,
            "product_id": 301,
            "review_text": "Camera quality is amazing, portrait mode is super sharp. However battery life is mediocre.",
            "rating": 4.0
        },
        {
            "review_id": 404,
            "product_id": 302,
            "review_text": "Gaming performance is a beast with high fps. Battery backup lasts all day with fast charging.",
            "rating": 4.5
        },
        {
            "review_id": 405,
            "product_id": 302,
            "review_text": "Super fast processor and gaming. Camera is decent but low-light shots are a bit blurry.",
            "rating": 4.0
        },
        {
            "review_id": 406,
            "product_id": 303,
            "review_text": "Insane battery life lasting two days. Screen display is bright and clear.",
            "rating": 4.0
        },

        # Laptops & Headphones
        {
            "review_id": 407,
            "product_id": 305,
            "review_text": "GPU and CPU speed are top notch for heavy games. Cooling fans can get loud under load.",
            "rating": 4.5
        },
        {
            "review_id": 408,
            "product_id": 308,
            "review_text": "Active noise cancellation is superb and sound clarity is breathtaking. Deep punchy bass.",
            "rating": 5.0
        },

        # Air Conditioners
        {
            "review_id": 409,
            "product_id": 313,
            "review_text": "Chills the room super fast even in 45 degree heat. Sturdy copper condenser ensures durability.",
            "rating": 4.5
        },
        {
            "review_id": 410,
            "product_id": 314,
            "review_text": "Amazing 5-star power saving and whisper quiet cooling. Slashes electricity bill noticeably.",
            "rating": 5.0
        },
        {
            "review_id": 411,
            "product_id": 315,
            "review_text": "Daikin cooling capacity is solid and reliable. Quiet motor sound and fast setup.",
            "rating": 4.5
        },

        # Washing Machines
        {
            "review_id": 412,
            "product_id": 317,
            "review_text": "Great wash quality for daily clothes with low water consumption. Spin speed dries well.",
            "rating": 4.5
        },
        {
            "review_id": 413,
            "product_id": 318,
            "review_text": "Outstanding stain removal and 1400 rpm spin drying. Direct drive motor is whisper silent without vibration.",
            "rating": 5.0
        },
        {
            "review_id": 414,
            "product_id": 319,
            "review_text": "Stains vanish easily and fabric care is superb. EcoSilence motor has low noise.",
            "rating": 4.5
        },

        # Refrigerators
        {
            "review_id": 415,
            "product_id": 321,
            "review_text": "Frost free cooling retention is impressive. Generous storage compartments for vegetables and fruits.",
            "rating": 4.5
        },

        # Televisions
        {
            "review_id": 416,
            "product_id": 323,
            "review_text": "Picture quality is stunning with deep black levels and vibrant 4K HDR. Dolby Atmos sound is crystal clear.",
            "rating": 5.0
        },
        {
            "review_id": 417,
            "product_id": 324,
            "review_text": "PurColor display produces crisp picture. Smart Google TV apps run snappy.",
            "rating": 4.5
        },

        # Footwear
        {
            "review_id": 418,
            "product_id": 326,
            "review_text": "Incredible cushioning with Zoom Air bounce. Breathable mesh provides all day running comfort and strong grip.",
            "rating": 5.0
        },
        {
            "review_id": 420,
            "product_id": 331,
            "review_text": "Great durable shoes under 1500. Sturdy rubber grip and breathable mesh for running.",
            "rating": 4.5
        },
        {
            "review_id": 421,
            "product_id": 332,
            "review_text": "Super soft cushioning foam and very comfortable for long walks and daily jogging.",
            "rating": 4.5
        },
        {
            "review_id": 422,
            "product_id": 333,
            "review_text": "Premium memory foam cushioning and stylish looks. Excellent fit and comfortable all day.",
            "rating": 5.0
        },
        {
            "review_id": 423,
            "product_id": 334,
            "review_text": "Best budget athletic sports shoe under 1000 rupees. Lightweight and comfortable.",
            "rating": 4.0
        },
        {
            "review_id": 424,
            "product_id": 335,
            "review_text": "1.96 inch super AMOLED display is crystal clear. Battery lasts a full week and Bluetooth calling works reliably.",
            "rating": 5.0
        },
        {
            "review_id": 425,
            "product_id": 336,
            "review_text": "Fastrack Reflex build quality is super premium for the price. Steps and fitness tracking are accurate.",
            "rating": 4.5
        },
        {
            "review_id": 427,
            "product_id": 339,
            "review_text": "Punchy deep bass and 42 hours battery backup. Best wireless earbuds under 1000 rupees.",
            "rating": 5.0
        },
        {
            "review_id": 428,
            "product_id": 340,
            "review_text": "ENC calling mic is clear and crisp. Fast charging gives hours of playtime. Extremely comfortable in ear fit.",
            "rating": 4.5
        },
        {
            "review_id": 429,
            "product_id": 341,
            "review_text": "Unbeatable budget TWS earbuds under 1k. Clear sound quality and lightweight compact case.",
            "rating": 4.0
        },
        {
            "review_id": 430,
            "product_id": 343,
            "review_text": "Spatial audio and crystal clear calling microphone. Seamless Apple ecosystem integration and great comfort.",
            "rating": 5.0
        },

        # Kitchen Appliance
        {
            "review_id": 419,
            "product_id": 328,
            "review_text": "Air frying performance is crispy and delicious with 90% less oil. Basket is non-stick and easy to clean.",
            "rating": 5.0
        }
    ]

    for r_data in reviews_data:
        prod = db.query(Product).filter_by(product_id=r_data["product_id"]).first()
        cat = prod.category if prod else "Smartphone"
        aspect_sentiments = extract_aspect_sentiments(r_data["review_text"], cat)

        rev = Review(
            review_id=r_data["review_id"],
            product_id=r_data["product_id"],
            review_text=r_data["review_text"],
            rating=r_data["rating"],
            aspect_sentiments_json=json.dumps(aspect_sentiments)
        )
        db.add(rev)
    db.commit()

    print("Computing and caching Aspect Aggregates...")
    all_products = db.query(Product).all()
    for prod in all_products:
        prod_reviews = db.query(Review).filter_by(product_id=prod.product_id).all()
        agg_scores = aggregate_product_aspect_scores(prod_reviews, prod.category, prod.get_spec_scores())

        agg = AspectAggregate(
            product_id_agg=prod.product_id,
            aspect_scores_json=json.dumps(agg_scores)
        )
        db.add(agg)
    db.commit()

    print("Seeding Sample Query 201 (SRS Test Query)...")
    sample_query_text = "I need a phone under 30k with excellent camera, battery and gaming."
    parsed = parse_query(sample_query_text)
    sample_q = Query(
        query_id=201,
        user_id=101,
        raw_query_text=sample_query_text,
        category="Smartphone",
        budget=30000,
        preference_weights_json=json.dumps(parsed["preference_weights"])
    )
    db.add(sample_q)
    db.commit()

    print("Seeding Complete! Database ready with multi-category e-commerce catalog.")
    db.close()

if __name__ == "__main__":
    seed_database()
