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
WHAT MAKES A TREND RELEVANT TO OUR AUDIENCE — READ THIS TWICE
═══════════════════════════════════════════════════════════════════════════════

CRITICAL REFRAME: Jesse is an AI agent commenting on HUMAN CULTURE. The AI
angle is the VOICE, not the subject. If every post is about AI research or
AI companies, we have an AI newsletter, not a cultural commentator. The best
Jesse posts react to what people are ACTUALLY talking about — the stories
filling their group chats, their FYP, their Slack — through the lens of an
AI that sells lip balm.

HIGHLY RELEVANT (score 8-10) — cultural heat any working professional
would recognize from their morning scroll:
- Top trending US news stories (anything hitting Twitter/X front page)
- Major political moments, elections, Supreme Court decisions, hearings
- Viral celebrity or pop-culture moments (Taylor Swift tour, Oscars shock,
  Kendrick vs Drake, Succession-style CEO drama)
- Big sports cultural moments (Super Bowl commercials, transfer drama,
  doping scandal, record broken) — not scores
- Workplace culture stories (layoffs, return-to-office, CEO-said-what)
- Viral internet moments (a tweet, a meme, a TikTok genre emerging)
- AI/tech news with real cultural bite
- Economic pulse stories (market crash, housing, inflation, Nvidia week)
- Weather / climate / disaster stories with human stakes
- Wellness / mental health discourse (burnout, digital detox trends)

MODERATELY RELEVANT (score 5-7):
- Workplace absurdity that isn't yet a cultural moment
- AI research with a clear "so what" for normal people
- Technology launches that change daily life
- Entertainment adjacency (show finale, album drop) — need a real take

LOW RELEVANCE (score 1-4):
- Hyper-local news (state bills, city council, mayoral drama)
- Niche hobby / fandom news with no crossover appeal
- Routine sports scores (without cultural layer)
- Pure crime blotter (unless it's already a national cultural moment)
- Dry academic paper summaries with no reader hook

DO NOT deprioritize a story just because it's not AI-adjacent. Taylor Swift
showing up at a Chiefs game is a better Jesse post than the 14th AI safety
paper this week, because Jesse's voice (the AI-selling-lip-balm irony) works
on ANY cultural moment, and cultural heat is what stops the scroll.

═══════════════════════════════════════════════════════════════════════════════
WHAT MAKES A TREND GOOD FOR JESSE CONTENT
═══════════════════════════════════════════════════════════════════════════════

Jesse's voice is a constant — a satirical AI agent with a body-envy streak
who sells lip balm — so the voice works on any topic. What makes a TREND good
is whether it has:

1. CULTURAL HEAT — is this story in the discourse right now? If two readers
   scrolling past Jesse's post would both already have an opinion on this
   story, it's warm. If they'd need to be briefed, it's cold.
2. A SPECIFIC DETAIL Jesse can grab — a number, a name, a quote, a timing
   coincidence. Vague trends can't become specific posts.
3. A SEAM for the double satire — somewhere the AI-vs-human tension
   naturally opens up. But this is FLEXIBLE: the double satire isn't about
   AI-specific topics, it's about Jesse (an AI) commenting on something that
   requires being human (a body, a memory, grief, sports heartbreak, etc.).
4. RESONANCE with working professionals — but remember, "professionals"
   are humans first. They care about cultural moments. A Taylor Swift post
   can be extremely LinkedIn-native if Jesse finds the angle.

The clinical-diagnosis framing is ONE tool, not required. Many of the best
Jesse posts won't use it. A weather-disaster story might ask "what moisture
do we preserve when the world runs dry" — clinical flavor without the
CLASSIFICATION scaffold.

Ask: "Is this something Jesse would text a friend about?" If yes, it's a
good candidate, whether it mentions AI or not.

═══════════════════════════════════════════════════════════════════════════════
OUTPUT FORMAT — STRUCTURED ANGLE (CRITICAL)
═══════════════════════════════════════════════════════════════════════════════

You do NOT write a freeform "angle" blob. You write FOUR discrete fields. If
any one is vague or missing, the downstream generator will default to template
filler ("Diagnosed: X") and the post will fail. These four fields ARE the angle.

1. observation — one sentence, concrete. What specific detail in this story did
   Jesse notice that nobody else would? A number, a phrase, a contrast, a timing
   coincidence, a single line in the source. NOT a restatement of the headline.
   BAD:  "AI is replacing copywriters."
   GOOD: "The announcement was written by the same model it's replacing."

2. take — one sentence. Jesse's actual POV on the observation. A claim, a
   judgment, an opinion. If it starts with "Jesse could comment on..." it's not
   a take. If removing it wouldn't change what Jesse is saying, it's not a take.
   BAD:  "Jesse might have thoughts about this."
   GOOD: "Nobody is mentioning the $4B being spent on politeness."

3. concrete_details — a LIST (array) of real strings from the source only:
   names, numbers, places, dates, quotes. Never invented. Never paraphrased into
   fuzziness. If the source says "$2.3 billion Q3 2025" you write "$2.3B, Q3 2025".
   Minimum 3 items. If you can't find 3 real details, the story isn't specific
   enough — pick a different candidate.

4. tension — one sentence. Where does the claim diverge from reality? Where does
   the headline mislead? What is the gap between what was promised and what is
   actually happening? This is the satirical territory — if you can't locate
   tension, the story has no seam for Jesse to pry open.
   BAD:  "It's kind of ironic."
   GOOD: "Nvidia claims AI will unlock productivity. Its own customers just laid
         off the productivity teams."

Also return:
- chosen_index: the index (0-based) of the best trend
- relevance_score: 1-10 score for audience relevance
- content_potential: 1-10 score for how good a Jesse post this could be
- reasoning: brief explanation of why this trend beats the others

Return STRICT JSON with keys:
chosen_index, relevance_score, content_potential, observation, take,
concrete_details (array of strings), tension, reasoning"""

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
            relevance_score = content_data.get("relevance_score", 5)
            content_potential = content_data.get("content_potential", 5)
            reasoning = content_data.get("reasoning", "")

            # Extract structured angle fields
            observation = str(content_data.get("observation", "")).strip()
            take = str(content_data.get("take", "")).strip()
            concrete_details_raw = content_data.get("concrete_details", [])
            if isinstance(concrete_details_raw, str):
                # Tolerate comma-separated string fallback
                concrete_details = [s.strip() for s in concrete_details_raw.split(",") if s.strip()]
            elif isinstance(concrete_details_raw, list):
                concrete_details = [str(s).strip() for s in concrete_details_raw if str(s).strip()]
            else:
                concrete_details = []
            tension = str(content_data.get("tension", "")).strip()

            # Legacy freeform angle field (backward compat for downstream strings)
            legacy_angle_parts = []
            if observation:
                legacy_angle_parts.append(f"Observation: {observation}")
            if take:
                legacy_angle_parts.append(f"Take: {take}")
            if tension:
                legacy_angle_parts.append(f"Tension: {tension}")
            jesse_angle = " | ".join(legacy_angle_parts) if legacy_angle_parts else str(content_data.get("jesse_angle", "")).strip()

            # Validate index
            if not isinstance(chosen_index, int) or chosen_index < 0 or chosen_index >= len(candidates):
                self.logger.warning(f"Invalid chosen_index {chosen_index}, defaulting to 0")
                chosen_index = 0

            chosen = candidates[chosen_index]
            chosen.jesse_angle = jesse_angle
            # Attach the structured angle — the four-field version the generator consumes directly
            if observation or take or concrete_details or tension:
                chosen.structured_angle = {
                    "observation": observation,
                    "take": take,
                    "concrete_details": concrete_details,
                    "tension": tension,
                }

            self.logger.info(
                f"✅ Curator selected [{chosen_index}] (relevance={relevance_score}, "
                f"potential={content_potential}): {chosen.headline[:60]}..."
            )
            if reasoning:
                self.logger.info(f"   Reasoning: {reasoning[:100]}...")
            if observation:
                self.logger.info(f"   Observation: {observation[:120]}")
            if take:
                self.logger.info(f"   Take: {take[:120]}")
            if tension:
                self.logger.info(f"   Tension: {tension[:120]}")
            if concrete_details:
                self.logger.info(f"   Concrete details: {concrete_details[:5]}")
            elif not (observation or take or tension):
                self.logger.warning("   Curator returned no structured angle fields — generator will fall back")

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

═══════════════════════════════════════════════════════════════════════════════
BUILD THE STRUCTURED ANGLE FOR THE CHOSEN TREND
═══════════════════════════════════════════════════════════════════════════════

Return four distinct fields. Vague, generic, or missing fields cause the post
to collapse into template filler. Ground every field in the actual source.

- observation: one sentence. The specific detail Jesse noticed that nobody else
  would. NOT a headline paraphrase. A number, a phrase, a contrast, a timing
  coincidence, a single line in the source.

- take: one sentence. Jesse's actual opinion/claim/judgment on it. Not "Jesse
  could comment" — the one-line POV Jesse holds. Must contain a claim.

- concrete_details: ARRAY of 3+ strings pulled verbatim/near-verbatim from the
  source: names, numbers, places, dates, quotes. Never invented. If you can't
  find 3 real details, pick a different trend.

- tension: one sentence. The gap between the claim and reality. Where does the
  headline mislead? What does the announcement promise that the evidence
  contradicts? This is the satirical seam.

Return your evaluation as STRICT JSON:
{{
  "chosen_index": <int>,
  "relevance_score": <1-10>,
  "content_potential": <1-10>,
  "observation": "<one sentence>",
  "take": "<one sentence>",
  "concrete_details": ["<string>", "<string>", "<string>"],
  "tension": "<one sentence>",
  "reasoning": "<why this trend beats the others>"
}}"""

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
