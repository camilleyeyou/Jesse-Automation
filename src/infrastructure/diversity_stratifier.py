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
import sqlite3
from collections import defaultdict
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


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
) -> List[Any]:
    """Return a balanced, deduped, diversity-ranked slate for the curator.

    Process:
        1. Group candidates into 6 canonical buckets
        2. Hard-filter buckets used in last `avoid_recent` posts
        3. If filtering empties the pool too much, fall back to soft-penalty
           MMR over everything (don't block the pipeline)
        4. Round-robin draw one from each surviving bucket (Techmeme)
        5. MMR-rank the leftover candidates to fill slate_size

    Args:
        candidates: raw candidate trends from get_candidate_trends()
        db_path: path to the SQLite DB (for recent-buckets lookup)
        slate_size: how many candidates to return for the curator (default 8)
        avoid_recent: window for hard-filter (default 2 = avoid buckets
            used in the last 2 committed posts)
        lam: MMR lambda — 0.5 = balance relevance and diversity equally

    Returns:
        Up to slate_size candidates, topically balanced.
    """
    if not candidates:
        return []

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
    # leave us with too few candidates
    recent = _recent_buckets(db_path, n=avoid_recent)
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
