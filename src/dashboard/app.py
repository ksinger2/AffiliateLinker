"""Streamlit Dashboard for AffiliateLinker."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
sys.path.insert(0, "../..")

from src.database import get_session, Product, Post, Metric, SystemLog

st.set_page_config(
    page_title="AffiliateLinker Dashboard",
    page_icon="📌",
    layout="wide"
)

# Database session
db = get_session()


def main():
    st.title("📌 AffiliateLinker Dashboard")
    st.markdown("---")

    # Sidebar
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", [
        "Overview",
        "Products",
        "Posts",
        "Performance",
        "System Logs"
    ])

    if page == "Overview":
        show_overview()
    elif page == "Products":
        show_products()
    elif page == "Posts":
        show_posts()
    elif page == "Performance":
        show_performance()
    elif page == "System Logs":
        show_logs()


def show_overview():
    """Show overview dashboard."""
    st.header("System Overview")

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    total_products = db.query(Product).count()
    pending_products = db.query(Product).filter_by(status="pending").count()
    total_posts = db.query(Post).count()
    total_clicks = sum(p.clicks or 0 for p in db.query(Post).all())

    col1.metric("Total Products", total_products)
    col2.metric("Pending", pending_products)
    col3.metric("Total Posts", total_posts)
    col4.metric("Total Clicks", total_clicks)

    st.markdown("---")

    # Recent activity
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Recent Products")
        recent_products = (
            db.query(Product)
            .order_by(Product.discovered_at.desc())
            .limit(5)
            .all()
        )
        for p in recent_products:
            st.write(f"**{p.title[:50]}...** - ${p.price:.2f}")

    with col2:
        st.subheader("Recent Posts")
        recent_posts = (
            db.query(Post)
            .order_by(Post.posted_at.desc())
            .limit(5)
            .all()
        )
        for post in recent_posts:
            st.write(f"**{post.pin_title[:40]}...** - {post.clicks or 0} clicks")


def show_products():
    """Show products table."""
    st.header("Product Pipeline")

    # Filters
    status_filter = st.selectbox("Status", ["All", "pending", "approved", "posted", "rejected"])

    query = db.query(Product)
    if status_filter != "All":
        query = query.filter_by(status=status_filter)

    products = query.order_by(Product.discovered_at.desc()).all()

    if products:
        df = pd.DataFrame([
            {
                "ASIN": p.asin,
                "Title": p.title[:50] + "..." if len(p.title) > 50 else p.title,
                "Price": f"${p.price:.2f}",
                "Rating": f"{p.rating} ⭐",
                "Reviews": p.review_count,
                "Status": p.status,
                "Commission": f"{(p.commission_rate or 0) * 100:.1f}%"
            }
            for p in products
        ])
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No products found")


def show_posts():
    """Show posts and engagement."""
    st.header("Pinterest Posts")

    posts = db.query(Post).order_by(Post.posted_at.desc()).all()

    if posts:
        df = pd.DataFrame([
            {
                "Pin ID": post.pin_id,
                "Title": post.pin_title[:40] + "..." if post.pin_title and len(post.pin_title) > 40 else post.pin_title,
                "Board": post.board_name,
                "Posted": post.posted_at.strftime("%Y-%m-%d %H:%M") if post.posted_at else "",
                "Impressions": post.impressions or 0,
                "Clicks": post.clicks or 0,
                "Saves": post.saves or 0,
                "CTR": f"{(post.clicks or 0) / max(post.impressions or 1, 1) * 100:.2f}%"
            }
            for post in posts
        ])
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No posts yet")


def show_performance():
    """Show performance charts."""
    st.header("Performance Analytics")

    metrics = db.query(Metric).order_by(Metric.date.desc()).limit(30).all()

    if metrics:
        df = pd.DataFrame([
            {
                "Date": m.date,
                "Products": m.products_discovered,
                "Posts": m.posts_made,
                "Impressions": m.total_impressions,
                "Clicks": m.total_clicks,
                "Saves": m.total_saves
            }
            for m in metrics
        ])

        # Impressions over time
        fig1 = px.line(df, x="Date", y="Impressions", title="Impressions Over Time")
        st.plotly_chart(fig1, use_container_width=True)

        # Clicks and saves
        fig2 = px.bar(df, x="Date", y=["Clicks", "Saves"], barmode="group", title="Engagement")
        st.plotly_chart(fig2, use_container_width=True)

        # Posts per day
        fig3 = px.bar(df, x="Date", y="Posts", title="Posts Per Day")
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("No metrics recorded yet")


def show_logs():
    """Show system logs."""
    st.header("System Logs")

    level_filter = st.selectbox("Level", ["All", "INFO", "WARNING", "ERROR"])

    query = db.query(SystemLog)
    if level_filter != "All":
        query = query.filter_by(level=level_filter)

    logs = query.order_by(SystemLog.timestamp.desc()).limit(100).all()

    if logs:
        for log in logs:
            level_color = {
                "INFO": "blue",
                "WARNING": "orange",
                "ERROR": "red"
            }.get(log.level, "gray")

            st.markdown(
                f"**:{level_color}[{log.level}]** `{log.timestamp}` "
                f"[{log.agent}] {log.action}: {log.details}"
            )
    else:
        st.info("No logs found")


if __name__ == "__main__":
    main()
