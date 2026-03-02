"""Product Researcher Agent - Finds Amazon products with affiliate potential."""

from loguru import logger
from src.agents.base import BaseAgent
from src.api import AmazonAPI, AmazonProduct
from src.database import Product, ProductStatus, get_session


class ProductResearcherAgent(BaseAgent):
    """Agent that discovers and catalogs Amazon products."""

    name = "product_researcher"

    def __init__(self, config: dict = None):
        super().__init__(config)
        self.amazon = AmazonAPI()
        self.niches = config.get("niches", ["home-kitchen", "electronics", "beauty"])
        self.price_range = config.get("price_range", {"min": 10, "max": 100})
        self.min_rating = config.get("min_rating", 4.0)
        self.min_reviews = config.get("min_reviews", 50)
        self.daily_target = config.get("daily_target", 25)

    async def run(self):
        """Run product discovery."""
        self.log("start", f"Starting product discovery for niches: {self.niches}")
        products_found = 0

        for niche in self.niches:
            try:
                products = await self._search_niche(niche)
                for product in products:
                    if self._passes_filters(product):
                        saved = await self._save_product(product)
                        if saved:
                            products_found += 1

                        if products_found >= self.daily_target:
                            break
            except Exception as e:
                self.log("error", f"Error searching {niche}: {e}", level="ERROR")

            if products_found >= self.daily_target:
                break

        self.log("complete", f"Found {products_found} products")
        return products_found

    async def _search_niche(self, niche: str) -> list[AmazonProduct]:
        """Search for products in a niche."""
        # Search terms for each niche
        search_terms = {
            "home-kitchen": ["kitchen gadgets", "home organizers", "cooking tools"],
            "electronics": ["tech accessories", "phone accessories", "smart home"],
            "beauty": ["skincare", "makeup tools", "hair care"],
            "sports-fitness": ["workout equipment", "fitness accessories", "yoga"],
            "tools-home-improvement": ["power tools", "hand tools", "home repair"],
        }

        terms = search_terms.get(niche, [niche])
        all_products = []

        for term in terms:
            products = await self.amazon.search_products(
                keywords=term,
                category=niche,
                min_price=self.price_range["min"],
                max_price=self.price_range["max"],
                limit=10
            )
            all_products.extend(products)

        return all_products

    def _passes_filters(self, product: AmazonProduct) -> bool:
        """Check if product passes quality filters."""
        if product.price < self.price_range["min"]:
            return False
        if product.price > self.price_range["max"]:
            return False
        if product.rating < self.min_rating:
            return False
        if product.review_count < self.min_reviews:
            return False
        return True

    async def _save_product(self, product: AmazonProduct) -> bool:
        """Save product to database if not already exists."""
        existing = self.db.query(Product).filter_by(asin=product.asin).first()
        if existing:
            return False

        db_product = Product(
            asin=product.asin,
            title=product.title,
            description=product.description,
            price=product.price,
            list_price=product.list_price,
            rating=product.rating,
            review_count=product.review_count,
            image_url=product.image_url,
            images=str(product.images),
            affiliate_link=product.affiliate_link,
            category=product.category,
            commission_rate=self.amazon.get_commission_rate(product.category),
            specs=str(product.specs),
            status=ProductStatus.PENDING.value
        )

        self.db.add(db_product)
        self.db.commit()

        self.log("product_saved", f"Saved: {product.asin} - {product.title[:50]}")
        return True

    async def status(self) -> dict:
        """Get researcher status."""
        pending = self.db.query(Product).filter_by(status=ProductStatus.PENDING.value).count()
        total = self.db.query(Product).count()

        return {
            "agent": self.name,
            "total_products": total,
            "pending_products": pending,
            "niches": self.niches,
            "daily_target": self.daily_target
        }

    async def get_pending_products(self, limit: int = 10) -> list[Product]:
        """Get pending products for posting."""
        return (
            self.db.query(Product)
            .filter_by(status=ProductStatus.PENDING.value)
            .order_by(Product.rating.desc(), Product.review_count.desc())
            .limit(limit)
            .all()
        )
