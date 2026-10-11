import re
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nlp.preference_extraction import CATEGORY_ASPECTS, ASPECT_SYNONYMS

# Initialize NLTK VADER analyzer
try:
    sia = SentimentIntensityAnalyzer()
except Exception:
    nltk.download('vader_lexicon', quiet=True)
    sia = SentimentIntensityAnalyzer()

# Domain-specific sentiment lexicons for hardware, appliances, and online retail reviews
POSITIVE_TECH_WORDS = [
    "fantastic", "excellent", "superb", "crisp", "sharp", "stunning", "amazing",
    "snappy", "fluid", "premium", "durable", "solid", "punchy", "clear", "bright",
    "top-notch", "beast", "great", "good", "fast", "smooth", "impressive", "long-lasting",
    "chills fast", "ice cold", "chilling", "whisper quiet", "silent", "power saver",
    "low power", "stains vanish", "cleans well", "cushioned", "comfortable", "comfy",
    "sturdy", "energy efficient", "5 star", "crystal clear", "easy to clean"
]

NEGATIVE_TECH_WORDS = [
    "drains quickly", "drain", "drains", "poor", "terrible", "laggy", "lags", "slow",
    "heating", "overheats", "heats up", "mediocre", "blurry", "muddy", "distortion",
    "uncomfortable", "plastic", "cheap", "fails", "glitchy", "bad", "worst", "horrible",
    "heavy", "scratch", "subpar", "disappointing", "noisy", "rattling", "vibrates",
    "loud", "weak cooling", "slow cooling", "stains remain", "high electricity bill",
    "power hungry", "tangles clothes", "rough sole", "painful"
]


def split_into_clauses(text):
    """Splits text by punctuation and conjunctions into meaningful clauses."""
    delimiters = r'[,.;!\n\r]+|\b(?:but|however|although|whereas|though|while|and)\b'
    clauses = [c.strip() for c in re.split(delimiters, text, flags=re.IGNORECASE) if c.strip()]
    return clauses if clauses else [text.strip()]


def classify_clause_sentiment(clause_text):
    """Classifies sentiment of a specific clause into positive, neutral, or negative."""
    text_lower = clause_text.lower()

    # Check domain-specific tech terms first
    pos_matches = sum(1 for w in POSITIVE_TECH_WORDS if w in text_lower)
    neg_matches = sum(1 for w in NEGATIVE_TECH_WORDS if w in text_lower)

    if pos_matches > neg_matches:
        return "positive"
    elif neg_matches > pos_matches:
        return "negative"

    # Use VADER compound score
    scores = sia.polarity_scores(clause_text)
    compound = scores['compound']

    if compound >= 0.15:
        return "positive"
    elif compound <= -0.15:
        return "negative"
    else:
        return "neutral"


def extract_aspect_sentiments(review_text, category="Smartphone"):
    """
    Extracts aspect-level sentiments from a single review.
    Returns dict like: {"camera": "positive", "battery": "negative"}
    """
    aspects = CATEGORY_ASPECTS.get(category, CATEGORY_ASPECTS["Smartphone"])
    clauses = split_into_clauses(review_text)

    aspect_sentiments = {}

    for clause in clauses:
        clause_lower = clause.lower()
        clause_sentiment = classify_clause_sentiment(clause)

        for aspect in aspects:
            if aspect == "price":
                continue
            synonyms = ASPECT_SYNONYMS.get(aspect, [aspect])
            if any(re.search(r'\b' + re.escape(syn) + r'\b', clause_lower) for syn in synonyms):
                # If already present, let positive/negative override neutral
                if aspect not in aspect_sentiments or aspect_sentiments[aspect] == "neutral":
                    aspect_sentiments[aspect] = clause_sentiment
                elif aspect_sentiments[aspect] != clause_sentiment and clause_sentiment != "neutral":
                    aspect_sentiments[aspect] = clause_sentiment

    # If no aspects identified from clauses, check entire text
    if not aspect_sentiments:
        text_lower = review_text.lower()
        full_sentiment = classify_clause_sentiment(review_text)
        for aspect in aspects:
            synonyms = ASPECT_SYNONYMS.get(aspect, [aspect])
            if any(re.search(r'\b' + re.escape(syn) + r'\b', text_lower) for syn in synonyms):
                aspect_sentiments[aspect] = full_sentiment

    return aspect_sentiments


def aggregate_product_aspect_scores(reviews, category="Smartphone", spec_scores=None):
    """
    Aggregates all reviews for a product into a normalized 0-1 aspect sentiment score.
    Returns: {"camera": 0.94, "battery": 0.65, ...}
    """
    aspects = [a for a in CATEGORY_ASPECTS.get(category, CATEGORY_ASPECTS["Smartphone"]) if a != "price"]
    spec_scores = spec_scores or {}

    stats = {a: {"pos": 0, "neu": 0, "neg": 0, "total": 0} for a in aspects}

    for rev in reviews:
        sentiments = rev.get_aspect_sentiments() if hasattr(rev, "get_aspect_sentiments") else rev.get("aspect_sentiments_json", {})
        if isinstance(sentiments, str):
            import json
            try:
                sentiments = json.loads(sentiments)
            except Exception:
                sentiments = {}

        for aspect, sentiment in sentiments.items():
            if aspect in stats:
                stats[aspect]["total"] += 1
                if sentiment == "positive":
                    stats[aspect]["pos"] += 1
                elif sentiment == "negative":
                    stats[aspect]["neg"] += 1
                else:
                    stats[aspect]["neu"] += 1

    aggregated = {}
    for a in aspects:
        total = stats[a]["total"]
        if total > 0:
            pos = stats[a]["pos"]
            neu = stats[a]["neu"]
            # (pos + 0.5 * neu) / total
            score = round((pos + 0.5 * neu) / total, 2)
        else:
            # Fallback to spec score if available, else 0.75
            score = float(spec_scores.get(a, 0.75))
        aggregated[a] = score

    return aggregated
