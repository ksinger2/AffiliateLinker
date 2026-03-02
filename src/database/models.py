"""Database models for AffiliateLinker."""

from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
import enum

Base = declarative_base()


class ProductStatus(enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    POSTED = "posted"
    REJECTED = "rejected"


class Product(Base):
    """Amazon product with affiliate link."""

    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    asin = Column(String(20), unique=True, nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    price = Column(Float)
    list_price = Column(Float)
    rating = Column(Float)
    review_count = Column(Integer)
    image_url = Column(String(1000))
    images = Column(Text)  # JSON array of image URLs
    affiliate_link = Column(String(1000))
    category = Column(String(200))
    commission_rate = Column(Float)
    specs = Column(Text)  # JSON object
    discovered_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default=ProductStatus.PENDING.value)

    posts = relationship("Post", back_populates="product")

    def __repr__(self):
        return f"<Product {self.asin}: {self.title[:50]}>"


class Post(Base):
    """Pinterest pin post."""

    __tablename__ = "posts"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    pin_id = Column(String(100))
    board_id = Column(String(100))
    board_name = Column(String(200))
    pin_title = Column(String(100))
    pin_description = Column(Text)
    posted_at = Column(DateTime, default=datetime.utcnow)
    scheduled_for = Column(DateTime)

    # Metrics (updated via Pinterest API)
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    saves = Column(Integer, default=0)

    product = relationship("Product", back_populates="posts")

    def __repr__(self):
        return f"<Post {self.pin_id} for {self.product.asin}>"


class Strategy(Base):
    """Strategy recommendations and research."""

    __tablename__ = "strategies"

    id = Column(Integer, primary_key=True)
    category = Column(String(50))  # niche, tactic, competitor
    title = Column(String(200))
    content = Column(Text)
    priority = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    applied = Column(Integer, default=0)  # 0 = not applied, 1 = applied


class SystemLog(Base):
    """System activity log."""

    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    agent = Column(String(50))
    action = Column(String(100))
    details = Column(Text)
    level = Column(String(20), default="INFO")


class Metric(Base):
    """Daily metrics snapshot."""

    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True)
    date = Column(DateTime, nullable=False)
    products_discovered = Column(Integer, default=0)
    posts_made = Column(Integer, default=0)
    total_impressions = Column(Integer, default=0)
    total_clicks = Column(Integer, default=0)
    total_saves = Column(Integer, default=0)
    estimated_revenue = Column(Float, default=0.0)


def init_db(db_path: str = "data/affiliatelinker.db"):
    """Initialize database and create tables."""
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)


def get_session(db_path: str = "data/affiliatelinker.db"):
    """Get a database session."""
    Session = init_db(db_path)
    return Session()
