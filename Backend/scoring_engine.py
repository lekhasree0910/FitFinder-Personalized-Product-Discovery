import json
from nlp.preference_extraction import CATEGORY_ASPECTS

def calculate_price_score(price, budget):
    """
    Computes a 0-1 score for product price relative to user's budget.
    """
    if not budget or budget <= 0:
        return 0.85

    if price <= budget:
        # Lower price under budget gives higher score (0.75 - 1.0)
        ratio = price / budget
        return round(1.0 - (0.25 * ratio), 2)
    else:
        # Over budget penalty
        over_ratio = (price - budget) / budget
        return max(0.1, round(0.7 - over_ratio, 2))


def blend_aspect_scores(spec_scores, absa_scores, category, price=None, budget=None):
    """
    Blends catalog spec score with review-derived ABSA sentiment score.
    Aspect Score = 0.5 * spec + 0.5 * absa (or 100% of available source).
    """
    aspects = CATEGORY_ASPECTS.get(category, CATEGORY_ASPECTS["Smartphone"])
    blended = {}

    for aspect in aspects:
        if aspect == "price":
            blended["price"] = calculate_price_score(price, budget) if price else 0.80
            continue

        spec = float(spec_scores.get(aspect, 0.70))
        if aspect in absa_scores:
            absa = float(absa_scores[aspect])
            score = round((0.4 * spec) + (0.6 * absa), 2)
        else:
            score = spec
        blended[aspect] = score

    return blended


def calculate_personalized_scores(products, preference_weights, category="Smartphone", budget=None):
    """
    Ranks shortlisted products by Personalized Score = Σ (Aspect Score * Weight).
    Returns ranked list and scores dictionary.
    """
    aspects = CATEGORY_ASPECTS.get(category, CATEGORY_ASPECTS["Smartphone"])
    scores_breakdown = {}
    ranked_products = []

    for product in products:
        p_id = str(product.product_id if hasattr(product, 'product_id') else product['product_id'])
        spec_scores = product.get_spec_scores() if hasattr(product, 'get_spec_scores') else product.get('spec_scores_json', {})
        if isinstance(spec_scores, str):
            try:
                spec_scores = json.loads(spec_scores)
            except Exception:
                spec_scores = {}

        # Get ABSA scores
        absa_scores = {}
        if hasattr(product, 'aspect_aggregate') and product.aspect_aggregate:
            absa_scores = product.aspect_aggregate.get_aspect_scores()
        elif 'aspect_scores_json' in product:
            absa_scores = product['aspect_scores_json']
            if isinstance(absa_scores, str):
                try:
                    absa_scores = json.loads(absa_scores)
                except Exception:
                    absa_scores = {}

        price = product.price if hasattr(product, 'price') else product.get('price')
        blended = blend_aspect_scores(spec_scores, absa_scores, category, price, budget)

        # Compute weighted sum
        total_score = 0.0
        feature_contributions = {}

        for aspect in aspects:
            weight = float(preference_weights.get(aspect, 0.0))
            aspect_score = blended.get(aspect, 0.70)
            weighted_val = aspect_score * weight
            total_score += weighted_val
            feature_contributions[aspect] = {
                "aspect_score": aspect_score,
                "importance_weight": weight,
                "weighted_score": round(weighted_val, 4)
            }

        final_score = round(total_score, 2)
        match_percentage = round(final_score * 100, 1)

        product_score_data = {
            "product_id": int(p_id),
            "name": product.name if hasattr(product, 'name') else product.get('name'),
            "brand": product.brand if hasattr(product, 'brand') else product.get('brand'),
            "price": price,
            "final_score": final_score,
            "match_percentage": match_percentage,
            "aspect_scores": blended,
            "feature_contributions": feature_contributions
        }

        scores_breakdown[p_id] = product_score_data
        ranked_products.append(product_score_data)

    # Rank by final_score descending
    ranked_products.sort(key=lambda x: x["final_score"], reverse=True)
    top_recommendation_id = ranked_products[0]["product_id"] if ranked_products else None

    return {
        "scores_json": scores_breakdown,
        "ranked_products": ranked_products,
        "top_recommendation_id": top_recommendation_id
    }
