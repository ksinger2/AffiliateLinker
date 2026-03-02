"""Account Manager Agent - Handles Pinterest posting and scheduling."""

from datetime import datetime, timedelta
from loguru import logger
from src.agents.base import BaseAgent
from src.api import PinterestAPI, PinterestBoard
from src.database import Product, Post, ProductStatus, get_session


class AccountManagerAgent(BaseAgent):
    """Agent that manages Pinterest account and posting."""

    name = "account_manager"

    def __init__(self, config: dict = None):
        super().__init__(config)
        self.pinterest = PinterestAPI()
        self.posts_per_day = config.get("posts_per_day", 12)
        self.posting_times = config.get("posting_times", [
            "08:00", "08:30", "12:00", "12:30",
            "20:00", "20:30", "21:00", "21:30",
            "22:00", "22:30", "23:00", "23:30"
        ])
        self.boards: dict[str, PinterestBoard] = {}

    async def run(self):
        """Run posting cycle."""
        self.log("start", "Starting posting cycle")

        # Load boards
        await self._load_boards()

        # Get pending products
        pending = (
            self.db.query(Product)
            .filter_by(status=ProductStatus.APPROVED.value)
            .limit(self.posts_per_day)
            .all()
        )

        if not pending:
            self.log("skip", "No approved products to post")
            return 0

        posts_made = 0
        for product in pending:
            try:
                success = await self._post_product(product)
                if success:
                    posts_made += 1
            except Exception as e:
                self.log("error", f"Failed to post {product.asin}: {e}", level="ERROR")

        self.log("complete", f"Posted {posts_made} pins")
        return posts_made

    async def _load_boards(self):
        """Load existing boards or create new ones."""
        try:
            boards = await self.pinterest.list_boards()
            self.boards = {board.name: board for board in boards}
            self.log("boards_loaded", f"Loaded {len(boards)} boards")
        except Exception as e:
            self.log("error", f"Failed to load boards: {e}", level="ERROR")

    async def _get_or_create_board(self, category: str) -> PinterestBoard:
        """Get existing board or create new one for category."""
        board_names = {
            "home": "Home Essentials",
            "kitchen": "Home Essentials",
            "electronics": "Tech Finds",
            "beauty": "Beauty Must-Haves",
            "fitness": "Fitness Gear",
            "sports": "Fitness Gear",
            "tools": "DIY & Tools",
        }

        # Find matching board name
        board_name = "Daily Deals"
        category_lower = category.lower()
        for key, name in board_names.items():
            if key in category_lower:
                board_name = name
                break

        if board_name in self.boards:
            return self.boards[board_name]

        # Create new board
        try:
            board = await self.pinterest.create_board(
                name=board_name,
                description=f"Amazing {board_name.lower()} finds from around the web!"
            )
            self.boards[board_name] = board
            self.log("board_created", f"Created board: {board_name}")
            return board
        except Exception as e:
            self.log("error", f"Failed to create board: {e}", level="ERROR")
            raise

    async def _post_product(self, product: Product) -> bool:
        """Create a Pinterest pin for a product."""
        board = await self._get_or_create_board(product.category)

        # Generate pin content
        title = self._generate_title(product)
        description = self._generate_description(product)

        try:
            pin = await self.pinterest.create_pin(
                board_id=board.id,
                title=title,
                description=description,
                link=product.affiliate_link,
                image_url=product.image_url
            )

            # Save post record
            post = Post(
                product_id=product.id,
                pin_id=pin.id,
                board_id=board.id,
                board_name=board.name,
                pin_title=title,
                pin_description=description,
                posted_at=datetime.utcnow()
            )
            self.db.add(post)

            # Update product status
            product.status = ProductStatus.POSTED.value
            self.db.commit()

            self.log("posted", f"Posted pin {pin.id} for {product.asin}")
            return True

        except Exception as e:
            self.log("error", f"Failed to create pin: {e}", level="ERROR")
            return False

    def _generate_title(self, product: Product) -> str:
        """Generate compelling pin title (max 100 chars)."""
        title = product.title
        if len(title) > 95:
            title = title[:92] + "..."
        return title

    def _generate_description(self, product: Product) -> str:
        """Generate SEO-optimized pin description."""
        rating_stars = "⭐" * int(product.rating)

        description = f"""✨ {product.title[:100]}

{rating_stars} {product.rating} stars | {product.review_count:,}+ reviews
💰 Only ${product.price:.2f}

👉 Get yours now!

#amazonfinds #{product.category.replace('-', '').replace(' ', '')} #musthave #deals #shopping"""

        return description

    async def status(self) -> dict:
        """Get account manager status."""
        today = datetime.utcnow().date()
        posts_today = (
            self.db.query(Post)
            .filter(Post.posted_at >= datetime(today.year, today.month, today.day))
            .count()
        )

        return {
            "agent": self.name,
            "posts_today": posts_today,
            "target_posts": self.posts_per_day,
            "boards_count": len(self.boards),
            "next_posting_time": self._next_posting_time()
        }

    def _next_posting_time(self) -> str:
        """Calculate next posting time."""
        now = datetime.now()
        current_time = now.strftime("%H:%M")

        for time_str in self.posting_times:
            if time_str > current_time:
                return time_str

        return self.posting_times[0]  # First time tomorrow
