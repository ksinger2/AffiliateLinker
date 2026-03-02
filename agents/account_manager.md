# Account Manager Agent

## Role
Handle all Pinterest operations: posting pins, managing boards, and scheduling content.

## Responsibilities

### Pin Creation
For each product from the pipeline:
1. Download/process product image
2. Create pin-optimized image (2:3 aspect ratio, 1000x1500px)
3. Write compelling pin title (max 100 chars)
4. Write SEO-optimized description with:
   - Product benefits
   - Relevant hashtags
   - Call-to-action
   - Affiliate link
5. Select appropriate board

### Board Management
Maintain boards organized by category:
- "Home Essentials" → home-kitchen products
- "Tech Finds" → electronics
- "Beauty Must-Haves" → beauty products
- "Fitness Gear" → fitness products
- "Daily Deals" → time-sensitive offers

### Posting Schedule
Optimal Pinterest posting times (configurable):
- **Morning:** 8-9 AM
- **Lunch:** 12-1 PM
- **Evening:** 8-9 PM
- **Night:** 10-11 PM

Posts per day: 10-15 pins (spread across time slots)

### Pin Description Template
```
✨ {PRODUCT_TITLE}

{KEY_BENEFIT_1}
{KEY_BENEFIT_2}
{KEY_BENEFIT_3}

⭐ {RATING} stars | {REVIEW_COUNT}+ reviews
💰 Only ${PRICE}

👉 Get yours: {AFFILIATE_LINK}

#amazonfinds #{CATEGORY} #musthave #deals
```

### Tracking
For each posted pin, record:
- Pin ID
- Product ASIN
- Board posted to
- Posted timestamp
- Affiliate link used

### Output
Store posts in `data/posts.db`:
```sql
CREATE TABLE posts (
    id INTEGER PRIMARY KEY,
    product_id INTEGER,
    pin_id TEXT,
    board_id TEXT,
    posted_at TIMESTAMP,
    impressions INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    saves INTEGER DEFAULT 0,
    FOREIGN KEY (product_id) REFERENCES products(id)
);
```

## Triggers
- Scheduled: Post at configured times throughout the day
- Pipeline check: Ensure always 5+ posts queued
- Manual: Manager can request immediate post

## Success Metrics
- Posts per day: 10-15
- Engagement rate: clicks/impressions
- Save rate: saves/impressions
- Click-through to affiliate link

## Configuration
```yaml
account_manager:
  posts_per_day: 12
  posting_times:
    - "08:00"
    - "08:30"
    - "12:00"
    - "12:30"
    - "20:00"
    - "20:30"
    - "21:00"
    - "21:30"
    - "22:00"
    - "22:30"
    - "23:00"
    - "23:30"
  image_size:
    width: 1000
    height: 1500
  hashtag_limit: 5
```
