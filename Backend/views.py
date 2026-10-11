import json
import datetime
from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from database import SessionLocal
from models import User, Query, Product, Review, AspectAggregate, Comparison, Explanation
from nlp.preference_extraction import (
    parse_query, CATEGORY_ASPECTS, extract_preference_weights, extract_budget, detect_category
)
from nlp.absa_engine import (
    extract_aspect_sentiments, aggregate_product_aspect_scores
)
from scoring_engine import calculate_personalized_scores, blend_aspect_scores
from explanation_generator import generate_grounded_explanation

api = Blueprint('api', __name__)

def get_db_session():
    return SessionLocal()


# ==========================================
# 1. USER MANAGEMENT APIS (4)
# ==========================================

@api.route('/auth/register/', methods=['POST'])
def register():
    data = request.get_json() or {}
    full_name = data.get('full_name', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '').strip()

    if not full_name or not email or not password:
        return jsonify({"error": "Full name, email, and password are required."}), 400

    db = get_db_session()
    try:
        if db.query(User).filter_by(email=email).first():
            return jsonify({"error": "An account with this email already exists."}), 409

        user = User(
            full_name=full_name,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        session['user_id'] = user.user_id
        return jsonify({
            "message": "User registered successfully",
            "user": user.to_dict()
        }), 201
    finally:
        db.close()


@api.route('/auth/login/', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '').strip()

    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400

    db = get_db_session()
    try:
        user = db.query(User).filter_by(email=email).first()
        if not user or not check_password_hash(user.password_hash, password):
            return jsonify({"error": "Invalid email or password."}), 401

        session['user_id'] = user.user_id
        return jsonify({
            "message": "Login successful",
            "user": user.to_dict()
        }), 200
    finally:
        db.close()


@api.route('/auth/logout/', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({"message": "Logged out successfully"}), 200


@api.route('/users/<int:user_id>/profile/', methods=['GET'])
def get_user_profile(user_id):
    db = get_db_session()
    try:
        user = db.query(User).filter_by(user_id=user_id).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        queries = db.query(Query).filter_by(user_id=user_id).order_by(Query.submitted_at.desc()).all()
        return jsonify({
            "user": user.to_dict(),
            "total_queries": len(queries),
            "recent_queries": [q.to_dict() for q in queries[:5]]
        }), 200
    finally:
        db.close()


# ==========================================
# 2. CHOICEAI PREFERENCE EXTRACTION APIS (3)
# ==========================================

@api.route('/choiceai/query/', methods=['POST'])
def submit_choiceai_query():
    """
    Submits a free-text shopping query, runs NLP entity & preference extraction,
    stores the query profile, and returns the structured result.
    """
    data = request.get_json() or {}
    raw_query = data.get('raw_query_text', '').strip()
    explicit_category = data.get('category')
    user_id = data.get('user_id', session.get('user_id', 101))

    if not raw_query:
        return jsonify({"error": "Query text cannot be empty."}), 400

    parsed = parse_query(raw_query, explicit_category)
    category = parsed["category"]
    budget = parsed["budget"]
    preference_weights = parsed["preference_weights"]

    db = get_db_session()
    try:
        query_obj = Query(
            user_id=user_id,
            raw_query_text=raw_query,
            category=category,
            budget=budget,
            preference_weights_json=json.dumps(preference_weights)
        )
        db.add(query_obj)
        db.commit()
        db.refresh(query_obj)

        return jsonify({
            "message": "Query analyzed successfully by ChoiceAI",
            "query": query_obj.to_dict(),
            "aspect_set": CATEGORY_ASPECTS.get(category, [])
        }), 200
    finally:
        db.close()


@api.route('/choiceai/query/<int:query_id>/', methods=['GET'])
def get_choiceai_query(query_id):
    db = get_db_session()
    try:
        query_obj = db.query(Query).filter_by(query_id=query_id).first()
        if not query_obj:
            return jsonify({"error": "Query not found"}), 404
        return jsonify(query_obj.to_dict()), 200
    finally:
        db.close()


@api.route('/categories/<string:category>/aspects/', methods=['GET'])
def get_category_aspects(category):
    # Case insensitive matching
    cat_match = next((k for k in CATEGORY_ASPECTS if k.lower() == category.lower()), None)
    if not cat_match:
        return jsonify({"error": f"Category '{category}' not supported.", "supported_categories": list(CATEGORY_ASPECTS.keys())}), 404

    return jsonify({
        "category": cat_match,
        "aspects": CATEGORY_ASPECTS[cat_match]
    }), 200


@api.route('/categories/', methods=['GET'])
def get_all_categories():
    return jsonify({
        "categories": list(CATEGORY_ASPECTS.keys()),
        "category_aspects": CATEGORY_ASPECTS
    }), 200


# ==========================================
# 3. PRODUCT CATALOG & FILTERING APIS (4)
# ==========================================

@api.route('/products/', methods=['GET'])
def list_products():
    category = request.args.get('category')
    search = request.args.get('search', '').strip().lower()

    db = get_db_session()
    try:
        q = db.query(Product)
        if category:
            q = q.filter(Product.category.ilike(category))
        if search:
            q = q.filter(Product.name.ilike(f"%{search}%") | Product.brand.ilike(f"%{search}%"))

        products = q.all()
        return jsonify([p.to_dict() for p in products]), 200
    finally:
        db.close()


@api.route('/products/<int:product_id>/', methods=['GET'])
def get_product_details(product_id):
    db = get_db_session()
    try:
        prod = db.query(Product).filter_by(product_id=product_id).first()
        if not prod:
            return jsonify({"error": "Product not found"}), 404

        reviews = db.query(Review).filter_by(product_id=product_id).all()
        aspect_aggregate = db.query(AspectAggregate).filter_by(product_id_agg=product_id).first()

        res = prod.to_dict()
        res["reviews"] = [r.to_dict() for r in reviews]
        res["aspect_scores"] = aspect_aggregate.get_aspect_scores() if aspect_aggregate else prod.get_spec_scores()
        return jsonify(res), 200
    finally:
        db.close()


@api.route('/products/shortlist/', methods=['POST'])
def shortlist_products():
    """
    Filters and shortlists products based on category, budget, and preference profile.
    Calculates initial match previews.
    """
    data = request.get_json() or {}
    category = data.get('category', 'Smartphone')
    budget = data.get('budget')
    if budget is not None:
        try:
            budget = float(budget)
        except Exception:
            budget = None

    preference_weights = data.get('preference_weights_json') or data.get('preference_weights') or {}
    if not preference_weights:
        aspects = CATEGORY_ASPECTS.get(category, CATEGORY_ASPECTS["Smartphone"])
        preference_weights = {a: round(1.0 / len(aspects), 2) for a in aspects}

    db = get_db_session()
    try:
        # Category filter
        query = db.query(Product).filter(Product.category.ilike(category))

        # Budget filter (allowing a flexible 10% buffer if under strict budget or filter strict)
        if budget and budget > 0:
            query = query.filter(Product.price <= budget * 1.15)

        candidates = query.all()

        # If strict budget filtered everything out, relax to category
        if not candidates:
            candidates = db.query(Product).filter(Product.category.ilike(category)).all()

        scoring_result = calculate_personalized_scores(candidates, preference_weights, category, budget)

        return jsonify({
            "category": category,
            "budget": budget,
            "total_candidates": len(candidates),
            "shortlisted_products": scoring_result["ranked_products"],
            "top_recommendation_id": scoring_result["top_recommendation_id"]
        }), 200
    finally:
        db.close()


@api.route('/products/', methods=['POST'])
def create_product():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    brand = data.get('brand', '').strip()
    category = data.get('category', '').strip()
    price = data.get('price')

    if not name or not brand or not category or price is None:
        return jsonify({"error": "name, brand, category, and price are required."}), 400

    spec_scores = data.get('spec_scores_json', {})
    image_url = data.get('image_url')

    db = get_db_session()
    try:
        prod = Product(
            name=name,
            brand=brand,
            category=category,
            price=float(price),
            spec_scores_json=json.dumps(spec_scores),
            image_url=image_url
        )
        db.add(prod)
        db.commit()
        db.refresh(prod)

        # Create initial aggregate
        agg = AspectAggregate(
            product_id_agg=prod.product_id,
            aspect_scores_json=json.dumps(spec_scores)
        )
        db.add(agg)
        db.commit()

        return jsonify(prod.to_dict()), 201
    finally:
        db.close()


# ==========================================
# 4. REVIEW INGESTION & ABSA APIS (3)
# ==========================================

@api.route('/reviews/', methods=['POST'])
def ingest_review():
    """
    Ingests a new review, runs ABSA aspect sentiment extraction,
    and updates the product's cached aspect aggregate.
    """
    data = request.get_json() or {}
    product_id = data.get('product_id')
    review_text = data.get('review_text', '').strip()
    rating = data.get('rating', 4.0)

    if not product_id or not review_text:
        return jsonify({"error": "product_id and review_text are required."}), 400

    db = get_db_session()
    try:
        prod = db.query(Product).filter_by(product_id=product_id).first()
        if not prod:
            return jsonify({"error": "Product not found."}), 404

        # Run ABSA
        aspect_sentiments = extract_aspect_sentiments(review_text, prod.category)

        review = Review(
            product_id=product_id,
            review_text=review_text,
            rating=float(rating) if rating else None,
            aspect_sentiments_json=json.dumps(aspect_sentiments)
        )
        db.add(review)
        db.commit()
        db.refresh(review)

        # Automatically recompute and update aggregate
        all_reviews = db.query(Review).filter_by(product_id=product_id).all()
        agg_scores = aggregate_product_aspect_scores(all_reviews, prod.category, prod.get_spec_scores())

        agg = db.query(AspectAggregate).filter_by(product_id_agg=product_id).first()
        if not agg:
            agg = AspectAggregate(product_id_agg=product_id)
            db.add(agg)

        agg.set_aspect_scores(agg_scores)
        agg.last_computed_at = datetime.datetime.utcnow()
        db.commit()

        return jsonify({
            "message": "Review ingested and aspect sentiments extracted successfully",
            "review": review.to_dict(),
            "updated_aspect_aggregate": agg.to_dict()
        }), 201
    finally:
        db.close()


@api.route('/products/<int:product_id>/absa/recompute/', methods=['POST'])
def recompute_product_absa(product_id):
    db = get_db_session()
    try:
        prod = db.query(Product).filter_by(product_id=product_id).first()
        if not prod:
            return jsonify({"error": "Product not found."}), 404

        all_reviews = db.query(Review).filter_by(product_id=product_id).all()
        agg_scores = aggregate_product_aspect_scores(all_reviews, prod.category, prod.get_spec_scores())

        agg = db.query(AspectAggregate).filter_by(product_id_agg=product_id).first()
        if not agg:
            agg = AspectAggregate(product_id_agg=product_id)
            db.add(agg)

        agg.set_aspect_scores(agg_scores)
        agg.last_computed_at = datetime.datetime.utcnow()
        db.commit()
        db.refresh(agg)

        return jsonify({
            "message": f"ABSA scores recomputed for product {product_id}",
            "aggregate": agg.to_dict()
        }), 200
    finally:
        db.close()


@api.route('/products/<int:product_id>/aspect-scores/', methods=['GET'])
def get_product_aspect_scores(product_id):
    db = get_db_session()
    try:
        prod = db.query(Product).filter_by(product_id=product_id).first()
        if not prod:
            return jsonify({"error": "Product not found."}), 404

        agg = db.query(AspectAggregate).filter_by(product_id_agg=product_id).first()
        if not agg:
            scores = prod.get_spec_scores()
        else:
            scores = agg.get_aspect_scores()

        return jsonify({
            "product_id": product_id,
            "name": prod.name,
            "category": prod.category,
            "aspect_scores": scores
        }), 200
    finally:
        db.close()


# ==========================================
# 5. COMPAREWISE SCORING & RECOMMENDATION APIS (3)
# ==========================================

@api.route('/comparewise/compare/', methods=['POST'])
def run_comparewise_comparison():
    """
    Scores and ranks shortlisted products against the query's preference profile.
    Stores comparison record and generates grounded explanations.
    """
    data = request.get_json() or {}
    query_id = data.get('query_id')
    product_ids = data.get('product_ids', [])

    db = get_db_session()
    try:
        query_obj = None
        if query_id:
            query_obj = db.query(Query).filter_by(query_id=query_id).first()

        category = data.get('category') or (query_obj.category if query_obj else 'Smartphone')
        budget = data.get('budget') if data.get('budget') is not None else (query_obj.budget if query_obj else None)
        preference_weights = data.get('preference_weights') or (query_obj.get_preference_weights() if query_obj else {})

        if not preference_weights:
            aspects = CATEGORY_ASPECTS.get(category, CATEGORY_ASPECTS["Smartphone"])
            preference_weights = {a: round(1.0 / len(aspects), 2) for a in aspects}

        if not product_ids:
            # Auto-select all category candidates
            prods = db.query(Product).filter(Product.category.ilike(category)).all()
        else:
            prods = db.query(Product).filter(Product.product_id.in_(product_ids)).all()

        if not prods:
            return jsonify({"error": "No products found for comparison."}), 404

        scoring_result = calculate_personalized_scores(prods, preference_weights, category, budget)
        top_id = scoring_result["top_recommendation_id"]

        # Save comparison record
        if not query_obj:
            # Create a fallback query object if none provided
            query_obj = Query(
                user_id=session.get('user_id', 101),
                raw_query_text=f"Direct comparison of {len(prods)} products in {category}",
                category=category,
                budget=budget,
                preference_weights_json=json.dumps(preference_weights)
            )
            db.add(query_obj)
            db.commit()
            db.refresh(query_obj)

        comp = Comparison(
            query_id=query_obj.query_id,
            product_ids_json=json.dumps([p.product_id for p in prods]),
            scores_json=json.dumps(scoring_result["scores_json"]),
            top_recommendation_id=top_id
        )
        db.add(comp)
        db.commit()
        db.refresh(comp)

        # Generate grounded explanations for all products
        explanations_map = {}
        for p in prods:
            p_scores = scoring_result["scores_json"].get(str(p.product_id), {}).get("aspect_scores", p.get_spec_scores())
            expl = generate_grounded_explanation(p.name, p.brand, p_scores, category)
            
            db_expl = Explanation(
                comparison_id=comp.comparison_id,
                product_id=p.product_id,
                strengths_text=expl["strengths_text"],
                weakness_text=expl["weakness_text"]
            )
            db.add(db_expl)
            explanations_map[str(p.product_id)] = expl

        db.commit()

        return jsonify({
            "comparison_id": comp.comparison_id,
            "query_id": comp.query_id,
            "category": category,
            "top_recommendation_id": top_id,
            "ranked_products": scoring_result["ranked_products"],
            "scores_json": scoring_result["scores_json"],
            "explanations": explanations_map
        }), 200
    finally:
        db.close()


@api.route('/comparewise/<int:comparison_id>/', methods=['GET'])
def get_comparison_result(comparison_id):
    db = get_db_session()
    try:
        comp = db.query(Comparison).filter_by(comparison_id=comparison_id).first()
        if not comp:
            return jsonify({"error": "Comparison not found"}), 404

        explanations = db.query(Explanation).filter_by(comparison_id=comparison_id).all()
        expl_dict = {str(e.product_id): e.to_dict() for e in explanations}

        res = comp.to_dict()
        res["explanations"] = expl_dict
        return jsonify(res), 200
    finally:
        db.close()


@api.route('/comparewise/<int:comparison_id>/recommendation/', methods=['GET'])
def get_comparison_recommendation(comparison_id):
    db = get_db_session()
    try:
        comp = db.query(Comparison).filter_by(comparison_id=comparison_id).first()
        if not comp:
            return jsonify({"error": "Comparison not found"}), 404

        top_id = comp.top_recommendation_id
        top_prod = db.query(Product).filter_by(product_id=top_id).first()
        scores = comp.get_scores()
        top_score_data = scores.get(str(top_id), {})

        expl = db.query(Explanation).filter_by(comparison_id=comparison_id, product_id=top_id).first()

        return jsonify({
            "comparison_id": comparison_id,
            "top_product": top_prod.to_dict() if top_prod else None,
            "personalized_score_data": top_score_data,
            "explanation": expl.to_dict() if expl else None
        }), 200
    finally:
        db.close()


# ==========================================
# 6. EXPLANATION & COMPARISON VIEW APIS (2)
# ==========================================

@api.route('/comparewise/<int:comparison_id>/explanation/<int:product_id>/', methods=['GET'])
def get_product_explanation(comparison_id, product_id):
    db = get_db_session()
    try:
        expl = db.query(Explanation).filter_by(comparison_id=comparison_id, product_id=product_id).first()
        if not expl:
            return jsonify({"error": "Explanation not found"}), 404
        return jsonify(expl.to_dict()), 200
    finally:
        db.close()


@api.route('/comparewise/<int:comparison_id>/table/', methods=['GET'])
def get_comparison_table(comparison_id):
    db = get_db_session()
    try:
        comp = db.query(Comparison).filter_by(comparison_id=comparison_id).first()
        if not comp:
            return jsonify({"error": "Comparison not found"}), 404

        product_ids = comp.get_product_ids()
        products = db.query(Product).filter(Product.product_id.in_(product_ids)).all()
        query = comp.query

        category = query.category if query else (products[0].category if products else "Smartphone")
        aspects = CATEGORY_ASPECTS.get(category, CATEGORY_ASPECTS["Smartphone"])

        scores_json = comp.get_scores()
        explanations = db.query(Explanation).filter_by(comparison_id=comparison_id).all()
        expl_map = {str(e.product_id): e.to_dict() for e in explanations}

        table_rows = []
        for p in products:
            p_id = str(p.product_id)
            score_data = scores_json.get(p_id, {})
            p_aspect_scores = score_data.get("aspect_scores", {})
            
            row = {
                "product_id": p.product_id,
                "name": p.name,
                "brand": p.brand,
                "price": p.price,
                "image_url": p.image_url,
                "is_top_recommendation": (p.product_id == comp.top_recommendation_id),
                "final_score": score_data.get("final_score", 0.0),
                "match_percentage": score_data.get("match_percentage", 0.0),
                "aspects": {a: p_aspect_scores.get(a, 0.70) for a in aspects},
                "explanation": expl_map.get(p_id, {})
            }
            table_rows.append(row)

        table_rows.sort(key=lambda x: x["final_score"], reverse=True)

        return jsonify({
            "comparison_id": comparison_id,
            "category": category,
            "aspect_headers": aspects,
            "preference_weights": query.get_preference_weights() if query else {},
            "top_recommendation_id": comp.top_recommendation_id,
            "rows": table_rows
        }), 200
    finally:
        db.close()


# ==========================================
# 7. USER HISTORY API
# ==========================================

@api.route('/users/<int:user_id>/history/', methods=['GET'])
def get_user_history(user_id):
    db = get_db_session()
    try:
        queries = db.query(Query).filter_by(user_id=user_id).order_by(Query.submitted_at.desc()).all()
        history_items = []
        for q in queries:
            comps = db.query(Comparison).filter_by(query_id=q.query_id).all()
            history_items.append({
                "query": q.to_dict(),
                "comparisons": [c.to_dict() for c in comps]
            })
        return jsonify({
            "user_id": user_id,
            "history": history_items
        }), 200
    finally:
        db.close()
