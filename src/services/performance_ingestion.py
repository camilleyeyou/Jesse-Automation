"""
Performance Ingestion Service
==============================

Fetches LinkedIn post analytics and writes engagement data to content_memory.

Runs weekly (Sunday 6:00 AM) via APScheduler to populate the data foundation
that feeds the Strategic Brain (Phase 2) and Learning System (Phase 3).

LinkedIn API endpoints used:
- GET /v2/organizationalEntityShareStatistics — post-level engagement stats
- GET /v2/socialActions/{shareUrn} — comment/reaction counts
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from urllib.parse import quote

import requests

logger = logging.getLogger(__name__)


class PerformanceIngestionService:
    """
    Fetches post-level engagement metrics from LinkedIn API
    and writes them to content_memory for the learning system.
    """

    def __init__(self, memory, access_token: str = None, company_id: str = None):
        """
        Args:
            memory: AgentMemory instance (for reading posts + writing engagement)
            access_token: LinkedIn API access token
            company_id: LinkedIn organization/company ID
        """
        self.memory = memory
        self.access_token = access_token or os.getenv("LINKEDIN_ACCESS_TOKEN")
        self.company_id = company_id or os.getenv("LINKEDIN_COMPANY_ID")
        self.api_base = "https://api.linkedin.com/v2"

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "X-Restli-Protocol-Version": "2.0.0",
        }

    def is_configured(self) -> bool:
        return bool(self.access_token)

    async def run(self) -> Dict[str, Any]:
        """
        Main entry point — fetch engagement for all published posts
        that haven't been updated recently.

        Returns summary of what was fetched.
        """
        logger.info("=" * 60)
        logger.info("📊 PERFORMANCE INGESTION — Fetching LinkedIn analytics")
        logger.info("=" * 60)

        if not self.is_configured():
            logger.warning("LinkedIn access token not configured — skipping ingestion")
            return {"success": False, "error": "not_configured", "updated": 0}

        # Get posts that need engagement data
        posts = self.memory.get_posts_needing_engagement(min_age_hours=24)

        if not posts:
            logger.info("No posts need engagement updates")
            return {"success": True, "updated": 0, "skipped": 0, "errors": 0}

        logger.info(f"Found {len(posts)} posts needing engagement data")

        updated = 0
        skipped = 0
        errors = 0

        for post in posts:
            linkedin_post_id = post.get("linkedin_post_id")
            if not linkedin_post_id:
                skipped += 1
                continue

            try:
                engagement = await asyncio.to_thread(self._fetch_post_engagement, linkedin_post_id)
                if engagement:
                    self.memory.update_post_engagement(
                        linkedin_post_id=linkedin_post_id,
                        reactions=engagement.get("reactions", 0),
                        comments=engagement.get("comments", 0),
                        shares=engagement.get("shares", 0),
                        impressions=engagement.get("impressions", 0),
                    )
                    updated += 1
                    logger.info(
                        f"  ✅ {linkedin_post_id[:40]}... "
                        f"r={engagement['reactions']} c={engagement['comments']} "
                        f"s={engagement['shares']} i={engagement['impressions']}"
                    )
                else:
                    skipped += 1
            except Exception as e:
                logger.error(f"  ❌ Failed for {linkedin_post_id}: {e}")
                errors += 1

        summary = {
            "success": True,
            "updated": updated,
            "skipped": skipped,
            "errors": errors,
            "total_posts": len(posts),
            "timestamp": datetime.utcnow().isoformat(),
        }
        logger.info(f"📊 Ingestion complete: {updated} updated, {skipped} skipped, {errors} errors")
        return summary

    def _fetch_post_engagement(self, post_urn: str) -> Optional[Dict[str, int]]:
        """
        Fetch engagement metrics for a single post from the LinkedIn API.

        Tries two approaches:
        1. organizationalEntityShareStatistics (org-level, richer data)
        2. socialActions (fallback, works for personal posts too)
        """
        # Try org-level stats first (gives impressions)
        if self.company_id:
            stats = self._fetch_org_share_statistics(post_urn)
            if stats:
                return stats

        # Fallback to socialActions endpoint
        return self._fetch_social_actions(post_urn)

    def _fetch_org_share_statistics(self, post_urn: str) -> Optional[Dict[str, int]]:
        """
        Fetch via organizationalEntityShareStatistics.
        Returns reactions, comments, shares, impressions.
        """
        try:
            org_urn = f"urn:li:organization:{self.company_id}"
            encoded_org = quote(org_urn, safe="")
            encoded_share = quote(post_urn, safe="")

            url = (
                f"{self.api_base}/organizationalEntityShareStatistics"
                f"?q=organizationalEntity"
                f"&organizationalEntity={encoded_org}"
                f"&shares[0]={encoded_share}"
            )

            response = requests.get(url, headers=self._headers(), timeout=15)

            if response.status_code != 200:
                logger.debug(f"Org stats API returned {response.status_code}")
                return None

            data = response.json()
            elements = data.get("elements", [])
            if not elements:
                return None

            stats = elements[0].get("totalShareStatistics", {})
            return {
                "reactions": stats.get("likeCount", 0),
                "comments": stats.get("commentCount", 0),
                "shares": stats.get("shareCount", 0),
                "impressions": stats.get("impressionCount", 0),
            }

        except Exception as e:
            logger.debug(f"Org stats fetch failed: {e}")
            return None

    def _fetch_social_actions(self, post_urn: str) -> Optional[Dict[str, int]]:
        """
        Fetch via socialActions endpoint.
        Returns reactions, comments (no impressions available here).
        """
        try:
            encoded_urn = quote(post_urn, safe="")
            url = f"{self.api_base}/socialActions/{encoded_urn}"

            response = requests.get(url, headers=self._headers(), timeout=15)

            if response.status_code != 200:
                logger.debug(f"Social actions API returned {response.status_code}")
                return None

            data = response.json()
            likes_summary = data.get("likesSummary", {})
            comments_summary = data.get("commentsSummary", {})

            return {
                "reactions": likes_summary.get("totalLikes", 0),
                "comments": comments_summary.get("totalFirstLevelComments", 0),
                "shares": 0,  # Not available via this endpoint
                "impressions": 0,  # Not available via this endpoint
            }

        except Exception as e:
            logger.debug(f"Social actions fetch failed: {e}")
            return None
