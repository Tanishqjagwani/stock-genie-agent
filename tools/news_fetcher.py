from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Dict, List
from urllib.parse import quote_plus

import feedparser
import requests

from config.sectors import SECTORS
from config.settings import NEWS_API_KEY, NEWS_DAYS_BACK
from models.schemas import NewsArticle

logger = logging.getLogger(__name__)


def fetch_newsapi_articles(query: str, days_back: int = NEWS_DAYS_BACK) -> List[dict]:
    """Fetch articles from NewsAPI.org."""
    if not NEWS_API_KEY:
        logger.warning("NEWS_API_KEY not set, skipping NewsAPI")
        return []

    from_date = (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "from": from_date,
        "sortBy": "relevancy",
        "pageSize": 5,
        "language": "en",
        "apiKey": NEWS_API_KEY,
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        articles = resp.json().get("articles", [])
        return [
            NewsArticle(
                title=a.get("title", ""),
                source=a.get("source", {}).get("name", ""),
                url=a.get("url", ""),
                published=a.get("publishedAt", ""),
            ).model_dump()
            for a in articles
            if a.get("title")
        ]
    except Exception as e:
        logger.warning(f"NewsAPI fetch failed for '{query}': {e}")
        return []


def fetch_google_news_rss(query: str) -> List[dict]:
    """Fetch articles from Google News RSS (no API key needed)."""
    try:
        url = f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=en-US&gl=US&ceid=US:en"
        feed = feedparser.parse(url)
        articles = []
        for entry in feed.entries[:5]:
            articles.append(
                NewsArticle(
                    title=entry.get("title", ""),
                    source=entry.get("source", {}).get("title", "Google News"),
                    url=entry.get("link", ""),
                    published=entry.get("published", ""),
                ).model_dump()
            )
        return articles
    except Exception as e:
        logger.warning(f"Google News RSS failed for '{query}': {e}")
        return []


def fetch_news_for_sectors(sectors: dict = SECTORS) -> Dict[str, List[dict]]:
    """Fetch news for each sector using both NewsAPI and Google News RSS."""
    sector_news: Dict[str, List[dict]] = {}
    for sector, meta in sectors.items():
        articles: List[dict] = []
        for query in meta["news_queries"]:
            articles.extend(fetch_newsapi_articles(query))
            articles.extend(fetch_google_news_rss(query))
        # Deduplicate by title
        seen: set = set()
        unique: List[dict] = []
        for a in articles:
            if a["title"] not in seen:
                seen.add(a["title"])
                unique.append(a)
        sector_news[sector] = unique[:10]
        logger.info(f"Fetched {len(sector_news[sector])} articles for {sector}")
    return sector_news


def fetch_geopolitical_news() -> List[dict]:
    """Fetch geopolitical/macro news that affects markets."""
    queries = [
        "geopolitical conflict trade war sanctions",
        "central bank interest rate decision",
        "tariffs trade policy",
        "military escalation economy",
    ]
    articles: List[dict] = []
    for query in queries:
        articles.extend(fetch_newsapi_articles(query))
        articles.extend(fetch_google_news_rss(query))

    seen: set = set()
    unique: List[dict] = []
    for a in articles:
        if a["title"] not in seen:
            seen.add(a["title"])
            unique.append(a)

    logger.info(f"Fetched {len(unique)} geopolitical news articles")
    return unique[:15]
