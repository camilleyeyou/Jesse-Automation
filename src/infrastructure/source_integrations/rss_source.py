"""
RSS Source Integration
======================

Generic RSS feed reader for HuggingFace, arXiv, blogs, and other RSS sources.

Supports:
- HuggingFace Daily Papers
- Simon Willison Blog
- arXiv feeds
- Policy/research institution feeds (CSET, AI Now, etc.)
"""

import logging
from typing import List, Dict, Any
from datetime import datetime
import hashlib

try:
    import feedparser
    FEEDPARSER_AVAILABLE = True
except ImportError:
    FEEDPARSER_AVAILABLE = False
    logging.warning("feedparser not installed. Run: pip install feedparser")

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

from .base_source import BaseSourceIntegration
from ..trend_service import TrendingNews


class RSSSource(BaseSourceIntegration):
    """
    Generic RSS feed reader.

    Configuration:
        {
            "name": "Source Name",
            "type": "rss",
            "url": "https://example.com/feed.xml",
            "enabled": True
        }

    Usage:
        source = RSSSource(config, tier=1)
        trends = await source.fetch(limit=10)
    """

    def __init__(self, config: Dict[str, Any], tier: int = 3):
        super().__init__(config, tier)

        if not FEEDPARSER_AVAILABLE:
            raise ImportError("feedparser required for RSS sources. Install: pip install feedparser")

        self.feed_url = config.get("url", "")
        if not self.feed_url:
            raise ValueError(f"RSS source {self.source_name} missing 'url' in config")

    async def fetch(self, limit: int = 10) -> List[TrendingNews]:
        """Fetch trends from RSS feed"""

        if not self.enabled:
            return []

        try:
            # Parse RSS feed
            self.logger.debug(f"Fetching RSS feed: {self.feed_url}")
            feed = feedparser.parse(self.feed_url)

            if feed.bozo and feed.bozo_exception:
                raise Exception(f"RSS parse error: {feed.bozo_exception}")

            trends = []
            entries = feed.entries[:limit]

            for entry in entries:
                try:
                    trend = self._parse_entry(entry)
                    trends.append(trend)
                except Exception as e:
                    self.logger.warning(f"Failed to parse RSS entry: {e}")
                    continue

            self.logger.info(f"Fetched {len(trends)} trends from {self.source_name}")
            return trends

        except Exception as e:
            self.logger.error(f"RSS fetch failed: {e}")
            raise

    def _parse_entry(self, entry) -> TrendingNews:
        """Parse single RSS entry into TrendingNews"""

        # Extract fields
        headline = entry.get('title', 'Untitled')

        # Try multiple summary fields (different RSS formats)
        summary = (
            entry.get('summary', '') or
            entry.get('description', '') or
            entry.get('content', [{}])[0].get('value', '') if entry.get('content') else ''
        )

        # Clean HTML from summary if present
        if summary:
            summary = self._clean_html(summary)[:500]

        url = entry.get('link', '')

        # Parse published date
        published = entry.get('published', entry.get('updated', ''))
        freshness = self._calculate_freshness(published)

        # Generate fingerprint
        fingerprint_text = f"{headline}_{summary[:100]}"
        fingerprint = hashlib.md5(fingerprint_text.encode()).hexdigest()

        # Extract author if available
        author = entry.get('author', '')

        # Build description
        description = summary
        if author:
            description = f"By {author}. {summary}"

        # Detect viral indicators based on source type
        viral_indicators = self._detect_viral_indicators(headline, summary)

        return TrendingNews(
            headline=headline,
            summary=summary,
            source=self.source_name,
            url=url,
            category=self._infer_category(headline, summary),
            fingerprint=fingerprint,
            description=description[:1000],
            related_articles=[],
            jesse_angle="",
            news_freshness=freshness,
            # Theme/tier metadata
            theme="",  # Will be classified later
            sub_theme="",
            tier=self.tier,
            tier_label=self._get_tier_label(),
            source_type="rss",
            confidence_score=0.0,
            detected_at=datetime.utcnow().isoformat(),
            viral_indicators=viral_indicators
        )

    def _clean_html(self, text: str) -> str:
        """Remove HTML tags from text"""
        import re
        # Simple HTML tag removal
        clean = re.sub(r'<[^>]+>', '', text)
        # Clean up whitespace
        clean = re.sub(r'\s+', ' ', clean).strip()
        return clean

    def _calculate_freshness(self, published_str: str) -> str:
        """Calculate how fresh the content is"""
        if not published_str:
            return "unknown"

        try:
            from dateutil import parser as date_parser
            published = date_parser.parse(published_str)
            now = datetime.now(published.tzinfo)
            delta = now - published

            if delta.days == 0:
                return "today"
            elif delta.days == 1:
                return "yesterday"
            elif delta.days <= 7:
                return "this_week"
            elif delta.days <= 30:
                return "this_month"
            else:
                return "older"
        except Exception:
            return "unknown"

    def _infer_category(self, headline: str, summary: str) -> str:
        """Infer category from content"""
        text = f"{headline} {summary}".lower()

        # Simple keyword-based categorization
        if any(word in text for word in ['paper', 'research', 'study', 'arxiv']):
            return "research"
        elif any(word in text for word in ['policy', 'regulation', 'government', 'law']):
            return "policy"
        elif any(word in text for word in ['release', 'launch', 'announce', 'update']):
            return "product"
        elif any(word in text for word in ['layoff', 'hire', 'job', 'workforce']):
            return "labor"
        else:
            return "trending"

    def _detect_viral_indicators(self, headline: str, summary: str) -> List[str]:
        """Detect signals of viral potential"""
        text = f"{headline} {summary}".lower()
        indicators = []

        # Check for viral keywords
        viral_keywords = {
            'breakthrough': 'breakthrough',
            'crisis': 'crisis',
            'record': 'record_breaking',
            'unprecedented': 'unprecedented',
            'shocking': 'shocking',
            'leaked': 'leaked',
            'exclusive': 'exclusive',
        }

        for keyword, indicator in viral_keywords.items():
            if keyword in text:
                indicators.append(indicator)

        # Check for numbers (concrete stats are more shareable)
        import re
        if re.search(r'\d+%|\$\d+[BMK]|\d+x', text):
            indicators.append('concrete_numbers')

        return indicators

    async def health_check(self) -> bool:
        """Check if RSS feed is accessible"""
        try:
            if not HTTPX_AVAILABLE:
                # Fallback to feedparser's built-in fetch
                feed = feedparser.parse(self.feed_url)
                return not feed.bozo or len(feed.entries) > 0

            # Use httpx for faster health check
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.feed_url)
                return response.status_code == 200
        except Exception as e:
            self.logger.warning(f"Health check failed: {e}")
            return False


class HuggingFaceSource(RSSSource):
    """
    HuggingFace Daily Papers RSS feed.

    Specialization of RSSSource with HuggingFace-specific parsing.
    """

    def _parse_entry(self, entry) -> TrendingNews:
        """Parse HuggingFace paper entry"""
        trend = super()._parse_entry(entry)

        # Override category for research papers
        trend.category = "research"

        # Add HuggingFace-specific viral indicators
        if 'huggingface' in trend.url.lower():
            trend.viral_indicators.append('huggingface_featured')

        return trend


class ArxivSource(RSSSource):
    """
    arXiv RSS feed.

    Specialization of RSSSource with arXiv-specific parsing.
    """

    def _parse_entry(self, entry) -> TrendingNews:
        """Parse arXiv paper entry"""
        trend = super()._parse_entry(entry)

        # Override category for academic papers
        trend.category = "research"
        trend.viral_indicators.append('academic_paper')

        # Extract arXiv ID if present
        if 'arxiv.org' in trend.url:
            import re
            match = re.search(r'arxiv\.org/abs/(\d+\.\d+)', trend.url)
            if match:
                arxiv_id = match.group(1)
                trend.description = f"arXiv:{arxiv_id}. {trend.description}"

        return trend
