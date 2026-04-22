"""
Reddit Source Integration
=========================

Reads public `.json` endpoints (no OAuth required) to surface what's trending
on Reddit. Covers r/popular (cross-sub viral), r/news, r/technology, etc.

Why this matters: Reddit's front page is a reasonable proxy for "what's
breaking out on US social media right now" — cheaper and more reliable than
scraping TikTok/Instagram. Stories usually hit Reddit before they hit
mainstream news. The score/comment count gives us an objective viral signal.

Config schema (YAML):
    - name: "Reddit r/popular"
      type: "reddit"
      subreddit: "popular"     # any subreddit name
      listing: "hot"           # hot | top | rising
      timeframe: "day"         # only for listing=top: hour/day/week/month
      min_score: 1000          # filter low-engagement posts
      enabled: true
"""

import hashlib
import logging
from datetime import datetime
from typing import Any, Dict, List

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    logging.warning("httpx not installed. Reddit source unavailable.")

from .base_source import BaseSourceIntegration
from ..trend_service import TrendingNews


class RedditSource(BaseSourceIntegration):
    """Reddit trends via public .json endpoints."""

    # Reddit requires a descriptive User-Agent or returns 429/403.
    # Using a generic bot UA is fine — the endpoints are public.
    # Phase M (2026-04-22): more specific UA. Reddit has tightened on
    # generic/bot-shaped UAs and rate-limits them harder. Format matches
    # Reddit's API docs recommendation: "<platform>:<app ID>:<version>
    # (by /u/<reddit username>)".
    DEFAULT_USER_AGENT = (
        "web:jesse-automation:v1.0 (by github.com/camilleyeyou/Jesse-Automation)"
    )

    def __init__(self, config: Dict[str, Any], tier: int = 3):
        super().__init__(config, tier)

        if not HTTPX_AVAILABLE:
            raise ImportError("httpx required for Reddit sources")

        self.subreddit = config.get("subreddit", "popular")
        self.listing = config.get("listing", "hot")  # hot | top | rising
        self.timeframe = config.get("timeframe", "day")  # for top: hour/day/week/month/year/all
        self.min_score = int(config.get("min_score", 1000))
        self.user_agent = config.get("user_agent", self.DEFAULT_USER_AGENT)

    async def fetch(self, limit: int = 10) -> List[TrendingNews]:
        if not self.enabled:
            return []

        url = f"https://www.reddit.com/r/{self.subreddit}/{self.listing}.json"
        params: Dict[str, Any] = {"limit": max(25, limit * 3)}  # overfetch to filter
        if self.listing == "top":
            params["t"] = self.timeframe

        headers = {"User-Agent": self.user_agent}

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                r = await client.get(url, params=params, headers=headers)
                if r.status_code == 429:
                    self.logger.warning(f"Reddit rate-limited for r/{self.subreddit}")
                    return []
                r.raise_for_status()
                data = r.json()
        except Exception as e:
            self.logger.error(f"Reddit fetch failed for r/{self.subreddit}: {e}")
            raise

        children = data.get("data", {}).get("children", [])
        trends: List[TrendingNews] = []

        for child in children:
            post = child.get("data", {})

            # Skip noise: stickied mod posts, NSFW, spoilers, deleted
            if post.get("stickied") or post.get("over_18") or post.get("spoiler"):
                continue
            if not post.get("title") or post.get("title") == "[deleted]":
                continue
            # Skip low-engagement — Reddit's "popular" can still have sub-500 posts
            if int(post.get("score", 0)) < self.min_score:
                continue

            trends.append(self._to_trend(post))
            if len(trends) >= limit:
                break

        self.logger.info(
            f"Fetched {len(trends)} Reddit posts from r/{self.subreddit}/{self.listing}"
        )
        return trends

    def _to_trend(self, post: Dict[str, Any]) -> TrendingNews:
        title = post.get("title", "").strip()
        subreddit = post.get("subreddit", "")
        score = int(post.get("score", 0))
        num_comments = int(post.get("num_comments", 0))
        permalink = post.get("permalink", "")
        url = f"https://www.reddit.com{permalink}" if permalink else post.get("url", "")

        # Prefer the linked article URL over the Reddit thread for sourcing.
        # The post's `url` field is the link target for link-posts; for
        # self-posts it's the Reddit permalink.
        article_url = post.get("url_overridden_by_dest") or post.get("url") or url

        # Self-post body if present (capped)
        selftext = (post.get("selftext") or "").strip()[:500]
        external_domain = post.get("domain", "")

        summary_parts = [f"r/{subreddit} • {score:,} upvotes • {num_comments:,} comments"]
        if external_domain and not external_domain.startswith("self."):
            summary_parts.append(f"via {external_domain}")
        if selftext:
            summary_parts.append(selftext)

        summary = " — ".join(summary_parts)

        fingerprint = hashlib.md5(f"{title}_{permalink}".encode()).hexdigest()[:16]

        # Viral indicators driven by objective Reddit signals
        viral_indicators: List[str] = [f"reddit_score_{score}", f"reddit_comments_{num_comments}"]
        if score >= 10000:
            viral_indicators.append("reddit_viral_10k")
        if num_comments >= 1000:
            viral_indicators.append("reddit_discussion_heavy")
        if post.get("upvote_ratio", 1.0) < 0.7:
            viral_indicators.append("reddit_controversial")

        trend = TrendingNews(
            headline=title,
            summary=summary[:500],
            source=f"reddit/{subreddit}",
            url=article_url,
            category="social_pulse",
            fingerprint=fingerprint,
            description=summary[:1000],
            related_articles=[],
            jesse_angle="",
            news_freshness="today",
            # Theme/tier metadata
            theme="",
            sub_theme="",
            tier=self.tier,
            tier_label=self._get_tier_label(),
            source_type="reddit_json",
            confidence_score=0.0,
            detected_at=datetime.utcnow().isoformat(),
            viral_indicators=viral_indicators,
        )
        # Phase B (2026-04-20): attach raw Reddit upvote score as a
        # numeric social-velocity signal for the curator. 1000+ is
        # moderate social lift; 10000+ is viral-class.
        try:
            setattr(trend, "social_velocity_score", score)
            setattr(trend, "social_velocity_source", "reddit")
            setattr(trend, "social_comment_count", num_comments)
        except Exception:
            pass
        return trend

    async def health_check(self) -> bool:
        try:
            url = f"https://www.reddit.com/r/{self.subreddit}/hot.json"
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.get(
                    url,
                    params={"limit": 1},
                    headers={"User-Agent": self.user_agent},
                )
                return r.status_code == 200
        except Exception as e:
            self.logger.warning(f"Reddit health check failed: {e}")
            return False
