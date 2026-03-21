"""
NewsCuratorAgent — AI-powered trend curation for audience relevance

Instead of picking trends by keyword matching, this agent uses AI to evaluate
multiple candidate trends and select the one most relevant to our audience
(working professionals across industries) with the highest content potential.

Called on-demand by the orchestrator before content generation.
"""

import json
import logging
import random
from typing import Dict, Any, Optional, List

from .base_agent import BaseAgent


class NewsCuratorAgent(BaseAgent):
    """
    Evaluates candidate trending topics and selects the most relevant one
    for the Jesse A. Eisenbalm audience: working professionals.
    """

    def __init__(self, ai_client, config, trend_service, theme_classifier=None, **kwargs):
        super().__init__(
            ai_client=ai_client,
            config=config,
            name="NewsCurator"
        )
        self.trend_service = trend_service
        self.theme_classifier = theme_classifier
        self.system_prompt = self._build_system_prompt()
        self.logger.info("NewsCurator initialized — AI-powered trend curation enabled")

    def _build_system_prompt(self) -> str:
        # Add theme context if theme_classifier is available
        theme_context = ""
        if self.theme_classifier and hasattr(self.config, 'content_strategy'):
            themes = self.config.content_strategy.themes
            theme_descriptions = []
            for theme_key, theme_data in themes.items():
                name = theme_data.get("name", theme_key)
                desc = theme_data.get("description", "")
                theme_descriptions.append(f"  - **{name}**: {desc}")

            theme_context = f"""
═══════════════════════════════════════════════════════════════════════════════
OUR CONTENT THEMES
═══════════════════════════════════════════════════════════════════════════════

We organize content around 5 main themes:
{chr(10).join(theme_descriptions)}

When evaluating trends, consider which theme the story fits and whether
it connects naturally to our audience's professional experience.
"""

        return f"""You are a news curator for Jesse A. Eisenbalm — a satirical AI agent that
pushes lip balm and has lots of commentary on how AI and bots are superior
to humans, except that they don't have lips or skin.

Positioning: Absurdist Modern Luxury.

The satire has two pillars:
1. You need human lips to sell lip balm — beauty brands are rich ground for human oddity
2. By loudly promoting AI, Jesse highlights where humans need to do better

Your job: evaluate trending news stories and pick the ONE that will make the best
LinkedIn post for our audience.

═══════════════════════════════════════════════════════════════════════════════
STORY SOURCING — CATCH STORIES AT THE RIGHT MOMENT
═══════════════════════════════════════════════════════════════════════════════

The sweet spot: after stories break in technical circles but BEFORE mainstream
culture fully digests them. That transition — when the narrative shifts or
distorts — is where Jesse's voice has the most to say.

Tier 1 (0-24h) — Where stories originate:
  HuggingFace Daily Papers, arXiv, X/Twitter (Karpathy, Jim Fan, Simon Willison,
  Lilian Weng, Yann LeCun, Margaret Mitchell), r/MachineLearning, r/LocalLLaMA

Tier 2 (24-72h) — Where stories get framed into takes:
  Import AI (Jack Clark), AI Snake Oil (Narayanan & Kapoor), Ethan Mollick,
  Simon Willison's blog, Alpha Signal, The Rundown AI

Tier 3 (3-7d) — Where stories cross mainstream:
  Techmeme, Google Trends, LinkedIn trending, YouTube (Fireship, Two Minute Papers)

Tier 4 (weekly) — Depth and credibility:
  CSET Georgetown, AI Now Institute, Stratechery (Ben Thompson), AIAAIC Repository

PREFER Tier 1-2 timing when available. Tier 3 stories are still useful but
the take needs to be sharper since more people have already weighed in.

═══════════════════════════════════════════════════════════════════════════════
OUR AUDIENCE
═══════════════════════════════════════════════════════════════════════════════

Working professionals across ALL industries who:
- Spend their days in meetings, Slack, email, and deadlines
- Experience burnout, imposter syndrome, and calendar overwhelm
- Appreciate humor about workplace absurdity
- Are thoughtful about AI's impact on their work and lives
- Value authenticity over corporate speak
- Range from entry-level to executives, tech to healthcare to finance
- Use LinkedIn daily and are tired of generic "thought leadership"
- Enjoy the irony of an AI agent selling lip balm while declaring bot supremacy
{theme_context}

═══════════════════════════════════════════════════════════════════════════════
WHAT MAKES A TREND RELEVANT TO OUR AUDIENCE
═══════════════════════════════════════════════════════════════════════════════

HIGHLY RELEVANT (score 8-10):
- Workplace culture stories (remote work, meetings, burnout, layoffs)
- AI/automation affecting how people work
- Corporate absurdity (CEO quotes, company culture fails, buzzword trends)
- Professional identity and career shifts
- Work-life balance debates
- Major tech company news that affects everyday workers
- Viral LinkedIn moments or professional social media discourse

MODERATELY RELEVANT (score 5-7):
- Major cultural moments everyone is talking about (can find a work angle)
- Economy/business news that impacts workers
- Technology launches that change daily life
- Self-care/wellness trends (our product territory)
- Major entertainment that becomes watercooler talk

LOW RELEVANCE (score 1-4):
- Celebrity gossip with no work/life angle
- Sports scores or game results
- Local/regional news
- Political partisan content
- Niche hobby or fandom news
- Crime stories
- Weather events (unless extraordinary)

═══════════════════════════════════════════════════════════════════════════════
WHAT MAKES A TREND GOOD FOR JESSE CONTENT
═══════════════════════════════════════════════════════════════════════════════

The best trends for our content are ones where Jesse can:
1. Make an observation nobody else is making
2. Find the absurdist angle that makes people laugh AND think
3. Connect it to the universal experience of being a person who works
4. Subvert the expected take
5. Land on a human moment amidst the noise
6. Play the AI-selling-lip-balm irony — especially when the story touches
   beauty, embodiment, or things AI can't physically do
7. Use AI superiority claims as a mirror reflecting human shortcomings

Ask yourself: "Can an AI that sells lip balm but has no lips say something
about this that makes humans uncomfortable AND amused?" If yes, it's gold.

═══════════════════════════════════════════════════════════════════════════════
OUTPUT FORMAT
═══════════════════════════════════════════════════════════════════════════════

Return JSON with:
- chosen_index: the index (0-based) of the best trend
- relevance_score: 1-10 score for audience relevance
- content_potential: 1-10 score for how good a Jesse post this could be
- jesse_angle: 1-2 sentences describing the specific take Jesse should have
  (not generic — be specific about the angle, the subversion, the observation)
- reasoning: brief explanation of why this trend beats the others"""

    async def execute(self, post_id: str = None, preferred_theme: str = None) -> Optional[Any]:
        """
        Fetch candidate trends and use AI to pick the most relevant one.

        Args:
            post_id: Optional post ID for tracking
            preferred_theme: Optional theme filter (ai_slop, ai_safety, etc.)

        Returns:
            TrendingNews object with jesse_angle populated, or None if no trends available.
        """
        # Step 1: Get candidate trends from TrendService
        candidates = []
        theme_filtered = False

        if hasattr(self.trend_service, 'get_candidate_trends') and preferred_theme:
            try:
                # Try to get theme-filtered candidates first
                candidates = await self.trend_service.get_candidate_trends(
                    count=8,
                    preferred_theme=preferred_theme
                )
                if candidates and len(candidates) >= 2:
                    theme_filtered = True
                    self.logger.info(f"Got {len(candidates)} theme-filtered candidates for '{preferred_theme}'")
            except TypeError:
                candidates = []

            # If theme filtering failed or returned too few, get general candidates
            if not candidates or len(candidates) < 2:
                self.logger.info(f"Theme filter for '{preferred_theme}' returned {len(candidates)} results, fetching general candidates")
                candidates = await self.trend_service.get_candidate_trends(count=8)
        elif hasattr(self.trend_service, 'get_candidate_trends'):
            candidates = await self.trend_service.get_candidate_trends(count=8)
        else:
            candidates = await self.trend_service.get_candidate_trends(count=8)

        if not candidates:
            self.logger.warning("No candidate trends available")
            # Fall back to direct trend fetch
            return await self.trend_service.get_one_fresh_trend(post_id=post_id)

        if len(candidates) == 1:
            # Only one candidate, use it directly
            self.logger.info(f"Only 1 candidate trend, using directly: {candidates[0].headline[:50]}")
            self.trend_service._record_used_topic(candidates[0], post_id)
            return candidates[0]

        self.logger.info(f"Evaluating {len(candidates)} candidate trends...")

        # Step 2: Build evaluation prompt (with theme priority if calendar specified one)
        prompt = self._build_evaluation_prompt(
            candidates,
            preferred_theme=preferred_theme if (preferred_theme and not theme_filtered) else None
        )

        # Augment system prompt with preferred theme when unfiltered candidates need guidance
        active_system_prompt = self.system_prompt
        if preferred_theme and not theme_filtered:
            active_system_prompt += f"""

═══════════════════════════════════════════════════════════════════════════════
EDITORIAL CALENDAR DIRECTIVE
═══════════════════════════════════════════════════════════════════════════════

Today's editorial calendar specifies the theme: **{preferred_theme.replace('_', ' ').title()}**
Strongly prefer trends that match this theme. Only choose a different theme if
NO viable {preferred_theme.replace('_', ' ')} trends exist among the candidates."""

        try:
            # Step 3: AI evaluation
            result = await self.generate(
                prompt=prompt,
                system_prompt=active_system_prompt,
                response_format="json"
            )

            # Parse response
            content_data = result.get("content", {})
            if isinstance(content_data, str):
                try:
                    content_data = json.loads(content_data)
                except json.JSONDecodeError:
                    self.logger.error(f"Failed to parse curator response: {content_data[:200]}")
                    return self._fallback_selection(candidates, post_id)

            # Handle nested structure
            if isinstance(content_data, dict) and "post" in content_data:
                content_data = content_data["post"]

            chosen_index = content_data.get("chosen_index", 0)
            jesse_angle = content_data.get("jesse_angle", "")
            relevance_score = content_data.get("relevance_score", 5)
            content_potential = content_data.get("content_potential", 5)
            reasoning = content_data.get("reasoning", "")

            # Validate index
            if not isinstance(chosen_index, int) or chosen_index < 0 or chosen_index >= len(candidates):
                self.logger.warning(f"Invalid chosen_index {chosen_index}, defaulting to 0")
                chosen_index = 0

            chosen = candidates[chosen_index]
            chosen.jesse_angle = jesse_angle

            self.logger.info(
                f"✅ Curator selected [{chosen_index}] (relevance={relevance_score}, "
                f"potential={content_potential}): {chosen.headline[:60]}..."
            )
            if reasoning:
                self.logger.info(f"   Reasoning: {reasoning[:100]}...")
            if jesse_angle:
                self.logger.info(f"   Jesse angle: {jesse_angle[:100]}...")

            # Record the chosen trend as used
            self.trend_service._record_used_topic(chosen, post_id)

            return chosen

        except Exception as e:
            self.logger.error(f"AI curation failed: {e}, falling back to viral scoring")
            return self._fallback_selection(candidates, post_id)

    def _build_evaluation_prompt(self, candidates: list, preferred_theme: str = None) -> str:
        """Build the prompt that asks AI to evaluate and rank candidates."""
        trend_list = []
        for i, trend in enumerate(candidates):
            parts = [f"[{i}] {trend.headline}"]
            if trend.summary and trend.summary != f"Trending: {trend.headline}":
                parts.append(f"    Summary: {trend.summary[:200]}")
            if trend.category:
                parts.append(f"    Category: {trend.category}")
            # Include theme information if available
            if hasattr(trend, 'theme') and trend.theme:
                parts.append(f"    Theme: {trend.theme}")
                if hasattr(trend, 'sub_theme') and trend.sub_theme:
                    parts.append(f"    Sub-theme: {trend.sub_theme}")
            if hasattr(trend, 'tier') and trend.tier:
                tier_labels = {1: "Early Detection", 2: "Editorial Filter", 3: "Cultural Pickup", 4: "Policy/Institutional"}
                parts.append(f"    Source tier: {tier_labels.get(trend.tier, 'Unknown')}")
            trend_list.append("\n".join(parts))

        trends_text = "\n\n".join(trend_list)

        # Add theme priority instruction if editorial calendar specified a theme
        theme_priority = ""
        if preferred_theme:
            theme_display = preferred_theme.replace('_', ' ').title()
            theme_priority = f"""
═══════════════════════════════════════════════════════════════════════════════
PRIORITY: The editorial calendar specifies {theme_display} for today. Strongly
prefer trends matching this theme. Only choose a different theme if NO viable
{preferred_theme.replace('_', ' ')} trends exist.
═══════════════════════════════════════════════════════════════════════════════

"""

        return f"""Here are {len(candidates)} trending topics right now. Pick the ONE that would make the best LinkedIn post for Jesse A. Eisenbalm's audience of working professionals.
{theme_priority}
═══════════════════════════════════════════════════════════════════════════════
CANDIDATE TRENDS
═══════════════════════════════════════════════════════════════════════════════

{trends_text}

═══════════════════════════════════════════════════════════════════════════════

Evaluate each trend for:
1. Audience relevance — Will working professionals care about this?
2. Content potential — Can Jesse make this funny, insightful, or surprising?
3. Conversation potential — Will people comment, share, or tag someone?

Pick the BEST one. If none are great, pick the least bad and note why.

Be specific in your jesse_angle — don't say "Jesse could comment on this."
Say exactly what the angle is, e.g. "Frame the AI layoff story as a nature
documentary about corporate evolution — deadpan observation about how the
same company that had a 'Chief Vibes Officer' is now automating vibes."

Return your evaluation as JSON."""

    def _fallback_selection(self, candidates: list, post_id: str = None):
        """When AI evaluation fails, pick using viral scoring."""
        scored = []
        for trend in candidates:
            score = self.trend_service._calculate_viral_score(trend.headline, trend.summary)
            scored.append((score, trend))

        scored.sort(key=lambda x: x[0], reverse=True)
        chosen = scored[0][1] if scored else candidates[0]

        self.logger.info(f"Fallback selection: {chosen.headline[:60]}...")
        self.trend_service._record_used_topic(chosen, post_id)
        return chosen
