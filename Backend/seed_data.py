import json
from werkzeug.security import generate_password_hash
from database import SessionLocal, init_db
from models import User, Query, Product, Review, AspectAggregate, Comparison, Explanation
from nlp.absa_engine import extract_aspect_sentiments, aggregate_product_aspect_scores
from nlp.preference_extraction import parse_query

def seed_database():
    init_db()
    db = SessionLocal()

    # Clear existing data
    db.query(Explanation).delete()
    db.query(Comparison).delete()
    db.query(AspectAggregate).delete()
    db.query(Review).delete()
    db.query(Product).delete()
    db.query(Query).delete()
    db.query(User).delete()
    db.commit()

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

    print("Seeding Products...")
    products_data = [
        # Smartphones
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

        # Laptops
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

        # Headphones
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

        # Smartwatches
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

        # Cameras
        {
            "product_id": 312,
            "category": "Camera",
            "name": "Alpha A7 IV",
            "brand": "Sony",
            "price": 198990,
            "spec_scores_json": json.dumps({"image quality": 0.97, "autofocus": 0.98, "low-light": 0.95, "build": 0.90, "video": 0.96}),
            "image_url": "https://images.unsplash.com/photo-1516035069371-29a1b244cc32?w=500&auto=format&fit=crop&q=60"
        }
    ]

    for p in products_data:
        prod = Product(**p)
        db.add(prod)
    db.commit()

    print("Seeding Reviews & Running Initial ABSA...")
    reviews_data = [
        # Product 301 (Phone B) - Matches Sample in SRS
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
        # Product 302 (OnePlus)
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
        # Product 303 (Redmi)
        {
            "review_id": 406,
            "product_id": 303,
            "review_text": "Insane battery life lasting two days. Screen display is bright and clear.",
            "rating": 4.0
        },
        # Product 305 (ROG Laptop)
        {
            "review_id": 407,
            "product_id": 305,
            "review_text": "GPU and CPU speed are top notch for heavy games. Cooling fans can get loud under load.",
            "rating": 4.5
        },
        # Product 308 (Sony XM5)
        {
            "review_id": 408,
            "product_id": 308,
            "review_text": "Active noise cancellation is superb and sound clarity is breathtaking. Deep punchy bass.",
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
    
    # Matching exact sample weights in SRS Section 9
    sample_weights = {
        "camera": 0.40,
        "battery": 0.30,
        "gaming": 0.20,
        "price": 0.10
    }

    q201 = Query(
        query_id=201,
        user_id=101,
        raw_query_text=sample_query_text,
        category="Smartphone",
        budget=30000.0,
        preference_weights_json=json.dumps(sample_weights)
    )
    db.add(q201)
    db.commit()

    print("Database seeding completed successfully!")
    db.close()

if __name__ == '__main__':
    seed_database()
