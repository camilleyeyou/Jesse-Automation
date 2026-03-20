"""
PositionExtractor — Lightweight agent that extracts Jesse's position from a post.

Runs AFTER a post is approved (before posting to LinkedIn) to capture:
- position_summary: 1-2 sentence summary of the argument
- sentiment: one of [celebrate, critique, warn, question, encourage, observe]
- key_claim: the core claim in one sentence

Uses GPT-4o-mini for speed and cost efficiency. Designed to never block posting
on failure — returns None gracefully on any error.
"""

import json
import logging
from typing import Dict, Any, Optional

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class PositionExtractor(BaseAgent):
    """
    Extracts the position/stance Jesse took in a piece of content.
    Lightweight, fast, and fault-tolerant.
    """

    VALID_SENTIMENTS = {"celebrate", "critique", "warn", "question", "encourage", "observe"}

    def __init__(self, ai_client, config, **kwargs):
        super().__init__(
            ai_client=ai_client,
            config=config,
            name="PositionExtractor"
        )
        self.logger.info("PositionExtractor initialized")

    async def execute(
        self,
        post_content: str,
        theme: str = None,
        topic: str = None,
        **kwargs,
    ) -> Optional[Dict[str, str]]:
        """
        Extract position from a post.

        Args:
            post_content: The full post text
            theme: The content theme (e.g. 'ai_workplace')
            topic: The specific topic or trending headline

        Returns:
            Dict with 'position_summary', 'sentiment', 'key_claim' — or None on failure.
        """
        if not post_content or not post_content.strip():
            self.logger.warning("Empty post content — skipping position extraction")
            return None

        try:
            result = await self._extract(post_content, theme, topic)
            if result:
                # Validate sentiment
                if result.get("sentiment") not in self.VALID_SENTIMENTS:
                    result["sentiment"] = "observe"
                self.logger.info(
                    f"Extracted position: sentiment={result.get('sentiment')}, "
                    f"claim={result.get('key_claim', '')[:60]}..."
                )
            return result
        except Exception as e:
            self.logger.warning(f"Position extraction failed (non-blocking): {e}")
            return None

    async def _extract(
        self,
        post_content: str,
        theme: str = None,
        topic: str = None,
    ) -> Optional[Dict[str, str]]:
        """Internal extraction using GPT-4o-mini."""

        system_prompt = (
            "You are a content analyst. Given a LinkedIn post by Jesse A. Eisenbalm "
            "(a premium lip balm brand that writes absurdist, self-aware commentary on "
            "work culture and current events), extract the position taken.\n\n"
            "Respond with a JSON object containing exactly three fields:\n"
            "- position_summary: 1-2 sentence summary of what the post argues or observes\n"
            "- sentiment: exactly one of [celebrate, critique, warn, question, encourage, observe]\n"
            "- key_claim: the single core claim or observation in one sentence"
        )

        context_parts = []
        if theme:
            context_parts.append(f"Theme: {theme}")
        if topic:
            context_parts.append(f"Topic: {topic}")
        context_line = ("\n" + "\n".join(context_parts) + "\n") if context_parts else ""

        prompt = f"""Extract the position from this LinkedIn post:
{context_line}
---POST START---
{post_content}
---POST END---

Return JSON with: position_summary, sentiment, key_claim"""

        result = await self.ai_client.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            model="gpt-4o-mini",
            temperature=0.2,
            max_tokens=300,
            response_format="json",
        )

        content = result.get("content")
        if not content:
            return None

        # Parse JSON response
        if isinstance(content, str):
            parsed = json.loads(content)
        elif isinstance(content, dict):
            parsed = content
        else:
            return None

        # Validate required fields
        position_summary = parsed.get("position_summary")
        sentiment = parsed.get("sentiment")
        key_claim = parsed.get("key_claim")

        if not position_summary or not key_claim:
            self.logger.warning("Position extraction returned incomplete data")
            return None

        return {
            "position_summary": str(position_summary).strip(),
            "sentiment": str(sentiment).strip().lower() if sentiment else "observe",
            "key_claim": str(key_claim).strip(),
        }
