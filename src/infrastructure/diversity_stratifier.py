"""
Diversity stratifier — Phase M (2026-04-22).

Sits between candidate-pool assembly (MultiTierTrendService) and the
news curator. Guarantees the curator sees a topically-balanced menu
instead of whatever source mix happens to dominate raw fetching.

Architecture:
    get_candidate_trends() → merge pool → stratify() → curator

Why this exists:
    Without this layer, Brave Search's 9 tech-heavy queries drown out
    Reddit / RSS / cultural sources. The curator picks the "best" but
    from a 80%-tech menu always picks tech. All Phase A-L downstream
    work (registers, comedy_moves, emotional_contact, validators) is
    architecturally valid — but operates on a monoculture input.

The stratifier preserves Phase A-L entirely. It only changes which
candidates the curator sees, not how anything downstream operates.

Technique grounding:
    - Techmeme pattern: bucket by topic, round-robin draw-one-per-bucket
    - MMR (Carbonell & Goldstein SIGIR 1998): diversity-aware rerank
    - Our similarity signal reuses extract_entities() from viral_signals.py
      (no new embeddings dependency)
"""

from __future__ import annotations

import logging
import re
import sqlite3
from collections import defaultdict
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


# Phase N (2026-04-22) — Non-US primary-subject detection.
# Curator's US-focus prompt keeps letting non-US stories through via LLM
# rationalization. Observed slippage:
#   - "Abuja wedding stopped the internet" (Nigerian local)
#   - "IndiGo oversold a flight" (Indian airline)
#   - "Lenskart changed dress code" (Indian eyewear chain)
#   - "₹1 Crore startup" (Indian currency)
# This pre-filter kills obvious foreign-subject trends before the curator
# sees them, so LLM rationalization can't bypass US-focus.
#
# Heuristic: if foreign marker appears in first 8 words AND no US marker
# is present in the first 8 words, treat as non-US. Conservative — "Trump
# meets in Tokyo" stays because "Trump" is a US marker.
_NON_US_CITY_MARKERS = re.compile(
    r"\b(?:Mumbai|Delhi|Bangalore|Chennai|Hyderabad|Kolkata|Pune|Ahmedabad|"
    r"Abuja|Lagos|Nairobi|Kinshasa|Cairo|"
    r"London|Manchester|Birmingham|Dublin|"
    r"Paris|Berlin|Munich|Frankfurt|Madrid|Barcelona|Rome|Milan|"
    r"Tokyo|Osaka|Seoul|Beijing|Shanghai|Shenzhen|Hong Kong|Taipei|"
    r"Dubai|Abu Dhabi|Riyadh|Doha|Karachi|Islamabad|Dhaka|Jakarta|"
    r"Manila|Kuala Lumpur|Singapore|Bangkok|Hanoi|Ho Chi Minh|"
    r"Sydney|Melbourne|Auckland|"
    r"Toronto|Montreal|Vancouver|"
    r"Moscow|Istanbul|Tehran|Baghdad|Damascus|"
    # Phase S+++ (2026-04-29) — country-name markers. Caught a "South
    # India beach vlogger" post that slipped through because no Indian
    # city was named. Country-level markers + regional sub-markers
    # (South India, North India, etc.) close the gap.
    r"South\s+India|North\s+India|"
    r"India|Pakistan|Bangladesh|Nepal|Sri\s+Lanka|"
    r"Nigeria|Kenya|Ghana|Ethiopia|Uganda|Tanzania|"
    r"Indonesia|Vietnam|Thailand|Philippines|Malaysia|"
    r"Egypt|Morocco|Algeria|Tunisia|"
    r"Iran|Iraq|Syria|Yemen|Afghanistan|"
    r"Ukraine|Belarus|Kazakhstan|"
    r"Argentina|Chile|Colombia|Peru|Venezuela|"
    r"Myanmar|Cambodia|Laos)\b",
    re.IGNORECASE,
)
_NON_US_COMPANY_MARKERS = re.compile(
    r"\b(?:Lenskart|IndiGo|Reliance\s+(?:Industries|Jio)|Tata\b|TCS|"
    r"Infosys|Wipro|Flipkart|Paytm|Zomato|Swiggy|Ola\s+(?:Cabs?)?|"
    r"Byju'?s|OYO|Nykaa|PhonePe|Zerodha|HCL\s+Tech|Mahindra|"
    r"Alibaba|Tencent|Baidu|Xiaomi|Huawei|ByteDance|TikTok\s+(?:China)?|"
    r"Samsung\s+India|Hyundai\s+India|Toyota\s+India|"
    r"Lenovo\b|Sony\s+India)\b",
    re.IGNORECASE,
)
# Phase S++ (2026-04-29) — non-US sports leagues + cricket/non-Western
# sports context. Slipped through Phase N filter: IPL 2026 cricket post
# about Vaibhav Sooryavanshi (16yo Indian cricketer) reached the queue.
# Cricket as primary sports context = non-US audience for Jesse's US
# LinkedIn followers. NBA/NFL/MLB/NHL stay exempt (US leagues).
_NON_US_SPORTS_MARKERS = re.compile(
    r"\b(?:"
    # Cricket leagues / governing bodies
    r"IPL\b|Indian\s+Premier\s+League|BCCI|PSL\b|Pakistan\s+Super\s+League|"
    r"BBL\b|Big\s+Bash\s+League|CPL\b|Caribbean\s+Premier\s+League|"
    r"T20\s+World\s+Cup|ICC\s+(?:World\s+Cup|Trophy)|"
    # Cricket as a sport (when primary subject)
    r"cricket\s+(?:match|game|league|player|team|tournament|series|World\s+Cup)|"
    # Non-US football (soccer-as-football for non-US audiences) + leagues
    r"Premier\s+League\s+(?:football|match|player|club)|EPL\b|La\s+Liga|"
    r"Bundesliga|Serie\s+A\s+football|Ligue\s+1|"
    # Olympics events that center non-US athletes (rare to flag here, but
    # included for completeness when the headline frames a non-US athlete)
    # Rugby leagues (mostly non-US)
    r"Six\s+Nations|Premiership\s+Rugby|Super\s+Rugby"
    r")\b",
    re.IGNORECASE,
)
_NON_US_CURRENCY_MARKERS = re.compile(
    r"(?:₹|€|£|¥|₩|₽|Rs\.?\s*\d|INR\s*\d|EUR\s*\d|GBP\s*\d|"
    r"\b(?:crore|lakh|yuan|yen|won|rupee|ruble|peso|real|rand|shilling)s?\b)",
    re.IGNORECASE,
)
_US_MARKERS = re.compile(
    # US politicians, companies, places, agencies — if present in first
    # 8 words, exempt the trend even if a foreign marker also appears
    r"\b(?:Trump|Biden|Harris|Obama|Pelosi|Schumer|McConnell|"
    r"Musk|Zuckerberg|Bezos|Cook|Pichai|Nadella|Altman|Huang|"
    r"Meta|OpenAI|Anthropic|Google|Amazon|Microsoft|Apple|Nvidia|"
    r"Netflix|Tesla|Uber|Airbnb|SpaceX|Twitter|X\s+Corp|"
    r"NBA|NFL|MLB|NHL|NCAA|WWE|UFC|NASCAR|"
    r"Democrat|Republican|Congress|Senate|House|SCOTUS|"
    r"FBI|CIA|NSA|DOJ|SEC|FDA|FTC|IRS|"
    r"NYC|New\s+York|Los\s+Angeles|LA\b|Chicago|Houston|Boston|"
    r"Washington|San\s+Francisco|SF\b|Seattle|Atlanta|Miami|"
    r"Texas|California|Florida|Virginia|"
    r"Hollywood|Silicon\s+Valley|Wall\s+Street)\b",
    re.IGNORECASE,
)


def _is_non_us_primary_subject(trend: Any) -> bool:
    """Heuristic: does this trend's headline center on a non-US subject?

    Checks:
      - First 8 words of headline for foreign city/company/currency
      - If found, exempt when US marker also in first 8 words

    Returns:
        True if trend should be filtered out as non-US primary subject.
    """
    headline = (getattr(trend, "headline", "") or "").strip()
    summary = (getattr(trend, "summary", "") or "").strip()
    if not headline:
        return False
    first_chunk = " ".join(headline.split()[:12])  # first ~12 words

    # Phase S++ — also scan summary for sports markers. Some headlines
    # don't contain the league name (e.g. "Nauman Niaz jokes about AI chip
    # in Vaibhav Sooryavanshi's bat") but the summary always has IPL/cricket
    # context. The non-US sports filter sees the league name in EITHER field.
    sports_text = headline + " " + summary[:300]

    has_foreign = bool(
        _NON_US_CITY_MARKERS.search(first_chunk)
        or _NON_US_COMPANY_MARKERS.search(first_chunk)
        or _NON_US_CURRENCY_MARKERS.search(first_chunk)
        or _NON_US_SPORTS_MARKERS.search(sports_text)
    )
    if not has_foreign:
        return False

    # Exempt if a US marker is ALSO in the first chunk (e.g., "Trump
    # threatens Iran" has Trump + Iran — keep it, Trump is the subject)
    has_us = bool(_US_MARKERS.search(first_chunk))
    return not has_us


# Collapse granular source categories into 6 top-level buckets the
# curator can actually rotate across. New categories should map here
# when added — otherwise they fall into "other".
BUCKET_MAP: Dict[str, str] = {
    # AI / tech-business
    "ai_news": "ai_business",
    "ai_labor": "ai_business",
    "ai_economy": "ai_business",
    "ai_slop": "ai_business",
    "ai_safety": "ai_business",
    "breaking_tech": "ai_business",
    "economic_pulse": "ai_business",
    "economy": "ai_business",
    # Politics / civic
    "politics_hot": "politics",
    "scandal_beat": "politics",
    "political_moment": "politics",
    "civic_moment": "politics",
    # Social / viral
    "trending_viral": "social_viral",
    "internet_discourse": "social_viral",
    "social_pulse": "social_viral",
    "viral_moment": "social_viral",
    "social_media_moment": "social_viral",
    # Culture / celebrity / sports
    "celebrity_moment": "culture",
    "sports_moment": "culture",
    "entertainment": "culture",
    "cultural_moment": "culture",
    "pop_culture": "culture",
    "meditations": "culture",
    "rituals": "culture",
    # Corporate-absurdism
    "corporate_absurd": "corporate_absurd",
    "corporate_pratfall": "corporate_absurd",
    "brand_moment": "corporate_absurd",
    "consumer_absurd": "corporate_absurd",
    # Fallback
    "top_us_news": "other",
    "trending": "other",
    "general": "other",
}


def _canonical_bucket(category: Optional[str]) -> str:
    """Map raw category string to one of 6 canonical buckets."""
    return BUCKET_MAP.get((category or "").lower().strip(), "other")


def _recent_buckets(db_path: str, n: int = 5) -> Set[str]:
    """Read categories of the last N used_topics and return their canonical
    buckets. Used for hard-filter: don't repeat a bucket used recently.
    """
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            # Table name may vary — try used_topics first (trend_service's
            # table), fall back to content_memory if that's how it's tracked
            try:
                rows = cursor.execute(
                    "SELECT category FROM used_topics "
                    "ORDER BY used_at DESC LIMIT ?",
                    (n,),
                ).fetchall()
            except sqlite3.OperationalError:
                rows = cursor.execute(
                    "SELECT pillar FROM content_memory "
                    "WHERE pillar IS NOT NULL "
                    "ORDER BY created_at DESC LIMIT ?",
                    (n,),
                ).fetchall()
        return {_canonical_bucket(r[0]) for r in rows if r and r[0]}
    except Exception as e:
        logger.debug(f"_recent_buckets lookup failed: {e}")
        return set()


def _saturated_entities(db_path: str, n: int = 10, min_occurrences: int = 2) -> Set[str]:
    """Phase S++ (2026-04-29) — extract named entities from last N
    committed posts and return any that appear in `min_occurrences`+ posts.

    Solves the 'Comey 3 batches in a row' problem: a named subject
    (Comey, Trump, Musk, Apple, etc.) saturating the recent feed should
    block new candidates featuring that same subject — even when the
    headlines are different stories about them.

    Phase S+++ (2026-04-29) — bumped default window 5 → 10 posts +
    extended timestamp filter from 3 days → 7 days. Comey appeared in
    4 of last 8 days but Phase S++'s 5-post window let him slip back
    in once a busy day pushed him out. 10-post / 7-day window catches
    sustained-subject saturation across slower news days.

    Returns a set of saturated entity strings (lowercase). Caller filters
    candidates whose entity set intersects this saturated set.
    """
    try:
        from .viral_signals import extract_entities
    except ImportError:
        return set()

    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            try:
                rows = cursor.execute(
                    "SELECT content, trending_topic FROM content_memory "
                    "WHERE created_at >= datetime('now', '-7 days') "
                    "ORDER BY created_at DESC LIMIT ?",
                    (n,),
                ).fetchall()
            except sqlite3.OperationalError:
                return set()

        # Count entity appearances across recent posts
        entity_post_count: Dict[str, int] = {}
        for row in rows:
            content = row[0] or ""
            trending = row[1] or ""
            text = f"{trending} {content[:200]}"  # focus on headline + opener
            ents = extract_entities(text) or set()
            # Each entity counts ONCE per post (set conversion already does this)
            for e in ents:
                e_lower = e.lower().strip()
                if not e_lower or len(e_lower) < 3:
                    continue
                entity_post_count[e_lower] = entity_post_count.get(e_lower, 0) + 1

        saturated = {
            e for e, count in entity_post_count.items()
            if count >= min_occurrences
        }
        if saturated:
            logger.info(
                f"🎯 Saturated entities (≥{min_occurrences}/{n} recent posts): "
                f"{sorted(saturated)}"
            )
        return saturated
    except Exception as e:
        logger.debug(f"_saturated_entities failed: {e}")
        return set()


def _jaccard(a: Set[str], b: Set[str]) -> float:
    """Jaccard similarity over entity sets. 1.0 = identical, 0 = disjoint."""
    if not a and not b:
        return 0.0
    if not a or not b:
        return 0.0
    return len(a & b) / max(1, len(a | b))


def _mmr_select(
    candidates: List[Any],
    entities_for: List[Set[str]],
    k: int,
    lam: float = 0.5,
) -> List[Any]:
    """MMR re-rank over entity-Jaccard similarity.

    Relevance proxy = cluster_score normalized to [0, 1].
    Diversity penalty = max Jaccard similarity with already-picked items.

    Carbonell & Goldstein SIGIR 1998 formula:
        MMR = argmax [λ·Rel(i) - (1-λ)·max_j Sim(i, j)]
    """
    if not candidates:
        return []
    if k <= 0:
        return []

    # Normalize cluster_score → relevance in [0, 1]
    scores = [float(getattr(c, "cluster_score", 0) or 0) for c in candidates]
    max_cs = max(scores) if scores else 1
    if max_cs <= 0:
        max_cs = 1
    rel = [s / max_cs for s in scores]

    picked: List[int] = []
    remaining = list(range(len(candidates)))

    while remaining and len(picked) < k:
        best_i = remaining[0]
        best_score = -1e9
        for i in remaining:
            max_sim = 0.0
            for j in picked:
                sim = _jaccard(entities_for[i], entities_for[j])
                if sim > max_sim:
                    max_sim = sim
            score = lam * rel[i] - (1 - lam) * max_sim
            if score > best_score:
                best_i = i
                best_score = score
        picked.append(best_i)
        remaining.remove(best_i)

    return [candidates[i] for i in picked]


def stratify(
    candidates: List[Any],
    db_path: str,
    slate_size: int = 8,
    avoid_recent: int = 2,
    lam: float = 0.5,
    sibling_buckets: Optional[List[str]] = None,
) -> List[Any]:
    """Return a balanced, deduped, diversity-ranked slate for the curator.

    Process:
        1. Pre-filter obvious non-US primary-subject trends (Phase N)
        2. Group candidates into 6 canonical buckets
        3. Hard-filter buckets used in last `avoid_recent` posts AND
           buckets used by in-batch committed siblings (Phase N)
        4. If filtering empties the pool too much, fall back to soft-penalty
           MMR over everything (don't block the pipeline)
        5. Round-robin draw one from each surviving bucket (Techmeme)
        6. MMR-rank the leftover candidates to fill slate_size

    Args:
        candidates: raw candidate trends from get_candidate_trends()
        db_path: path to the SQLite DB (for recent-buckets lookup)
        slate_size: how many candidates to return for the curator (default 8)
        avoid_recent: window for hard-filter (default 2 = avoid buckets
            used in the last 2 committed posts)
        lam: MMR lambda — 0.5 = balance relevance and diversity equally
        sibling_buckets: buckets already used by in-batch committed
            siblings. Added to avoid_recent's set to prevent same-batch
            repeats (Phase N — fixes the Nike+Lenskart both-PR-apology bug).

    Returns:
        Up to slate_size candidates, topically balanced.
    """
    if not candidates:
        return []

    # Phase N (2026-04-22) — pre-filter non-US primary-subject trends.
    # Runs BEFORE bucketing so LLM curator can't rationalize foreign
    # stories into the pool. See _is_non_us_primary_subject heuristic.
    non_us_count = 0
    us_candidates: List[Any] = []
    for c in candidates:
        if _is_non_us_primary_subject(c):
            non_us_count += 1
            logger.info(
                f"🌎 Stratifier: dropped non-US primary-subject trend — "
                f"'{(getattr(c, 'headline', '') or '')[:70]}...'"
            )
        else:
            us_candidates.append(c)
    if non_us_count:
        logger.info(
            f"🌎 Stratifier: filtered {non_us_count} non-US trend(s) — "
            f"{len(us_candidates)} US-focused candidates remain"
        )
    # If filter wipes everything, fall back to raw pool (don't block pipeline)
    if us_candidates:
        candidates = us_candidates
    else:
        logger.warning(
            "🌎 Stratifier: all candidates flagged non-US — falling back to "
            "raw pool (better to ship something than nothing)"
        )

    # Phase S++ (2026-04-29) — entity-saturation filter.
    # Solves the 'Comey 3 batches in a row' problem. If a named entity
    # (Comey, Trump, Musk, etc.) has appeared as primary subject in
    # ≥2 of the last 5 committed posts, drop new candidates featuring
    # that entity. The bucket-rotation gate doesn't catch this because
    # multiple Comey stories can land in different buckets (politics,
    # social_viral, corporate_absurd) — but readers still see "Comey
    # again."
    try:
        from .viral_signals import extract_entities as _extract_ents
        # Phase S+++ — widened window 5 → 10 posts + 3 days → 7 days
        # to catch sustained-subject saturation (Comey across batches)
        saturated = _saturated_entities(db_path, n=10, min_occurrences=2)
        if saturated:
            entity_dropped = 0
            entity_kept: List[Any] = []
            for c in candidates:
                ent_text = f"{getattr(c, 'headline', '')} {getattr(c, 'summary', '') or ''}"
                cand_ents = {e.lower().strip() for e in (_extract_ents(ent_text) or set())}
                # Drop if ANY of the candidate's entities is saturated
                overlap = cand_ents & saturated
                if overlap:
                    entity_dropped += 1
                    logger.info(
                        f"🎯 Entity-saturation drop: '{(getattr(c, 'headline', '') or '')[:60]}...'"
                        f" — saturated entity: {sorted(overlap)}"
                    )
                else:
                    entity_kept.append(c)
            # Don't wipe pool entirely — fall back if filter empties everything
            if entity_kept:
                candidates = entity_kept
                if entity_dropped:
                    logger.info(
                        f"🎯 Entity-saturation: filtered {entity_dropped} candidate(s) "
                        f"featuring saturated subjects"
                    )
            elif entity_dropped:
                logger.warning(
                    "🎯 Entity-saturation: would empty pool — keeping raw "
                    "(better to ship a saturated subject than nothing)"
                )
    except Exception as e:
        logger.debug(f"Entity-saturation filter failed (non-blocking): {e}")

    # Compute entity sets once (we reuse viral_signals — this is the
    # same extractor the curator already uses for entity-overlap checks)
    try:
        from .viral_signals import extract_entities
    except ImportError:
        logger.debug("viral_signals unavailable — stratifier degrades to raw")
        return candidates[:slate_size]

    entities_for: List[Set[str]] = []
    for c in candidates:
        text = f"{getattr(c, 'headline', '') or ''} {getattr(c, 'summary', '') or ''}"
        try:
            entities_for.append(extract_entities(text))
        except Exception:
            entities_for.append(set())

    # Bucket by canonical category
    buckets: Dict[str, List[int]] = defaultdict(list)
    for idx, c in enumerate(candidates):
        bucket = _canonical_bucket(getattr(c, "category", None))
        buckets[bucket].append(idx)

    bucket_dist = {b: len(v) for b, v in buckets.items()}
    logger.info(f"🪣 Stratifier input: {bucket_dist}")

    # Hard-filter: drop buckets used in last-N-posts unless this would
    # leave us with too few candidates. Phase N: also unions buckets used
    # by committed siblings in the current batch, so Nike-PR-apology +
    # Lenskart-PR-apology can't both land in the same batch.
    recent = _recent_buckets(db_path, n=avoid_recent)
    if sibling_buckets:
        sibling_set = {b for b in sibling_buckets if b}
        if sibling_set:
            logger.info(
                f"🪣 Stratifier: in-batch sibling buckets added to avoid: "
                f"{sorted(sibling_set)}"
            )
            recent = recent | sibling_set
    filtered_buckets: Dict[str, List[int]] = {
        b: idxs for b, idxs in buckets.items() if b not in recent
    }
    total_filtered = sum(len(v) for v in filtered_buckets.values())

    if total_filtered < min(3, len(candidates)):
        # Fallback — filter would empty pool. Keep all buckets, let MMR
        # handle diversity via soft penalty instead.
        logger.info(
            f"🪣 Stratifier: hard-filter would drop too many (only "
            f"{total_filtered} survived) — falling back to soft-penalty MMR"
        )
        filtered_buckets = dict(buckets)
    else:
        dropped_buckets = set(buckets.keys()) - set(filtered_buckets.keys())
        if dropped_buckets:
            logger.info(
                f"🪣 Stratifier: dropped {sorted(dropped_buckets)} "
                f"(used in last {avoid_recent} posts)"
            )

    # Round-robin draw one-per-bucket, then MMR on the rest
    slate: List[Any] = []
    leftover_idxs: List[int] = []

    for bucket_name, idxs in filtered_buckets.items():
        bucket_cands = [candidates[i] for i in idxs]
        bucket_ents = [entities_for[i] for i in idxs]
        ranked = _mmr_select(bucket_cands, bucket_ents, k=len(bucket_cands), lam=lam)
        if ranked:
            slate.append(ranked[0])
            # Remaining from this bucket go to leftover pool
            leftover_idxs.extend(idxs[1:])  # simplistic but fine for typical batch size

    # Fill remaining slate via MMR over leftover pool
    if len(slate) < slate_size and leftover_idxs:
        leftover_cands = [candidates[i] for i in leftover_idxs]
        leftover_ents = [entities_for[i] for i in leftover_idxs]
        remaining_slots = slate_size - len(slate)
        extras = _mmr_select(leftover_cands, leftover_ents, k=remaining_slots, lam=lam)
        slate.extend(extras)

    final_slate = slate[:slate_size]
    final_buckets = [
        _canonical_bucket(getattr(c, "category", None)) for c in final_slate
    ]
    logger.info(
        f"🪣 Stratifier output: {len(final_slate)} candidates across "
        f"{len(set(final_buckets))} buckets → {final_buckets}"
    )
    return final_slate
