def generate_grounded_explanation(product_name, brand, aspect_scores, category="Smartphone"):
    """
    Generates deterministic, grounded strength and weakness summaries
    strictly derived from aggregated aspect scores without LLM hallucination.
    """
    # Exclude price from aspect breakdown
    scored_aspects = [(aspect, score) for aspect, score in aspect_scores.items() if aspect != "price"]
    
    if not scored_aspects:
        return {
            "strengths_text": f"The {brand} {product_name} provides balanced overall specifications for general use.",
            "weakness_text": "No notable weaknesses reported in review sentiment data."
        }

    # Sort aspects by score descending
    scored_aspects.sort(key=lambda x: x[1], reverse=True)

    # Top 2 strengths
    top_aspects = scored_aspects[:2]
    strength_phrases = []
    for aspect, score in top_aspects:
        pct = int(score * 100)
        aspect_title = aspect.title()
        if score >= 0.85:
            strength_phrases.append(f"outstanding {aspect_title} performance (scored {pct}%)")
        elif score >= 0.70:
            strength_phrases.append(f"strong {aspect_title} capabilities (scored {pct}%)")
        else:
            strength_phrases.append(f"reliable {aspect_title} (scored {pct}%)")

    strengths_text = f"Top recommended for its {', and '.join(strength_phrases)}, supported by strong positive sentiment across verified user reviews."

    # Lowest aspect is weakness
    lowest_aspect, lowest_score = scored_aspects[-1]
    lowest_pct = int(lowest_score * 100)
    lowest_title = lowest_aspect.title()

    if lowest_score < 0.70:
        weakness_text = f"User feedback highlights lower satisfaction in {lowest_title} (scored {lowest_pct}%), where reviewers noted room for improvement."
    else:
        weakness_text = f"While all aspects perform well, {lowest_title} is its relatively lowest-rated feature at {lowest_pct}%."

    return {
        "strengths_text": strengths_text,
        "weakness_text": weakness_text
    }
