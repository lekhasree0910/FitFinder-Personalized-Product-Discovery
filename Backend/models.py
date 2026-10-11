import datetime
import json
from sqlalchemy import (
    Column, Integer, String, Float, Text, DateTime, ForeignKey, Enum as SqlEnum
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    full_name = Column(String(150), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    queries = relationship("Query", back_populates="user", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "full_name": self.full_name,
            "email": self.email,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class Query(Base):
    __tablename__ = 'queries'

    query_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    raw_query_text = Column(Text, nullable=False)
    category = Column(String(50), nullable=False)
    budget = Column(Float, nullable=True)
    preference_weights_json = Column(Text, nullable=False, default="{}")
    submitted_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="queries")
    comparisons = relationship("Comparison", back_populates="query", cascade="all, delete-orphan")

    def get_preference_weights(self):
        try:
            return json.loads(self.preference_weights_json)
        except Exception:
            return {}

    def set_preference_weights(self, weights_dict):
        self.preference_weights_json = json.dumps(weights_dict)

    def to_dict(self):
        return {
            "query_id": self.query_id,
            "user_id": self.user_id,
            "raw_query_text": self.raw_query_text,
            "category": self.category,
            "budget": self.budget,
            "preference_weights_json": self.get_preference_weights(),
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None
        }


class Product(Base):
    __tablename__ = 'products'

    product_id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    brand = Column(String(100), nullable=False)
    price = Column(Float, nullable=False)
    spec_scores_json = Column(Text, nullable=False, default="{}")
    image_url = Column(String(500), nullable=True)

    reviews = relationship("Review", back_populates="product", cascade="all, delete-orphan")
    aspect_aggregate = relationship("AspectAggregate", uselist=False, back_populates="product", cascade="all, delete-orphan")

    def get_spec_scores(self):
        try:
            return json.loads(self.spec_scores_json)
        except Exception:
            return {}

    def set_spec_scores(self, scores_dict):
        self.spec_scores_json = json.dumps(scores_dict)

    def to_dict(self):
        return {
            "product_id": self.product_id,
            "category": self.category,
            "name": self.name,
            "brand": self.brand,
            "price": self.price,
            "spec_scores_json": self.get_spec_scores(),
            "image_url": self.image_url
        }


class Review(Base):
    __tablename__ = 'reviews'

    review_id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey('products.product_id'), nullable=False)
    review_text = Column(Text, nullable=False)
    rating = Column(Float, nullable=True)
    aspect_sentiments_json = Column(Text, nullable=False, default="{}")

    product = relationship("Product", back_populates="reviews")

    def get_aspect_sentiments(self):
        try:
            return json.loads(self.aspect_sentiments_json)
        except Exception:
            return {}

    def set_aspect_sentiments(self, sentiments_dict):
        self.aspect_sentiments_json = json.dumps(sentiments_dict)

    def to_dict(self):
        return {
            "review_id": self.review_id,
            "product_id": self.product_id,
            "review_text": self.review_text,
            "rating": self.rating,
            "aspect_sentiments_json": self.get_aspect_sentiments()
        }


class AspectAggregate(Base):
    __tablename__ = 'aspect_aggregates'

    aggregate_id = Column(Integer, primary_key=True, autoincrement=True)
    product_id_agg = Column(Integer, ForeignKey('products.product_id'), unique=True, nullable=False)
    aspect_scores_json = Column(Text, nullable=False, default="{}")
    last_computed_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    product = relationship("Product", back_populates="aspect_aggregate")

    def get_aspect_scores(self):
        try:
            return json.loads(self.aspect_scores_json)
        except Exception:
            return {}

    def set_aspect_scores(self, scores_dict):
        self.aspect_scores_json = json.dumps(scores_dict)

    def to_dict(self):
        return {
            "aggregate_id": self.aggregate_id,
            "product_id_agg": self.product_id_agg,
            "aspect_scores_json": self.get_aspect_scores(),
            "last_computed_at": self.last_computed_at.isoformat() if self.last_computed_at else None
        }


class Comparison(Base):
    __tablename__ = 'comparisons'

    comparison_id = Column(Integer, primary_key=True, autoincrement=True)
    query_id = Column(Integer, ForeignKey('queries.query_id'), nullable=False)
    product_ids_json = Column(Text, nullable=False, default="[]")
    scores_json = Column(Text, nullable=False, default="{}")
    top_recommendation_id = Column(Integer, ForeignKey('products.product_id'), nullable=True)
    generated_at = Column(DateTime, default=datetime.datetime.utcnow)

    query = relationship("Query", back_populates="comparisons")
    top_recommendation = relationship("Product", foreign_keys=[top_recommendation_id])
    explanations = relationship("Explanation", back_populates="comparison", cascade="all, delete-orphan")

    def get_product_ids(self):
        try:
            return json.loads(self.product_ids_json)
        except Exception:
            return []

    def set_product_ids(self, ids_list):
        self.product_ids_json = json.dumps(ids_list)

    def get_scores(self):
        try:
            return json.loads(self.scores_json)
        except Exception:
            return {}

    def set_scores(self, scores_dict):
        self.scores_json = json.dumps(scores_dict)

    def to_dict(self):
        return {
            "comparison_id": self.comparison_id,
            "query_id": self.query_id,
            "product_ids_json": self.get_product_ids(),
            "scores_json": self.get_scores(),
            "top_recommendation_id": self.top_recommendation_id,
            "generated_at": self.generated_at.isoformat() if self.generated_at else None
        }


class Explanation(Base):
    __tablename__ = 'explanations'

    explanation_id = Column(Integer, primary_key=True, autoincrement=True)
    comparison_id = Column(Integer, ForeignKey('comparisons.comparison_id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.product_id'), nullable=False)
    strengths_text = Column(Text, nullable=False)
    weakness_text = Column(Text, nullable=False)

    comparison = relationship("Comparison", back_populates="explanations")
    product = relationship("Product")

    def to_dict(self):
        return {
            "explanation_id": self.explanation_id,
            "comparison_id": self.comparison_id,
            "product_id": self.product_id,
            "strengths_text": self.strengths_text,
            "weakness_text": self.weakness_text
        }
