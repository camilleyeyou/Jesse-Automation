"""
Content Orchestrator - SIMPLIFIED
- One fresh trend fetched per post
- No trend storage/caching
- Clean separation of concerns
- Memory integration for learning and avoiding repetition
"""

import asyncio
import logging
import os
import random
import uuid
from typing import Dict, Any, List, Optional

from ..models.post import LinkedInPost, ValidationScore
from ..agents.content_strategist import ContentGeneratorAgent
from ..agents.feedback_aggregator import FeedbackAggregatorAgent
from ..agents.revision_generator import RevisionGeneratorAgent
from ..agents.validators import SarahChenValidator, MarcusWilliamsValidator, JordanParkValidator

try:
    from ..agents.position_extractor import PositionExtractor
    POSITION_EXTRACTOR_AVAILABLE = True
except ImportError:
    POSITION_EXTRACTOR_AVAILABLE = False
    PositionExtractor = None

try:
    from ..agents.news_curator import NewsCuratorAgent
    NEWS_CURATOR_AVAILABLE = True
except ImportError:
    NEWS_CURATOR_AVAILABLE = False

try:
    from ..agents.angle_architect import AngleArchitectAgent
    ANGLE_ARCHITECT_AVAILABLE = True
except ImportError:
    ANGLE_ARCHITECT_AVAILABLE = False
    AngleArchitectAgent = None

try:
    from ..infrastructure.trend_service import get_trend_service, MultiTierTrendService
    from ..infrastructure.theme_classifier import ThemeClassifier
    TREND_SERVICE_AVAILABLE = True
    MULTI_TIER_AVAILABLE = True
except ImportError:
    TREND_SERVICE_AVAILABLE = False
    MULTI_TIER_AVAILABLE = False
    MultiTierTrendService = None
    ThemeClassifier = None

try:
    from ..infrastructure.memory import get_memory
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False
    get_memory = None

logger = logging.getLogger(__name__)


def convert_to_web_url(file_path: str, media_type: str = "image") -> str:
    """Convert local file path to web-accessible URL"""
    if not file_path:
        return None
    if file_path.startswith('/images') or file_path.startswith('/videos'):
        return file_path
    if file_path.startswith('http'):
        return file_path
    
    filename = file_path.split('/')[-1]
    if media_type == "video" or filename.endswith('.mp4'):
        return f"/videos/{filename}"
    return f"/images/{filename}"


class BatchResult:
    def __init__(self, batch_id: str, posts: List[LinkedInPost], media_type: str = "image"):
        self.batch_id = batch_id
        self.id = batch_id
        self.posts = posts
        self.media_type = media_type
        self.approved_posts = posts
        self.rejected_posts = []
    
    def get_approved_posts(self):
        return self.approved_posts
    
    def get_rejected_posts(self):
        return self.rejected_posts


class ContentOrchestrator:
    """
    Orchestrates content generation.
    
    KEY CHANGE: Each post gets ONE fresh trend fetched at generation time.
    No caching, no storage, no duplicates.
    """
    
    # CTA comments in Jesse's voice — one is chosen randomly per post
    CTA_COMMENTS = [
        "Hand-numbered. Waiting. jesseaeisenbalm.com",
        "The balm doesn't judge. jesseaeisenbalm.com",
        "$8.99 and zero opinions about your calendar. jesseaeisenbalm.com",
        "One tube. No advice. jesseaeisenbalm.com",
        "Still here. Still $8.99. jesseaeisenbalm.com",
        "The void called. It wants balm. jesseaeisenbalm.com",
    ]

    def __init__(self, ai_client, config, image_generator=None, queue_manager=None, comment_service=None, db_path=None):
        self.ai_client = ai_client
        self.config = config
        self.image_generator = image_generator
        self.queue_manager = queue_manager
        self.comment_service = comment_service
        self.db_path = db_path or ("/data/queue.db" if os.path.isdir("/data") else "data/automation/queue.db")

        self.content_generator = ContentGeneratorAgent(ai_client, config)
        self.feedback_aggregator = FeedbackAggregatorAgent(ai_client, config)
        self.revision_generator = RevisionGeneratorAgent(ai_client, config)
        
        self.validators = [
            SarahChenValidator(ai_client, config),
            MarcusWilliamsValidator(ai_client, config),
            JordanParkValidator(ai_client, config)
        ]
        
        self.trend_service = None
        self.news_curator = None
        self.theme_classifier = None

        if TREND_SERVICE_AVAILABLE:
            # Initialize theme classifier if content strategy is available
            if MULTI_TIER_AVAILABLE and hasattr(config, 'content_strategy'):
                try:
                    self.theme_classifier = ThemeClassifier(ai_client, config, db_path=self.db_path)
                    logger.info("✅ Theme classifier initialized - AI-powered theme classification enabled")

                    # Initialize MultiTierTrendService with theme classification
                    self.trend_service = MultiTierTrendService(
                        config=config,
                        theme_classifier=self.theme_classifier,
                        db_path=self.db_path,
                        brave_api_key=os.getenv('BRAVE_API_KEY')
                    )
                    logger.info("✅ Multi-tier trend service initialized - 5 themes, 4 sourcing tiers active")

                    # Check enabled sources
                    tier_dist = self.trend_service.get_tier_distribution()
                    enabled_sources = sum(tier_dist.values())
                    logger.info(f"📊 Source distribution: {enabled_sources} sources enabled across tiers {list(tier_dist.keys())}")

                except Exception as e:
                    logger.warning(f"⚠️ MultiTierTrendService initialization failed: {e}, falling back to legacy TrendService")
                    self.trend_service = get_trend_service(self.db_path)
            else:
                # Fall back to legacy TrendService
                self.trend_service = get_trend_service(self.db_path)
                logger.info("✅ Trend service initialized - content will react to real news")

            # Initialize AI-powered news curator with theme classifier
            if NEWS_CURATOR_AVAILABLE:
                self.news_curator = NewsCuratorAgent(
                    ai_client,
                    config,
                    self.trend_service,
                    theme_classifier=self.theme_classifier  # Pass theme classifier
                )
                if self.theme_classifier:
                    logger.info("✅ News curator initialized - AI-powered trend curation + theme classification enabled")
                else:
                    logger.info("✅ News curator initialized - AI-powered trend curation enabled")
            else:
                logger.warning("⚠️ NewsCuratorAgent not available, using direct trend selection")

        # Initialize AngleArchitect — sits between curator and generator,
        # picks register + forces real opinion + plans ski-jump shape. Phase
        # 1 (2026-04-19). If unavailable or disabled, generator falls back
        # to its legacy single-register behavior.
        self.angle_architect = None
        if ANGLE_ARCHITECT_AVAILABLE:
            try:
                self.angle_architect = AngleArchitectAgent(ai_client, config)
                logger.info("✅ AngleArchitect initialized - register rotation + POV forcing enabled")
            except Exception as e:
                logger.warning(f"AngleArchitect init failed (graceful degrade): {e}")

        # Initialize memory system
        self.memory = None
        if MEMORY_AVAILABLE:
            try:
                self.memory = get_memory(self.db_path)
                logger.info("✅ Memory system initialized - agents will learn from past content")
            except Exception as e:
                logger.warning(f"Memory system unavailable: {e}")

        # Initialize position extractor for tracking what Jesse says
        self.position_extractor = None
        if POSITION_EXTRACTOR_AVAILABLE:
            try:
                self.position_extractor = PositionExtractor(ai_client, config)
                logger.info("✅ Position extractor initialized - will track Jesse's stances")
            except Exception as e:
                logger.warning(f"Position extractor unavailable: {e}")

        if self.image_generator:
            logger.info("✅ ContentOrchestrator initialized WITH image generator")
        else:
            logger.warning("⚠️ ContentOrchestrator initialized WITHOUT image generator")
    
    async def _architect_angle(self, trend, pillar: str = None, post_id: str = None):
        """Run the AngleArchitect on a curated trend. Attaches `blueprint`
        attribute to the trend object. Graceful degrade: if architect is
        unavailable or fails, `blueprint` is None and the generator falls
        back to legacy single-register behavior.

        Phase 1 (2026-04-19). Same logic for batch + live flows — must stay
        shared so both paths get identical register rotation.
        """
        if not trend or not self.angle_architect:
            return None

        # Extract curator's structured angle if it exists on the trend
        curator_angle = getattr(trend, "structured_angle", None) or {}
        if not isinstance(curator_angle, dict):
            curator_angle = {}

        # Pull recent register history from memory so architect can rotate
        recent_registers: list = []
        recent_length_targets: list = []
        recent_structure_shapes: list = []
        if self.memory:
            try:
                recent_registers = self.memory.get_recent_registers(days=7, limit=10)
            except Exception as e:
                logger.debug(f"Could not fetch recent_registers: {e}")
            try:
                # Phase C (2026-04-20): length + structure rotation state
                bp_fields = self.memory.get_recent_blueprint_fields(
                    fields=["length_target", "structure_shape"],
                    days=7, limit=10,
                )
                recent_length_targets = bp_fields.get("length_target", [])
                recent_structure_shapes = bp_fields.get("structure_shape", [])
            except Exception as e:
                logger.debug(f"Could not fetch recent blueprint fields: {e}")

        try:
            blueprint = await self.angle_architect.execute(
                trend_headline=trend.headline,
                trend_summary=getattr(trend, "summary", "") or "",
                curator_angle=curator_angle,
                recent_registers=recent_registers,
                pillar=pillar,
                post_id=post_id,
                recent_length_targets=recent_length_targets,
                recent_structure_shapes=recent_structure_shapes,
            )
            # Attach to trend so it flows with the post through generation
            trend.blueprint = blueprint
            trend.register = blueprint.get("register") if isinstance(blueprint, dict) else None
            return blueprint
        except Exception as e:
            logger.warning(f"Architect invocation failed (graceful degrade): {e}")
            trend.blueprint = None
            trend.register = None
            return None

    def _determine_post_context(self):
        """Decide today's (theme, angle_seed, format) — the editorial guidance
        that travels with a generation.

        Same logic the scheduled 'generate_and_post_now' flow runs, extracted
        here so the batch / manual 'generate-content' path gets IDENTICAL
        treatment — including the QualityDriftAgent's pillar-starvation
        override and the weekly strategist's calendar entry. Without this,
        the dashboard's Generate button skipped all the supervisor protections.

        Returns: (preferred_theme: Optional[str], angle_seed: Optional[str],
                  preferred_format: Optional[str])
        """
        from datetime import datetime as _dt

        preferred_theme = None
        angle_seed = None
        preferred_format = None

        if not self.memory:
            return preferred_theme, angle_seed, preferred_format

        try:
            # Calendar — weekly strategist's editorial guidance
            today_str = _dt.utcnow().strftime("%Y-%m-%d")
            calendar_entry = self.memory.get_calendar_entry(today_str)
            if calendar_entry and calendar_entry.get("status") == "planned":
                preferred_theme = calendar_entry.get("theme")
                angle_seed = calendar_entry.get("angle_seed")
                preferred_format = calendar_entry.get("format")
                logger.info(
                    f"📅 Calendar entry found: theme={preferred_theme}, "
                    f"format={preferred_format}, angle={angle_seed}"
                )
                self.memory.update_calendar_status(calendar_entry["id"], "generating")
            elif calendar_entry:
                logger.info(f"📅 Calendar entry exists but status={calendar_entry.get('status')} — skipping")

            # No calendar entry → DO NOT force a pillar. Previously we picked
            # the least-used pillar and filtered candidates to only that theme,
            # which narrowed the curator's pool. Observed failure: with pillar
            # forced to "ai_slop", grief/wellness/cultural stories were filtered
            # out and the curator was left picking between niche dev tool blog
            # posts (Simon Willison → "blog-to-newsletter feature") instead of
            # a cancer-grief essay in the same candidate pool.
            #
            # Leaving preferred_theme=None lets the curator evaluate the ENTIRE
            # pool and pick on cultural heat, then whatever pillar best fits
            # the selected story is used. The supervisor's pillar_imbalance
            # finding still catches long-term imbalance via get_severely_starved
            # below.

            # Safety valve: supervisor-detected pillar starvation overrides all.
            try:
                starved = self.memory.get_severely_starved_pillar(days=7)
                if starved and starved != preferred_theme:
                    logger.warning(
                        f"⚠️  Pillar '{starved}' has zero posts in the last 7 days. "
                        f"Overriding theme '{preferred_theme}' → '{starved}' to restore balance."
                    )
                    preferred_theme = starved
                    # Calendar-sourced angle seed doesn't match if we switched pillars
                    angle_seed = None
            except Exception as e:
                logger.debug(f"Starvation check failed (non-blocking): {e}")
        except Exception as e:
            logger.warning(f"Calendar/context check failed: {e}")

        return preferred_theme, angle_seed, preferred_format

    async def generate_batch(self, num_posts: int = 1, use_video: bool = False) -> BatchResult:
        """Generate a batch of posts, each with a unique fresh trend."""

        batch_id = str(uuid.uuid4())
        logger.info(f"Starting batch {batch_id[:8]} with {num_posts} posts")

        # Start memory session for this batch
        if self.memory:
            self.memory.start_session(batch_id)
            logger.info("📝 Memory session started")

        # Reset trend tracking for this batch
        if self.trend_service:
            self.trend_service.reset_for_new_batch()

        approved_posts = []
        rejected_count = 0

        for i in range(num_posts):
            post_number = i + 1
            post_id = f"{batch_id[:8]}_{post_number}"  # Create tracking ID
            logger.info(f"\n--- Post {post_number}/{num_posts} ---")

            # Determine the post's editorial context — calendar guidance,
            # pillar rotation, starvation override. This was previously only
            # run in the scheduled live-post flow; now batch/manual generation
            # (dashboard "Generate" button) gets the same protections.
            preferred_theme, angle_seed, preferred_format = self._determine_post_context()

            # Fetch curated trend for THIS post (curator respects preferred_theme)
            trend = None
            if self.news_curator:
                curator_kwargs = {"post_id": post_id}
                if preferred_theme:
                    curator_kwargs["preferred_theme"] = preferred_theme
                trend = await self.news_curator.execute(**curator_kwargs)
                if trend:
                    logger.info(f"📰 Curated trend ({trend.category}): {trend.headline[:70]}...")
            elif self.trend_service:
                trend = await self.trend_service.get_one_fresh_trend(post_id=post_id)
                if trend:
                    logger.info(f"📰 Trend ({trend.category}): {trend.headline[:70]}...")

            # Phase 1: architect the angle BEFORE generation
            if trend:
                await self._architect_angle(trend, pillar=preferred_theme, post_id=post_id)

            try:
                post, validation_scores, was_approved = await self._process_single_post_with_memory(
                    post_number=post_number,
                    batch_id=batch_id,
                    trend=trend,
                    use_video=use_video,
                    angle_seed=angle_seed,
                    preferred_format=preferred_format,
                )

                if was_approved and post:
                    approved_posts.append(post)
                    logger.info(f"✅ Post {post_number} APPROVED")
                else:
                    rejected_count += 1
                    logger.warning(f"❌ Post {post_number} REJECTED")

            except Exception as e:
                logger.error(f"Post {post_number} failed: {e}")
                import traceback
                traceback.print_exc()
                rejected_count += 1

        # End memory session
        if self.memory:
            self.memory.end_session()
            logger.info(f"📝 Memory session ended: {len(approved_posts)} approved, {rejected_count} rejected")

        logger.info(f"\nBatch complete: {len(approved_posts)}/{num_posts} approved")
        return BatchResult(batch_id=batch_id, posts=approved_posts)
    
    async def _process_single_post_with_memory(
        self,
        post_number: int,
        batch_id: str,
        trend=None,
        use_video: bool = False,
        angle_seed: str = None,
        preferred_format: str = None,
    ) -> tuple:
        """
        Process a single post and store results in memory.

        Returns:
            tuple: (post, validation_scores, was_approved)
        """
        post = await self._process_single_post(
            post_number=post_number,
            batch_id=batch_id,
            trend=trend,
            use_video=use_video,
            angle_seed=angle_seed,
            preferred_format=preferred_format,
        )

        # Real approval requires 2-of-3 validator consensus. Previously the
        # orchestrator shipped any non-None post, which included max-revisions
        # fallbacks that never hit consensus — observed at 88% of shipped posts.
        # Now: the post must actually have 2+ approvals to count as approved.
        validation_scores = post.validation_scores if post else []
        approval_count = sum(1 for vs in validation_scores if vs.approved)
        was_approved = post is not None and approval_count >= 2

        # Store in memory
        if self.memory:
            try:
                # Extract metadata for memory
                post_id = f"{batch_id[:8]}_{post_number}"
                content = post.content if post else ""
                pillar = getattr(post, 'cultural_reference', None)
                pillar_name = pillar.category if pillar else None

                # Calculate average score
                avg_score = 0
                if validation_scores:
                    avg_score = sum(v.score for v in validation_scores) / len(validation_scores)

                # Convert validation scores to dicts for storage
                scores_as_dicts = []
                for vs in validation_scores:
                    scores_as_dicts.append({
                        'agent_name': vs.agent_name,
                        'score': vs.score,
                        'approved': vs.approved,
                        'feedback': vs.feedback,
                        'strengths': getattr(vs, 'strengths', []),
                        'weaknesses': getattr(vs, 'weaknesses', [])
                    })

                # Extract theme/tier info from trend if available
                theme_metadata = {}
                if trend:
                    if hasattr(trend, 'theme') and trend.theme:
                        theme_metadata['theme'] = trend.theme
                    if hasattr(trend, 'sub_theme') and trend.sub_theme:
                        theme_metadata['sub_theme'] = trend.sub_theme
                    if hasattr(trend, 'tier') and trend.tier:
                        theme_metadata['tier'] = trend.tier
                    if hasattr(trend, 'source_type') and trend.source_type:
                        theme_metadata['source_type'] = trend.source_type
                    if hasattr(trend, 'confidence_score') and trend.confidence_score:
                        theme_metadata['theme_confidence'] = trend.confidence_score

                # Phase 1: capture architect + curator artifacts for observability
                register = getattr(trend, "register", None) if trend else None
                blueprint = getattr(trend, "blueprint", None) if trend else None
                curator_angle = getattr(trend, "structured_angle", None) if trend else None
                if isinstance(curator_angle, dict) is False:
                    curator_angle = None

                self.memory.remember_post(
                    post_id=post_id,
                    batch_id=batch_id,
                    content=content,
                    pillar=pillar_name,
                    trending_topic=trend.headline if trend else None,
                    was_approved=was_approved,
                    average_score=avg_score,
                    validation_scores=scores_as_dicts,
                    metadata=theme_metadata if theme_metadata else None,
                    register=register,
                    blueprint=blueprint,
                    curator_angle=curator_angle,
                )
                logger.debug(f"📝 Stored post {post_id} in memory (approved={was_approved})")

                # Extract and store position for approved posts
                if was_approved and post and content:
                    await self._extract_and_store_position(
                        post_id=post_id,
                        content=content,
                        trend=trend,
                    )

                # Auto-grow the gold-standard retrieval corpus from clean wins.
                # A "clean win" is a post that passed 3-of-3 validators on the
                # first attempt with a high average — no revisions, no fallback.
                # Those are the exemplars future retrieval should anchor voice on.
                if was_approved and post and content:
                    await self._maybe_promote_to_gold_standard(
                        post_id=post_id,
                        content=content,
                        pillar=pillar_name,
                        format_name=getattr(post.cultural_reference, "reference", None)
                            if post.cultural_reference else None,
                        validation_scores=validation_scores,
                        revision_count=getattr(post, "revision_count", 0),
                    )

            except Exception as e:
                logger.warning(f"Failed to store post in memory: {e}")

        return post, validation_scores, was_approved

    async def _process_single_post(
        self,
        post_number: int,
        batch_id: str,
        trend=None,
        use_video: bool = False,
        angle_seed: str = None,
        preferred_format: str = None,
    ) -> Optional[LinkedInPost]:
        """Process a single post with its assigned trend."""
        
        # Format trend for content generator with rich context
        trend_context = None
        if trend:
            parts = [
                f"HEADLINE: {trend.headline}",
                f"CATEGORY: {trend.category.upper()}",
            ]

            # Add theme/tier context if available
            theme = getattr(trend, 'theme', '') or ''
            sub_theme = getattr(trend, 'sub_theme', '') or ''
            tier = getattr(trend, 'tier', None)
            tier_label = getattr(trend, 'tier_label', '')

            if theme:
                theme_display = theme.replace('_', ' ').title()
                if sub_theme:
                    sub_theme_display = sub_theme.replace('_', ' ').title()
                    parts.append(f"STRATEGIC THEME: {theme_display} / {sub_theme_display}")
                else:
                    parts.append(f"STRATEGIC THEME: {theme_display}")

                if tier and tier_label:
                    tier_names = {
                        1: "Early Detection (0-24h)",
                        2: "Editorial Filter (24-72h)",
                        3: "Cultural Pickup (3-7d)",
                        4: "Policy/Institutional (weekly)"
                    }
                    tier_desc = tier_names.get(tier, tier_label)
                    parts.append(f"SOURCE TIER: Tier {tier} ({tier_desc})")

            # Use description (rich) or summary (basic)
            description = getattr(trend, 'description', '') or ''
            if description:
                parts.append(f"DETAILS: {description[:300]}")
            elif trend.summary:
                parts.append(f"SUMMARY: {trend.summary}")

            if trend.url and trend.source != "fallback":
                parts.append(f"SOURCE: {trend.url}")

            # Include related articles for additional context
            related = getattr(trend, 'related_articles', []) or []
            if related:
                parts.append("\nRELATED CONTEXT:")
                for i, article in enumerate(related[:3], 1):
                    if article.get("title"):
                        parts.append(f"  {i}. {article['title']}")
                        if article.get("snippet"):
                            parts.append(f"     {article['snippet']}")

            jesse_angle = getattr(trend, 'jesse_angle', '') or ''
            if jesse_angle:
                parts.append(f"\nSUGGESTED ANGLE: {jesse_angle}")

            trend_body = "\n".join(parts)

            # Add angle seed from editorial calendar if available
            angle_instruction = ""
            if angle_seed:
                angle_instruction = f"""

═══════════════════════════════════════════════════════════════════════════════
EDITORIAL DIRECTION (from weekly strategy — follow this):
{angle_seed}
═══════════════════════════════════════════════════════════════════════════════
Your post MUST align with this editorial direction. The trend above is the raw material — the angle seed tells you HOW to approach it. Don't ignore this guidance."""

            trend_context = f"""
{trend_body}

IMPORTANT: React to the SPECIFIC news above. Reference the actual details, source, and cultural moment.
Do NOT start your post with "Today's trending headline:" or any preamble about the news — just react AS Jesse.
Don't create generic content. Don't summarize the headline. Find YOUR angle and write the post.{angle_instruction}
"""

            # Inject position context so Jesse builds on prior stances
            if self.memory and theme:
                try:
                    position_context = self.memory.get_position_context_for_generation(
                        theme=theme, days=30
                    )
                    if position_context:
                        trend_context += f"\n\n{position_context}\n"
                        logger.debug(f"Injected position context for theme={theme}")
                except Exception as e:
                    logger.debug(f"Position context lookup failed (non-blocking): {e}")

        # Map preferred_format string from calendar to PostFormat enum
        requested_format = None
        if preferred_format:
            try:
                from ..agents.content_strategist import PostFormat
                requested_format = PostFormat(preferred_format)
                logger.info(f"📋 Editorial calendar requests format: {preferred_format}")
            except (ValueError, ImportError):
                logger.warning(f"⚠️ Unknown calendar format '{preferred_format}', ignoring")

        # Pull structured angle from the trend so the generator can inject the
        # four fields directly (observation / take / concrete_details / tension)
        # instead of selecting a random methodology string.
        structured_angle = getattr(trend, 'structured_angle', None) if trend else None

        # Phase 1: pull the architect's blueprint (register / opinion / ski-jump /
        # brutal-honesty / STEPPS / first-49-char). Generator reads it and
        # picks the matching register's voice. None when architect unavailable
        # or failed — generator degrades to legacy single-register behavior.
        blueprint = getattr(trend, 'blueprint', None) if trend else None

        # Generate content
        post = await self.content_generator.execute(
            post_number=post_number,
            batch_id=batch_id,
            trending_context=trend_context,
            requested_format=requested_format,
            structured_angle=structured_angle,
            blueprint=blueprint,
        )
        
        # Generate media
        if self.image_generator:
            try:
                media_result = await self.image_generator.execute(post, use_video=use_video)
                
                if media_result.get("success"):
                    saved_path = media_result.get("saved_path") or media_result.get("path")
                    web_url = convert_to_web_url(saved_path, "video" if use_video else "image")
                    post.image_url = web_url
                    if use_video:
                        post.video_url = web_url
                        post.media_type = "video"
                    else:
                        post.media_type = "image"
                    logger.info(f"✅ Media: {web_url}")
            except Exception as e:
                logger.warning(f"Media generation failed: {e}")
        
        # Validate with revision loop — keep revising until approved or max attempts
        MAX_REVISION_ATTEMPTS = 3
        best_post = None
        best_score = 0

        validation_scores = await self._validate_post(post)
        approvals = sum(1 for v in validation_scores if v.approved)
        avg_score = sum(v.score for v in validation_scores) / len(validation_scores) if validation_scores else 0

        logger.info(f"Validation: {approvals}/3 approvals, avg: {avg_score:.1f}")

        # Track best version in case we never reach 2/3 approval
        if avg_score > best_score:
            best_score = avg_score
            best_post = post
            best_post.validation_scores = validation_scores

        attempt = 0
        while approvals < 2 and attempt < MAX_REVISION_ATTEMPTS:
            attempt += 1
            logger.info(f"Revision attempt {attempt}/{MAX_REVISION_ATTEMPTS} (had {approvals}/3 approvals)...")

            aggregated = await self.feedback_aggregator.execute(post, validation_scores)
            post = await self.revision_generator.execute(post, aggregated)

            validation_scores = await self._validate_post(post)
            approvals = sum(1 for v in validation_scores if v.approved)
            avg_score = sum(v.score for v in validation_scores) / len(validation_scores) if validation_scores else 0

            logger.info(f"Revision {attempt} result: {approvals}/3 approvals, avg: {avg_score:.1f}")

            if avg_score > best_score:
                best_score = avg_score
                best_post = post
                best_post.validation_scores = validation_scores

        if approvals >= 2:
            post.validation_scores = validation_scores
            return post

        # All revision attempts exhausted without 2-of-3 consensus.
        # REJECT the post — do NOT ship as "best version" fallback. The caller
        # inspects post.approval_count and treats this as rejected.
        # We still return the best attempt (rather than None) so it lands in
        # content_memory with was_approved=False for the supervisor to analyze.
        if best_post is None:
            best_post = post
            best_post.validation_scores = validation_scores
        logger.warning(
            f"❌ Max revisions reached with only {approvals}/3 approvals (best avg: {best_score:.1f}). "
            f"Post REJECTED — will not ship."
        )
        return best_post
    
    async def _maybe_promote_to_gold_standard(
        self,
        post_id: str,
        content: str,
        pillar: Optional[str],
        format_name: Optional[str],
        validation_scores,
        revision_count: int,
    ):
        """If the post is a clean 3-of-3 win, embed it and add to gold_standard_posts.

        Promotion criteria:
          - All three validators approved (not Jordan abstention)
          - Average score >= 8.5
          - Zero revisions (first-pass win — proves the generator hit the voice)
          - Not already in the gold-standard corpus (prefix-match dedup)

        This is the closed loop that makes retrieval get BETTER over time
        without manual curation. Every organically-great post becomes a voice
        anchor for future generations.
        """
        if not self.memory:
            return
        if not validation_scores:
            return

        # All three approved = True (including Jordan if genuine, not abstention)
        real_approvals = [
            vs for vs in validation_scores
            if vs.approved and not (vs.criteria_breakdown or {}).get("abstained")
        ]
        if len(real_approvals) < 3:
            return

        avg = sum(vs.score for vs in validation_scores) / len(validation_scores)
        if avg < 8.5 or revision_count > 0:
            return

        # Dedup: if this content (prefix) is already in the corpus, skip.
        try:
            import sqlite3 as _sq
            prefix = content.strip()[:80]
            with _sq.connect(self.memory.db_path) as conn:
                row = conn.execute(
                    "SELECT id FROM gold_standard_posts WHERE content LIKE ? LIMIT 1",
                    (prefix + "%",),
                ).fetchone()
            if row:
                logger.debug(f"  ↩️  Post {post_id} already in gold-standard corpus, skipping auto-promote")
                return
        except Exception as e:
            logger.debug(f"  dedup check failed ({e}), proceeding anyway")

        try:
            embedding = await self.ai_client.embed_text(content)
            if not embedding:
                logger.warning(f"  ⚠️  Auto-promote skipped (embedding failed) for {post_id}")
                return

            entry_id = self.memory.add_gold_standard_post(
                content=content.strip(),
                pillar=pillar,
                format=format_name,
                embedding=embedding,
                notes=f"Auto-promoted: clean 3-of-3 win (avg {avg:.1f}, 0 revisions)",
                curator="auto_promoted",
                source_post_id=post_id,
            )
            logger.info(
                f"  ⭐ Auto-promoted post {post_id} to gold-standard corpus "
                f"(avg {avg:.1f}, 3/3 approvals, id={entry_id})"
            )
        except Exception as e:
            logger.warning(f"  ⚠️  Auto-promote failed for {post_id}: {e}")

    async def _extract_and_store_position(
        self,
        post_id: str,
        content: str,
        trend=None,
    ):
        """Extract Jesse's position from an approved post and store it in memory."""
        if not self.position_extractor or not self.memory:
            return

        try:
            theme = getattr(trend, 'theme', None) or '' if trend else ''
            sub_theme = getattr(trend, 'sub_theme', None) or '' if trend else ''
            topic = trend.headline if trend else None

            position = await self.position_extractor.execute(
                post_content=content,
                theme=theme,
                topic=topic,
            )

            if position:
                self.memory.store_position(
                    post_id=post_id,
                    theme=theme,
                    sub_theme=sub_theme,
                    topic=topic,
                    position_summary=position.get("position_summary"),
                    sentiment=position.get("sentiment"),
                    key_claim=position.get("key_claim"),
                )
                logger.info(f"📌 Position stored for {post_id}: {position.get('sentiment')}")
            else:
                logger.debug(f"No position extracted for {post_id}")
        except Exception as e:
            logger.warning(f"Position extraction/storage failed (non-blocking): {e}")

    async def _validate_post(self, post: LinkedInPost) -> List[ValidationScore]:
        """Run all validators."""
        tasks = [v.execute(post) for v in self.validators]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        scores = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                scores.append(ValidationScore(
                    agent_name=self.validators[i].name,
                    score=5.0,
                    approved=False,
                    feedback=f"Error: {result}"
                ))
            else:
                scores.append(result)
        
        return scores
    
    async def generate_and_post_now(self, linkedin_poster, use_video: bool = False) -> Dict[str, Any]:
        """
        Generate fresh content and post immediately to LinkedIn.
        
        This is the RECOMMENDED method for automated posting because:
        - Always uses fresh trending topics (not stale queued content)
        - Generates and posts in one step
        - No queue management needed
        
        Args:
            linkedin_poster: LinkedInPoster instance
            use_video: Whether to generate video instead of image
            
        Returns:
            Dict with success status, post details, and LinkedIn result
        """
        import uuid
        from datetime import datetime
        
        logger.info("=" * 60)
        logger.info("🚀 GENERATE AND POST NOW - Fresh content pipeline")
        logger.info("=" * 60)
        
        try:
            # Start memory session for this live post
            if self.memory:
                self.memory.start_session(f"live_{uuid.uuid4().hex[:8]}")

            # Step 1: Determine post context (calendar + pillar starvation override)
            preferred_theme, angle_seed, preferred_format = self._determine_post_context()

            # Step 2: Reset trend tracking for fresh selection
            if self.trend_service:
                self.trend_service.reset_for_new_batch()

            # Step 3: Get curated trending topic (guided by calendar if available)
            post_id = f"live_{uuid.uuid4().hex[:8]}"
            trend = None
            if self.news_curator:
                curator_kwargs = {"post_id": post_id}
                if preferred_theme:
                    curator_kwargs["preferred_theme"] = preferred_theme
                trend = await self.news_curator.execute(**curator_kwargs)
                if trend:
                    logger.info(f"📰 Curated trend ({trend.category}): {trend.headline[:70]}...")
                else:
                    logger.warning("⚠️ No curated trend available, generating without trend")
            elif self.trend_service:
                trend = await self.trend_service.get_one_fresh_trend(post_id=post_id)
                if trend:
                    logger.info(f"📰 Fresh trend ({trend.category}): {trend.headline[:70]}...")
                else:
                    logger.warning("⚠️ No fresh trend available, generating without trend")

            # Phase 1: architect the angle BEFORE generation (live flow)
            if trend:
                await self._architect_angle(trend, pillar=preferred_theme, post_id=post_id)

            # Step 4: Generate content (with memory + calendar guidance)
            logger.info("✍️ Generating content...")
            post, validation_scores, was_approved = await self._process_single_post_with_memory(
                post_number=1,
                batch_id=post_id,
                trend=trend,
                use_video=use_video,
                angle_seed=angle_seed,
                preferred_format=preferred_format,
            )

            if not was_approved or not post:
                logger.error("❌ Content generation failed validation")
                if self.memory:
                    self.memory.end_session()
                return {
                    "success": False,
                    "error": "Content failed validation - no post generated",
                    "stage": "generation"
                }

            logger.info(f"✅ Content generated: {post.content[:50]}...")

            # Note: Position extraction already handled by _process_single_post_with_memory

            # Step 5: Post to LinkedIn
            logger.info(f"📤 Posting to LinkedIn... (media_type: {post.media_type})")
            linkedin_result = await asyncio.to_thread(
                linkedin_poster.publish_post,
                content=post.content,
                image_path=post.image_url if post.media_type != 'video' else None,
                video_path=post.video_url if post.media_type == 'video' else None,
                media_type=post.media_type,
                hashtags=[]  # No hashtags per client request
            )

            if linkedin_result.get("success"):
                logger.info(f"✅ Posted successfully: {linkedin_result.get('post_id')}")

                # Post CTA as first comment
                cta_result = await self._post_cta_comment(linkedin_result)

                # Mark trend as used (permanently) after successful post
                if self.trend_service and trend:
                    self.trend_service.mark_topic_used_permanent(trend, post_id=post_id)

                # Mark post as published in memory
                if self.memory:
                    self.memory.mark_posted_to_linkedin(
                        f"{post_id[:8]}_1",
                        linkedin_result.get('post_id', '')
                    )
                    # Update editorial calendar entry to 'posted'
                    if calendar_entry:
                        self.memory.update_calendar_status(calendar_entry["id"], "posted")
                    self.memory.end_session()

                return {
                    "success": True,
                    "post": post.to_dict(),
                    "linkedin": linkedin_result,
                    "cta_comment": cta_result,
                    "trend_used": {
                        "headline": trend.headline if trend else None,
                        "category": trend.category if trend else None
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                logger.error(f"❌ LinkedIn post failed: {linkedin_result.get('error')}")
                if self.memory:
                    self.memory.end_session()
                return {
                    "success": False,
                    "error": linkedin_result.get("error"),
                    "details": linkedin_result.get("details"),
                    "stage": "linkedin_post",
                    "post": post.to_dict()  # Include post so it can be manually posted
                }

        except Exception as e:
            logger.error(f"❌ Generate and post failed: {e}")
            import traceback
            traceback.print_exc()
            if self.memory:
                self.memory.end_session()
            return {
                "success": False,
                "error": str(e),
                "stage": "exception"
            }
    
    async def _post_cta_comment(self, linkedin_result: Dict[str, Any]) -> Dict[str, Any]:
        """Post a CTA comment on a successfully published LinkedIn post."""
        if not self.comment_service:
            logger.info("No comment service configured — skipping CTA comment")
            return {"skipped": True, "reason": "no_comment_service"}

        post_urn = linkedin_result.get("post_id")
        post_url = linkedin_result.get("url", "")

        if not post_urn and not post_url:
            logger.warning("No post URN or URL available — skipping CTA comment")
            return {"skipped": True, "reason": "no_post_identifier"}

        cta_text = random.choice(self.CTA_COMMENTS)

        try:
            result = await self.comment_service.post_comment(
                post_url=post_url,
                comment_text=cta_text,
                post_urn=post_urn
            )
            if result.get("success"):
                logger.info(f"✅ CTA comment posted: \"{cta_text}\"")
            else:
                logger.warning(f"⚠️ CTA comment failed: {result.get('error')}")
            return result
        except Exception as e:
            logger.warning(f"⚠️ CTA comment failed: {e}")
            return {"success": False, "error": str(e)}

    def get_stats(self):
        stats = {
            "validators": [v.name for v in self.validators],
            "trend_service": self.trend_service is not None,
            "news_curator": self.news_curator is not None,
            "image_generator": self.image_generator is not None,
            "memory": self.memory is not None
        }

        # Add memory stats if available
        if self.memory:
            try:
                stats["memory_stats"] = self.memory.get_stats()
            except Exception:
                pass

        return stats