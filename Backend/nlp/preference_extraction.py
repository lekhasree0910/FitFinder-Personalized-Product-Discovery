import re
import json

CATEGORY_ASPECTS = {
    # Electronics & Computing
    "Smartphone": ["camera", "battery", "performance", "display", "gaming", "price"],
    "Laptop": ["cpu", "gpu", "battery", "display", "build", "thermals", "price"],
    "Headphones": ["sound", "bass", "anc", "comfort", "battery", "mic", "price"],
    "Smartwatch": ["battery", "display", "fitness tracking", "build", "app ecosystem", "price"],
    "Camera": ["image quality", "autofocus", "low-light", "build", "video", "price"],
    "Tablet": ["display", "battery", "performance", "stylus", "portability", "price"],

    # Major Home Appliances
    "Air Conditioner": ["cooling", "energy efficiency", "noise", "durability", "installation", "price"],
    "Washing Machine": ["wash quality", "capacity", "energy efficiency", "spin speed", "noise", "price"],
    "Refrigerator": ["cooling", "storage", "energy efficiency", "noise", "build", "price"],
    "Television": ["picture quality", "sound", "smart features", "display", "connectivity", "price"],

    # Kitchen & Living
    "Kitchen Appliance": ["performance", "build quality", "ease of cleaning", "capacity", "noise", "price"],
    "Furniture": ["ergonomics", "comfort", "build quality", "durability", "material", "price"],

    # Fashion, Footwear & Personal Care
    "Footwear": ["comfort", "durability", "cushioning", "grip", "style", "price"],
    "Personal Care": ["performance", "battery", "waterproof", "ergonomics", "build quality", "price"],

    # Universal / Dynamic Fallback
    "General Product": ["quality", "performance", "durability", "design", "ease of use", "price"]
}

CATEGORY_KEYWORDS = {
    "Air Conditioner": ["ac", "air conditioner", "split ac", "inverter ac", "window ac", "cooling ac", "ton ac"],
    "Washing Machine": ["washing machine", "washer", "front load", "top load", "clothes washer", "laundry machine", "wash machine"],
    "Refrigerator": ["refrigerator", "fridge", "double door", "single door", "frost free", "deep freezer", "mini fridge"],
    "Television": ["television", "tv", "smart tv", "led tv", "oled", "qled", "4k tv", "android tv", "google tv"],
    "Smartphone": ["phone", "smartphone", "mobile", "cell", "android", "iphone", "galaxy", "oneplus", "redmi", "realme", "pixel"],
    "Laptop": ["laptop", "notebook", "macbook", "ultrabook", "pc", "computer", "thinkpad"],
    "Headphones": ["headphone", "headphones", "earbuds", "earbud", "headset", "earphones", "earphone", "buds", "airpods", "earpods", "tws"],
    "Smartwatch": ["smartwatch", "smart watch", "watch", "fitness band", "band", "tracker", "wristband"],
    "Camera": ["camera", "dslr", "mirrorless", "cam", "digicam", "shooter"],
    "Tablet": ["tablet", "ipad", "tab"],
    "Kitchen Appliance": ["air fryer", "mixer grinder", "blender", "toaster", "coffee maker", "kettle", "microwave", "oven", "juicer", "food processor", "cooker", "induction", "chimney"],
    "Furniture": ["chair", "office chair", "gaming chair", "desk", "table", "sofa", "bed", "mattress", "furniture"],
    "Footwear": ["shoes", "shoe", "sneakers", "sneaker", "running shoes", "sports shoes", "boots", "sandals", "slippers", "loafers", "footwear"],
    "Personal Care": ["trimmer", "shaver", "hair dryer", "electric toothbrush", "straightener", "grooming"]
}

ASPECT_SYNONYMS = {
    # Electronics
    "camera": ["camera", "cameras", "photo", "photos", "photography", "snaps", "portrait", "lens", "lenses", "optical", "selfie", "megapixels", "sensor"],
    "battery": ["battery", "battery life", "backup", "charging", "mah", "endurance", "long-lasting", "fast charging", "runtime"],
    "performance": ["performance", "speed", "fast", "smooth", "multitasking", "ram", "processor", "snappy", "lag-free", "power"],
    "display": ["display", "screen", "amoled", "oled", "120hz", "90hz", "refresh rate", "bright", "resolution", "hdr", "panel", "viewing"],
    "gaming": ["gaming", "games", "game", "gamer", "pubg", "bgmi", "cod", "fps", "framerate", "graphics", "gameplay"],
    "cpu": ["cpu", "processor", "intel", "amd", "ryzen", "i7", "i5", "i9", "m1", "m2", "m3", "core", "clock speed"],
    "gpu": ["gpu", "graphics", "rtx", "gtx", "radeon", "nvidia", "video card", "gaming", "rendering"],
    "thermals": ["thermals", "thermal", "cooling", "cool", "fans", "fan", "heat", "heating", "temperature", "airflow", "throttling"],
    "sound": ["sound", "audio", "sound quality", "clarity", "treble", "volume", "acoustics", "musical", "hi-res", "speakers", "dolby"],
    "bass": ["bass", "punchy bass", "deep bass", "low-end", "sub-bass", "thump", "heavy bass"],
    "anc": ["anc", "noise cancellation", "noise cancelling", "active noise cancellation", "isolation", "quiet"],
    "comfort": ["comfort", "comfortable", "ergonomics", "ergonomic", "lightweight", "fit", "ear tips", "cushion", "wearable", "padding"],
    "mic": ["mic", "microphone", "calling", "voice", "calls", "call clarity", "speak"],
    "fitness tracking": ["fitness", "fitness tracking", "steps", "heart rate", "spo2", "sleep", "tracking", "workouts", "running", "gps", "sensors", "health"],
    "app ecosystem": ["apps", "app ecosystem", "wearos", "watchos", "wear os", "notifications", "third-party", "ecosystem"],
    "image quality": ["image quality", "dynamic range", "sharpness", "colors", "raw", "resolution", "detail"],
    "autofocus": ["autofocus", "af", "eye tracking", "fast focus", "subject tracking", "quick focus", "focus"],
    "low-light": ["low-light", "low light", "night", "dark", "night mode", "iso", "low-light performance"],
    "video": ["video", "4k", "60fps", "120fps", "cinematic", "vlog", "vlogging", "stabilization", "gimbal", "recording"],
    "build": ["build", "build quality", "durability", "metal", "aluminum", "premium", "water resistant", "ip68", "rugged", "sturdy"],
    "stylus": ["stylus", "pencil", "pen", "s-pen", "drawing", "writing", "palm rejection"],
    "portability": ["portability", "lightweight", "slim", "thin", "portable", "travel friendly", "compact"],

    # Appliances - AC & Fridge & Microwave
    "cooling": ["cooling", "cool", "chill", "chills", "fast cooling", "turbo cooling", "cooling capacity", "airflow", "tonnage", "ice making", "freshness", "frost free"],
    "energy efficiency": ["energy efficiency", "energy efficient", "power saving", "power consumption", "electricity bill", "5 star", "4 star", "3 star", "star rating", "inverter", "iseer", "eco mode", "energy saver"],
    "noise": ["noise", "silent", "quiet", "decibel", "db", "whisper", "sound", "humming", "vibration", "noiseless", "low noise"],
    "durability": ["durability", "durable", "copper condenser", "copper coil", "rust", "build", "sturdy", "reliable", "compressor", "lifespan", "long-lasting"],
    "installation": ["installation", "setup", "service", "mounting", "technician", "warranty", "after-sales"],

    # Appliances - Washing Machine
    "wash quality": ["wash quality", "washing", "cleaning", "wash", "stain removal", "tangle", "gentle", "wash cycles", "pulsator", "agitator", "drum", "rinse", "dirt removal"],
    "capacity": ["capacity", "kg", "7kg", "8kg", "6kg", "9kg", "litres", "liters", "load", "drum size", "volume", "family size", "storage space"],
    "spin speed": ["spin speed", "drying", "rpm", "spin", "dryer", "dry", "spin cycle", "quick wash", "1200 rpm", "1400 rpm"],

    # Appliances - Refrigerator
    "storage": ["storage", "capacity", "litres", "liters", "shelves", "veg box", "crisper", "space", "door racks", "compartments", "freezer"],

    # Television
    "picture quality": ["picture quality", "picture", "clarity", "contrast", "hdr", "dolby vision", "black levels", "vibrant", "colors", "sharpness", "uhd"],
    "smart features": ["smart features", "smart tv", "os", "google tv", "android tv", "apps", "netflix", "youtube", "voice remote", "assistant", "ui", "chromecast"],
    "connectivity": ["connectivity", "hdmi", "usb", "bluetooth", "wifi", "ports", "e-arc", "optical"],

    # Footwear & Fashion
    "cushioning": ["cushioning", "cushion", "bounce", "foam", "midsole", "shock absorption", "soft", "responsive", "zoom", "boost", "comfort sole"],
    "grip": ["grip", "traction", "outsole", "rubber", "slip resistant", "anti-skid", "tread", "sole grip"],
    "style": ["style", "stylish", "looks", "look", "design", "appearance", "aesthetic", "colors", "fashionable", "modern"],

    # Kitchen & Furniture
    "build quality": ["build quality", "build", "sturdy", "stainless steel", "jars", "durability", "material", "finish", "solid", "frame"],
    "ease of cleaning": ["ease of cleaning", "cleaning", "washable", "dishwasher safe", "non-stick", "maintenance", "clean", "easy to clean"],
    "ergonomics": ["ergonomics", "ergonomic", "lumbar support", "posture", "adjustable", "headrest", "armrest", "recline", "sitting comfort"],
    "material": ["material", "mesh", "leather", "fabric", "wood", "metal", "cushioning", "finish"],

    # Personal Care
    "waterproof": ["waterproof", "ipx7", "washable", "shower", "water resistant"],

    # General / Universal
    "quality": ["quality", "premium", "reliable", "materials", "overall quality"],
    "design": ["design", "compact", "portable", "aesthetic", "sleek"],
    "ease of use": ["ease of use", "simple", "convenient", "easy to use", "user friendly", "setup"],

    # Universal Price
    "price": ["price", "budget", "cheap", "affordable", "value for money", "vfm", "economical", "cost", "under", "below", "worth"]
}

HIGH_INTENSITY_MODIFIERS = [
    "excellent", "best", "superb", "top notch", "amazing", "great", "must have", 
    "priority", "heavy", "fantastic", "extreme", "pro", "flawless", "highest", "outstanding",
    "whisper", "silent", "5 star", "dual inverter", "super"
]

MEDIUM_INTENSITY_MODIFIERS = [
    "good", "decent", "nice", "solid", "reliable", "high", "better", "well", "efficient"
]


def detect_category(query_text, explicit_category=None):
    """
    Intelligently detects product category from query text or explicit category.
    Priority 1: Category explicitly matched in the free-text prompt (e.g. 'AC' -> 'Air Conditioner').
    Priority 2: If no category detected in query text, use explicit_category (if provided and valid).
    Priority 3: Dynamic entity extraction or fallback to Smartphone.
    """
    text = query_text.lower().strip()

    # Priority order: Check primary host categories first so features like 'camera' or 'sound'
    # don't override the primary product (e.g. 'phone with good camera' is a Smartphone, not a Camera).
    CATEGORY_PRIORITY_ORDER = [
        "Air Conditioner",
        "Washing Machine",
        "Refrigerator",
        "Television",
        "Smartphone",
        "Laptop",
        "Tablet",
        "Footwear",
        "Kitchen Appliance",
        "Furniture",
        "Personal Care",
        "Headphones",
        "Smartwatch",
        "Camera"
    ]

    for cat in CATEGORY_PRIORITY_ORDER:
        keywords = CATEGORY_KEYWORDS.get(cat, [])
        # Check longer phrases first
        sorted_kw = sorted(keywords, key=lambda k: -len(k))
        for kw in sorted_kw:
            pattern = r'\b' + re.escape(kw) + r'\b'
            if re.search(pattern, text):
                return cat

    # 2. If no category keywords in text, use explicit_category if specified
    if explicit_category and explicit_category in CATEGORY_ASPECTS and explicit_category not in ["All", "Auto", "All Categories"]:
        return explicit_category

    # 3. Dynamic product extraction heuristic (e.g., "i want a/an [product]")
    m = re.search(r'\b(?:want|need|looking for|buy|recommend|suggest)\s+(?:an?|the|some)?\s+([a-zA-Z\s]{2,25}?)(?:\s+(?:under|in|below|with|for|around|\d+|$))', text)
    if m:
        candidate_noun = m.group(1).strip().title()
        if candidate_noun and len(candidate_noun) > 2 and candidate_noun.lower() not in ["good", "best", "new", "cheap", "product"]:
            for cat in CATEGORY_ASPECTS:
                if cat.lower() in candidate_noun.lower() or candidate_noun.lower() in cat.lower():
                    return cat

    return "Smartphone"


def extract_budget(query_text):
    """Extracts budget value from user query text."""
    text = query_text.lower().replace(',', '')

    patterns = [
        r'(?:under|below|less than|within|around|upto|up to|budget of|max|in)\s*(?:rs\.?|inr|₹)?\s*(\d+(?:\.\d+)?)\s*(k|lakh|thousand)?\b',
        r'(?:rs\.?|inr|₹)\s*(\d+(?:\.\d+)?)\s*(k|lakh|thousand)?\b',
        r'<\s*(\d+(?:\.\d+)?)\s*(k|lakh|thousand)?\b',
        r'(\d+(?:\.\d+)?)\s*k\b'
    ]

    for pat in patterns:
        match = re.search(pat, text)
        if match:
            num = float(match.group(1))
            unit = match.group(2) if len(match.groups()) > 1 else None
            if unit:
                unit = unit.lower()
                if unit == 'k' or unit == 'thousand':
                    num *= 1000
                elif unit == 'lakh':
                    num *= 100000
            elif num < 500:
                num *= 1000
            return float(num)

    return None


def extract_preference_weights(query_text, category="Smartphone", budget=None):
    """
    Extracts per-aspect importance weights from free-text query.
    Weights sum to 1.00 exactly across the category's aspect set.
    """
    aspects = CATEGORY_ASPECTS.get(category, CATEGORY_ASPECTS.get("General Product", ["quality", "price"]))
    text = query_text.lower()

    # Raw scoring dict
    raw_weights = {a: 0.1 for a in aspects}

    # If budget is present or budget words mentioned, set a price weight baseline
    if budget is not None or any(w in text for w in ["under", "below", "budget", "cheap", "affordable", "price", "k", "inr", "rs"]):
        raw_weights["price"] = 0.5

    for aspect in aspects:
        if aspect == "price":
            continue
        synonyms = ASPECT_SYNONYMS.get(aspect, [aspect])
        for syn in synonyms:
            pattern = r'\b' + re.escape(syn) + r'\b'
            match = re.search(pattern, text)
            if match:
                # Base mention weight
                weight = 1.0

                # Check proximity for intensity modifiers
                start_pos = max(0, match.start() - 25)
                end_pos = min(len(text), match.end() + 25)
                context = text[start_pos:end_pos]

                if any(m in context for m in HIGH_INTENSITY_MODIFIERS):
                    weight = 2.5
                elif any(m in context for m in MEDIUM_INTENSITY_MODIFIERS):
                    weight = 1.8

                if weight > raw_weights[aspect]:
                    raw_weights[aspect] = weight

    # Normalize weights so they sum to 1.00
    total = sum(raw_weights.values())
    normalized = {}
    for a, w in raw_weights.items():
        normalized[a] = round(w / total, 2)

    # Adjust rounding discrepancy to guarantee exactly 1.00
    diff = round(1.0 - sum(normalized.values()), 2)
    if diff != 0:
        max_aspect = max(normalized, key=normalized.get)
        normalized[max_aspect] = round(normalized[max_aspect] + diff, 2)

    return normalized


KNOWN_BRANDS = {
    # Watches & Smartwatches
    "fastrack": "Fastrack",
    "titan": "Titan",
    "noise": "Noise",
    "fire-boltt": "Fire-Boltt",
    "fireboltt": "Fire-Boltt",
    "boat": "boAt",
    "boult": "Boult",
    "zebronics": "Zebronics",
    "fossil": "Fossil",
    "amazfit": "Amazfit",
    # Phones & Tech
    "apple": "Apple",
    "samsung": "Samsung",
    "oneplus": "OnePlus",
    "google": "Google",
    "pixel": "Google",
    "xiaomi": "Xiaomi",
    "redmi": "Xiaomi",
    "realme": "Realme",
    "motorola": "Motorola",
    "moto": "Motorola",
    "oppo": "Oppo",
    "vivo": "Vivo",
    "nothing": "Nothing",
    "asus": "ASUS",
    "dell": "Dell",
    "lenovo": "Lenovo",
    "hp": "HP",
    "acer": "Acer",
    # Audio
    "sony": "Sony",
    "bose": "Bose",
    "sennheiser": "Sennheiser",
    "jbl": "JBL",
    # Appliances
    "lg": "LG",
    "daikin": "Daikin",
    "voltas": "Voltas",
    "godrej": "Godrej",
    "bosch": "Bosch",
    "whirlpool": "Whirlpool",
    "ifb": "IFB",
    # Footwear
    "nike": "Nike",
    "puma": "Puma",
    "adidas": "Adidas",
    "sparx": "Sparx",
    "campus": "Campus",
    "red tape": "Red Tape",
    "redtape": "Red Tape",
    "asian": "Asian",
    # Kitchen & Grooming
    "philips": "Philips",
    "sujata": "Sujata",
    "dyson": "Dyson",
    "green soul": "Green Soul"
}


def extract_brand(query_text):
    """Extracts known brand entity from query text."""
    text = query_text.lower()
    # Avoid false positive where 'noise cancellation' or 'noise cancelling' triggers the brand 'Noise'
    text_for_brand = re.sub(r'\bnoise\s+cancell(?:ation|ing)\b', '', text)
    # Also avoid 'apple' when preceded by 'pineapple' etc. (handled by word boundary)

    sorted_brands = sorted(KNOWN_BRANDS.keys(), key=lambda b: -len(b))
    for b in sorted_brands:
        pattern = r'\b' + re.escape(b) + r'\b'
        if re.search(pattern, text_for_brand):
            return KNOWN_BRANDS[b]
    return None


def parse_query(raw_query_text, explicit_category=None):
    """Full ChoiceAI extraction pipeline."""
    category = detect_category(raw_query_text, explicit_category)
    brand = extract_brand(raw_query_text)
    budget = extract_budget(raw_query_text)
    preference_weights = extract_preference_weights(raw_query_text, category, budget)

    return {
        "category": category,
        "brand": brand,
        "budget": budget,
        "preference_weights": preference_weights,
        "aspect_set": CATEGORY_ASPECTS.get(category, [])
    }
