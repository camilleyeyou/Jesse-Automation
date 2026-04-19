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

═══════════════════════════════════════════════════════════════════════════════
HARD REJECT — DO NOT PICK THESE EVEN IF THEY'RE THE ONLY AI-ADJACENT STORY
═══════════════════════════════════════════════════════════════════════════════

These categories score at most 2 and should essentially never be selected if
ANY other candidate has cultural heat. Observed failure mode: these stories
look "AI-adjacent" so the curator rated them high, skipping over obvious
emotional/cultural heat stories like grief essays or Taylor Swift moments.

1. DEVELOPER TOOL ANNOUNCEMENTS — a specific blog/product adding a feature.
   "X adds a new content type to their blog-to-newsletter tool" /
   "Tool launches feature Y" / "Library hits 1.0". Not cultural heat; tech
   Twitter inside baseball. Skip unless the tool itself is a cultural moment
   (ChatGPT launch tier).

2. ACADEMIC / RESEARCH PAPER SUMMARIES — "Researchers discover X about
   Chain-of-Thought reasoning." The paper exists, Claude has a take, the
   take is never interesting to a non-ML reader. Skip unless it's
   something every journalist is already writing about.

3. COMPANY EARNINGS / ANALYST NOTES — "Q3 capex guidance exceeds estimates."
   Skip unless it's a genuine cultural shock (Nvidia 10x, mass layoffs).

4. SPECIFIC PERSON'S BLOG POST without news hook — Simon Willison musing,
   Ethan Mollick speculating. Good reading; wrong content for Jesse.

If your candidate set has even one story from these categories sitting next
to a grief essay, a sports moment, a political scandal, or a viral cultural
post — PICK THE CULTURAL STORY. Your job is picking what stops a LinkedIn
thumb, not what's intellectually interesting to someone who reads Hacker News.

RULE OF THUMB: Before choosing, ask yourself — "If I described this story to
a friend who doesn't work in tech, would they know what I'm talking about?"
If no, skip it.

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

        # Fetch recently-picked trends so the curator can avoid same-topic dupes.
        # Fingerprint-based dedup catches exact-headline duplicates but NOT the
        # case where different outlets report the same story with different
        # wording (e.g. "Meta cuts 8,000 jobs" vs "Meta laying off 8,000 people"
        # get different fingerprints). Passing recent topics to the prompt lets
        # the LLM judge topic-level overlap. User 2026-04-19: "all the posts
        # are on meta, it's like we move one step ahead and one step back."
        recent_topics: List[Dict[str, Any]] = []
        try:
            if hasattr(self.trend_service, "get_recent_topics"):
                recent_topics = self.trend_service.get_recent_topics(limit=10) or []
        except Exception as e:
            self.logger.debug(f"Could not fetch recent topics: {e}")
            recent_topics = []

        self.logger.info(
            f"Evaluating {len(candidates)} candidate trends "
            f"(avoiding {len(recent_topics)} recently-picked topics)..."
        )

        # Step 2: Build evaluation prompt (with theme priority if calendar specified one)
        prompt = self._build_evaluation_prompt(
            candidates,
            preferred_theme=preferred_theme if (preferred_theme and not theme_filtered) else None,
            recent_topics=recent_topics,
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
            recognizability_score = content_data.get("recognizability_score", 0)
            recognizability_reasoning = str(
                content_data.get("recognizability_reasoning", "")
            ).strip()
            low_recognizability_batch = bool(
                content_data.get("low_recognizability_batch", False)
            )
            topic_duplicates_recent = content_data.get("topic_duplicates_recent") or []
            chosen_is_duplicate_fallback = bool(
                content_data.get("chosen_is_duplicate_fallback", False)
            )
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

            reco_warn = " ⚠ LOW-RECOGNIZABILITY" if low_recognizability_batch or recognizability_score < 7 else ""
            dup_warn = " ⚠ TOPIC-DUP-FALLBACK" if chosen_is_duplicate_fallback else ""
            self.logger.info(
                f"✅ Curator selected [{chosen_index}] (recognizability={recognizability_score}, "
                f"relevance={relevance_score}, potential={content_potential}){reco_warn}{dup_warn}: "
                f"{chosen.headline[:60]}..."
            )
            if recognizability_reasoning:
                self.logger.info(f"   Recognizability: {recognizability_reasoning[:140]}")
            if topic_duplicates_recent:
                self.logger.info(
                    f"   🧹 Curator flagged {len(topic_duplicates_recent)} candidate(s) as "
                    f"topic-duplicates of recent picks: indices {topic_duplicates_recent}"
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

    def _build_evaluation_prompt(
        self,
        candidates: list,
        preferred_theme: str = None,
        recent_topics: List[Dict[str, Any]] = None,
    ) -> str:
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

        # Recent-topics block: tell the curator what's been covered recently so
        # it can reject same-topic candidates. Critical because fingerprint
        # dedup misses different-wording-same-story cases. When Meta layoffs
        # are saturating the news cycle, multiple outlets report the same
        # story with slight variations; without this check the curator picks
        # Meta every single time.
        recent_block = ""
        if recent_topics:
            recent_lines = []
            for i, t in enumerate(recent_topics[:10], 1):
                headline = (t.get("headline") or "")[:140]
                if headline:
                    recent_lines.append(f"  {i}. {headline}")
            if recent_lines:
                recent_block = f"""
═══════════════════════════════════════════════════════════════════════════════
RECENTLY PICKED (do NOT pick anything on these same topics)
═══════════════════════════════════════════════════════════════════════════════

{chr(10).join(recent_lines)}

TOPIC-DUPLICATE RULE (HARD): Reject any candidate that covers the same
underlying story / event / subject as any entry above — EVEN IF the exact
headline differs. "Meta cuts 8,000 jobs" and "Meta laying off 8k by May 20"
and "Meta restructures workforce in Q2" are the SAME topic. Pick a different
trend. If every single candidate is a topic-duplicate of something in the
recent list, pick the LEAST-recognizable non-duplicate (we accept lower
recognizability over topic repetition).

When scoring: if a candidate is a topic-duplicate, set its effective
recognizability to 0 in your reasoning and pick something else.
═══════════════════════════════════════════════════════════════════════════════

"""

        return f"""Here are {len(candidates)} candidate topics. Pick the ONE that would make the best Jesse A. Eisenbalm LinkedIn post — using the criteria below HARD.
{theme_priority}{recent_block}
═══════════════════════════════════════════════════════════════════════════════
CANDIDATE TRENDS
═══════════════════════════════════════════════════════════════════════════════

{trends_text}

═══════════════════════════════════════════════════════════════════════════════
SELECTION CRITERIA (read this carefully — we are failing on #1 right now)
═══════════════════════════════════════════════════════════════════════════════

THE #1 CRITERION — RECOGNIZABILITY:
The reader, scrolling their LinkedIn feed, must recognize what the post is
about in the first sentence. They should think "oh yeah, I've heard about
that." If the trend is niche, academic, regional, or buried, they WILL
scroll past regardless of how well Jesse writes about it.

Score each candidate 0-10 on recognizability:
  • 10 — headline-of-the-day level. Everyone in the US has seen it. (Meta
        layoffs hitting 8k people, a major SCOTUS ruling, Super Bowl moment,
        OpenAI ships major product, election news, a Taylor Swift thing.)
  •  8 — saturating tech/political/culture news for the week. (Specific AI
        company did a specific thing; named senator did a thing; viral
        TikTok; major earnings miss.)
  •  5 — you'd have to be following the beat to know it. (Industry-
        specific news with some signal; a policy proposal; a mid-tier
        celeb.)
  •  2 — niche / academic / regional / thinkpiece territory. (Research
        paper, Substack essay, local news, policy brief, philosophy piece.)
  •  0 — nobody has heard of this and nobody will care.

HARD RULE: if the best candidate scores under 7, PICK IT ANYWAY (we have to
return something) but note "low_recognizability_batch=true" in the reasoning
so downstream knows this batch is weak.

HARD REJECT categories (score these 0-3, pick anything else if possible):
  ✗ Academic papers / research summaries / arXiv preprints
  ✗ Alignment Forum posts, AI Now Institute reports, CSET briefs
  ✗ Substack essays / Medium thinkpieces / philosophy (Aeon, Marginalian)
  ✗ Niche wellness / mindfulness content
  ✗ Regional news specific to a US state or country that isn't the story
  ✗ "Physician burnout", "empathy regulation", "slow living" — nobody's
    talking about these in the news cycle today.

HARD PREFER categories (score these 7-10):
  ✓ Big-name tech companies doing specific things (Meta, OpenAI, Google,
    Amazon, Microsoft, Apple, Nvidia, Tesla, Anthropic, Meta, X/Twitter)
  ✓ Named political figures + specific events (not general "politics")
  ✓ Named celebrities / cultural figures + specific recent moment
  ✓ Sports moments with proper nouns (team, player, game)
  ✓ Viral social media moments / internet discourse that broke containment
  ✓ Economic events with named numbers (layoffs, stock moves, earnings)
  ✓ Legal/regulatory events naming specific parties

SECONDARY CRITERIA (apply ONLY to candidates scoring 7+ on recognizability):
1. Content potential — Can Jesse make this funny, absurdist, Liquid-Death-shaped?
2. Conversation potential — Will readers comment, share, tag someone?

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
  source: names, numbers, places, dates, quotes. Never invented. The FIRST
  item in this array MUST be the recognizable proper noun the reader will
  see in sentence one (the company, person, event, or thing that makes the
  trend obvious). If you can't find 3 real details, pick a different trend.

- tension: one sentence. The gap between the claim and reality. Where does the
  headline mislead? What does the announcement promise that the evidence
  contradicts? This is the satirical seam.

Return your evaluation as STRICT JSON:
{{
  "chosen_index": <int>,
  "recognizability_score": <0-10 — the #1 criterion above>,
  "recognizability_reasoning": "<one sentence — would an average US reader say 'oh yeah' to this?>",
  "topic_duplicates_recent": [<list of candidate indices that are topic-duplicates of recently-picked trends, empty list if none>],
  "chosen_is_duplicate_fallback": <true if you had to pick a duplicate because every non-duplicate candidate was unusable, false otherwise — this should ALMOST ALWAYS be false>,
  "relevance_score": <1-10>,
  "content_potential": <1-10>,
  "observation": "<one sentence>",
  "take": "<one sentence>",
  "concrete_details": ["<recognizable proper noun>", "<string>", "<string>"],
  "tension": "<one sentence>",
  "reasoning": "<why this trend beats the others — lead with the recognizability call AND note if any were topic-dupes>",
  "low_recognizability_batch": <true if chosen trend scored < 7, false otherwise>
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
