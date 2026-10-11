import re
import json

CATEGORY_ASPECTS = {
    "Smartphone": ["camera", "battery", "performance", "display", "gaming", "price"],
    "Laptop": ["cpu", "gpu", "battery", "display", "build", "thermals", "price"],
    "Headphones": ["sound", "bass", "anc", "comfort", "battery", "mic", "price"],
    "Smartwatch": ["battery", "display", "fitness tracking", "build", "app ecosystem", "price"],
    "Camera": ["image quality", "autofocus", "low-light", "build", "video", "price"]
}

CATEGORY_KEYWORDS = {
    "Smartphone": ["phone", "smartphone", "mobile", "cell", "android", "iphone", "galaxy", "oneplus", "redmi", "realme", "pixel"],
    "Laptop": ["laptop", "notebook", "macbook", "ultrabook", "pc", "computer", "thinkpad"],
    "Headphones": ["headphone", "headphones", "earbuds", "earbud", "headset", "earphones", "earphone", "buds", "airpods", "earpods", "tws"],
    "Smartwatch": ["smartwatch", "smart watch", "watch", "fitness band", "band", "tracker", "wristband"],
    "Camera": ["camera", "dslr", "mirrorless", "cam", "digicam", "shooter"]
}

ASPECT_SYNONYMS = {
    "camera": ["camera", "cameras", "photo", "photos", "photography", "snaps", "portrait", "lens", "lenses", "optical", "selfie", "megapixels", "sensor"],
    "battery": ["battery", "battery life", "backup", "charging", "mah", "endurance", "long-lasting", "fast charging"],
    "performance": ["performance", "speed", "fast", "smooth", "multitasking", "ram", "processor", "snappy", "lag-free"],
    "display": ["display", "screen", "amoled", "oled", "120hz", "90hz", "refresh rate", "bright", "resolution", "hdr", "panel", "viewing"],
    "gaming": ["gaming", "games", "game", "gamer", "pubg", "bgmi", "cod", "fps", "framerate", "graphics", "gameplay"],
    "cpu": ["cpu", "processor", "intel", "amd", "ryzen", "i7", "i5", "i9", "m1", "m2", "m3", "core", "clock speed"],
    "gpu": ["gpu", "graphics", "rtx", "gtx", "radeon", "nvidia", "video card", "gaming", "rendering"],
    "thermals": ["thermals", "thermal", "cooling", "cool", "fans", "fan", "heat", "heating", "temperature", "airflow", "throttling"],
    "sound": ["sound", "audio", "sound quality", "clarity", "treble", "volume", "acoustics", "musical", "hi-res"],
    "bass": ["bass", "punchy bass", "deep bass", "low-end", "sub-bass", "thump", "heavy bass"],
    "anc": ["anc", "noise cancellation", "noise cancelling", "active noise cancellation", "isolation", "quiet"],
    "comfort": ["comfort", "comfortable", "ergonomics", "ergonomic", "lightweight", "fit", "ear tips", "cushion", "wearable"],
    "mic": ["mic", "microphone", "calling", "voice", "calls", "call clarity", "speak"],
    "fitness tracking": ["fitness", "fitness tracking", "steps", "heart rate", "spo2", "sleep", "tracking", "workouts", "running", "gps", "sensors", "health"],
    "app ecosystem": ["apps", "app ecosystem", "wearos", "watchos", "wear os", "notifications", "third-party", "ecosystem"],
    "image quality": ["image quality", "dynamic range", "sharpness", "colors", "raw", "resolution", "detail"],
    "autofocus": ["autofocus", "af", "eye tracking", "fast focus", "subject tracking", "quick focus", "focus"],
    "low-light": ["low-light", "low light", "night", "dark", "night mode", "iso", "low-light performance"],
    "video": ["video", "4k", "60fps", "120fps", "cinematic", "vlog", "vlogging", "stabilization", "gimbal", "recording"],
    "build": ["build", "build quality", "durability", "metal", "aluminum", "premium", "water resistant", "ip68", "rugged", "sturdy"],
    "price": ["price", "budget", "cheap", "affordable", "value for money", "vfm", "economical", "cost", "under", "below"]
}

HIGH_INTENSITY_MODIFIERS = [
    "excellent", "best", "superb", "top notch", "amazing", "great", "must have", 
    "priority", "heavy", "fantastic", "extreme", "pro", "flawless", "highest", "outstanding"
]

MEDIUM_INTENSITY_MODIFIERS = [
    "good", "decent", "nice", "solid", "reliable", "high", "better", "well"
]


def detect_category(query_text, explicit_category=None):
    """Detects category from query text or validates explicit category."""
    if explicit_category and explicit_category in CATEGORY_ASPECTS:
        return explicit_category

    text = query_text.lower()
    for cat, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            pattern = r'\b' + re.escape(kw) + r'\b'
            if re.search(pattern, text):
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
    aspects = CATEGORY_ASPECTS.get(category, CATEGORY_ASPECTS["Smartphone"])
    text = query_text.lower()

    # Raw scoring dict
    raw_weights = {a: 0.1 for a in aspects}

    # If budget is present or budget words mentioned, set a price weight baseline
    if budget is not None or any(w in text for w in ["under", "below", "budget", "cheap", "affordable", "price", "k"]):
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
        # adjust the largest weight
        max_aspect = max(normalized, key=normalized.get)
        normalized[max_aspect] = round(normalized[max_aspect] + diff, 2)

    return normalized


def parse_query(raw_query_text, explicit_category=None):
    """Full ChoiceAI extraction pipeline."""
    category = detect_category(raw_query_text, explicit_category)
    budget = extract_budget(raw_query_text)
    preference_weights = extract_preference_weights(raw_query_text, category, budget)

    return {
        "category": category,
        "budget": budget,
        "preference_weights": preference_weights,
        "aspect_set": CATEGORY_ASPECTS.get(category, [])
    }
