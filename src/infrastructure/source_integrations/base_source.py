"""
Base Source Integration
========================

Abstract base class for all content source integrations.

Provides standard interface for fetching trends from various sources:
- RSS feeds (HuggingFace, arXiv, blogs)
- APIs (Reddit, Twitter)
- Web scraping (Techmeme)
- Newsletters (future)
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging

# Import TrendingNews from parent module
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from infrastructure.trend_service import TrendingNews


@dataclass
class SourceHealth:
    """Health status of a content source"""
    source_name: str
    is_healthy: bool
    last_fetch_success: bool
    last_error: Optional[str] = None
    fetch_count: int = 0
    success_count: int = 0

    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.fetch_count == 0:
            return 1.0
        return self.success_count / self.fetch_count


class BaseSourceIntegration(ABC):
    """
    Abstract base class for all content source integrations.

    Subclasses must implement:
    - fetch(): Retrieve trends from the source
    - health_check(): Verify source is accessible
    - transform_to_trending_news(): Convert raw data to TrendingNews

    Usage:
        class MySource(BaseSourceIntegration):
            async def fetch(self) -> List[TrendingNews]:
                # Fetch and return trends
                pass

            async def health_check(self) -> bool:
                # Check if source is accessible
                pass
    """

    def __init__(self, config: Dict[str, Any], tier: int = 3):
        """
        Initialize source integration.

        Args:
            config: Source configuration (url, api_key, etc.)
            tier: Sourcing tier (1-4)
        """
        self.config = config
        self.tier = tier
        self.source_name = config.get("name", self.__class__.__name__)
        self.source_type = config.get("type", "unknown")
        self.enabled = config.get("enabled", False)

        self.logger = logging.getLogger(f"source.{self.source_name}")

        # Health tracking
        self._fetch_count = 0
        self._success_count = 0
        self._last_error = None

    @abstractmethod
    async def fetch(self, limit: int = 10) -> List[TrendingNews]:
        """
        Fetch trends from the source.

        Args:
            limit: Maximum number of trends to fetch

        Returns:
            List of TrendingNews objects

        Raises:
            Exception if fetch fails
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if source is accessible and healthy.

        Returns:
            True if source is healthy, False otherwise
        """
        pass

    def transform_to_trending_news(
        self,
        raw_data: Dict[str, Any],
        source_label: str = None
    ) -> TrendingNews:
        """
        Convert raw source data to TrendingNews object.

        Override this method if source data format is non-standard.

        Args:
            raw_data: Raw data dict from source
            source_label: Optional source override

        Returns:
            TrendingNews object
        """
        from datetime import datetime
        import hashlib

        headline = raw_data.get("title", raw_data.get("headline", ""))
        summary = raw_data.get("summary", raw_data.get("description", ""))
        url = raw_data.get("url", raw_data.get("link", ""))

        # Generate fingerprint
        fingerprint_text = f"{headline}_{summary[:100]}"
        fingerprint = hashlib.md5(fingerprint_text.encode()).hexdigest()

        return TrendingNews(
            headline=headline,
            summary=summary[:500] if summary else "",
            source=source_label or self.source_name,
            url=url,
            category=raw_data.get("category", "trending"),
            fingerprint=fingerprint,
            description=raw_data.get("description", summary)[:1000],
            related_articles=[],
            jesse_angle="",
            news_freshness=raw_data.get("freshness", "today"),
            # Theme/tier metadata
            theme="",  # Will be classified later
            sub_theme="",
            tier=self.tier,
            tier_label=self._get_tier_label(),
            source_type=self.source_type,
            confidence_score=0.0,
            detected_at=datetime.utcnow().isoformat(),
            viral_indicators=raw_data.get("viral_indicators", [])
        )

    def _get_tier_label(self) -> str:
        """Get human-readable tier label"""
        tier_labels = {
            1: "early_detection",
            2: "editorial_filter",
            3: "cultural_pickup",
            4: "policy_institutional"
        }
        return tier_labels.get(self.tier, "unknown")

    def get_tier(self) -> int:
        """Get source tier (1-4)"""
        return self.tier

    def get_refresh_rate(self) -> int:
        """Get refresh rate in minutes"""
        return self.config.get("refresh_minutes", 60)

    def is_enabled(self) -> bool:
        """Check if source is enabled"""
        return self.enabled

    def record_fetch_attempt(self, success: bool, error: str = None):
        """Record fetch attempt for health tracking"""
        self._fetch_count += 1
        if success:
            self._success_count += 1
            self._last_error = None
        else:
            self._last_error = error
            self.logger.warning(f"Fetch failed: {error}")

    def get_health_status(self) -> SourceHealth:
        """Get current health status"""
        return SourceHealth(
            source_name=self.source_name,
            is_healthy=self._success_count / max(self._fetch_count, 1) > 0.5,
            last_fetch_success=self._last_error is None,
            last_error=self._last_error,
            fetch_count=self._fetch_count,
            success_count=self._success_count
        )

    async def fetch_with_health_tracking(self, limit: int = 10) -> List[TrendingNews]:
        """
        Fetch with automatic health tracking.

        Wraps fetch() with error handling and health metrics.
        """
        try:
            if not self.enabled:
                self.logger.debug(f"Source {self.source_name} is disabled")
                return []

            trends = await self.fetch(limit)
            self.record_fetch_attempt(success=True)
            self.logger.info(f"Fetched {len(trends)} trends from {self.source_name}")
            return trends

        except Exception as e:
            self.record_fetch_attempt(success=False, error=str(e))
            self.logger.error(f"Fetch failed for {self.source_name}: {e}")
            return []

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} tier={self.tier} enabled={self.enabled}>"
