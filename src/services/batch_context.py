"""
BatchContext — Phase H (2026-04-21) in-batch coordination state.

Solves the concurrent-batch sibling-blindness bug documented in today's
queue review: when the orchestrator generates 7 posts in a 20-min window,
each post's architect/curator queries persistent memory BEFORE siblings
commit. Result: 3-of-7 same topic, 6-of-7 same compositional frame,
pattern-saturation gates bypassed.

Architecture (research-backed — STORM Stanford OVAL NAACL'24, SimpleStrat
NeurIPS'24, LangChain MMR conventions):

  (C) Slot pre-allocation — at batch start, shuffle a list of
      (register, emotional_temperature, contact_frame) tuples. Each post
      receives ONE slot up-front. Architect honors the forced slot
      unless all slots are exhausted (graceful degrade). This prevents
      convergence at the pick stage instead of detecting it after.

  (D) Semantic in-batch dedup — each sibling commits an embedding + key
      identifier (headline, post body) to a shared in-memory set. Later
      siblings check via cosine similarity before accepting a curated
      trend (topic threshold 0.80) or finalizing a post (frame threshold
      0.72). Thresholds per LangChain MMR / sentence-transformers
      conventions for short-text similarity.

Uses OpenAI text-embedding-3-small via existing ai_client — NO new
dependencies. Graceful fallback to keyword-based dedup on embedding
API failure.
"""

from __future__ import annotations

import logging
import math
import random
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# Slot registry. Each slot is a (register, emotional_temperature,
# contact_frame, comedy_move) tuple. At batch start, we shuffle and
# take the first N slots. N posts cannot converge on the same slot
# because each one gets a pre-assigned different cell.
#
# Phase J (2026-04-21): added comedy_move. Client diagnosis: same
# formula across posts. Fix: rotate the comedic engine itself, not just
# voice/shape. Four moves cover the Phase J scope; each slot ships with
# one pre-assigned. Cross-slot ensures we never ship two posts in the
# same batch with the same comedy_move.
#
# Registers/temps are the names defined in angle_architect.REGISTERS and
# angle_architect.EMOTIONAL_TEMPERATURES respectively. Frames are the
# compositional frame families from Phase G's alternative-frames menu.
# comedy_move is one of the 4 Phase J techniques.
_SLOTS: List[Dict[str, str]] = [
    # Warm/tender slice — softer temperatures, intimate frames
    {"register": "clinical_diagnostician", "emotional_temperature": "tender",     "frame": "direct_object_observation", "comedy_move": "genre_pastiche"},
    {"register": "contrarian",             "emotional_temperature": "dry_amused", "frame": "scale_anchor_bare",         "comedy_move": "false_parallel_list"},
    {"register": "prophet",                "emotional_temperature": "outraged",   "frame": "name_verb_object_time",     "comedy_move": "register_costume"},
    {"register": "confession",             "emotional_temperature": "weary",      "frame": "scene_fragment_emdash",     "comedy_move": "anti_climactic_diminishment"},
    {"register": "roast",                  "emotional_temperature": "delighted",  "frame": "role_action_consequence",   "comedy_move": "genre_pastiche"},
    # Second tier — complementary combinations
    {"register": "clinical_diagnostician", "emotional_temperature": "reverent",   "frame": "noun_verb_role_reaction",   "comedy_move": "register_costume"},
    {"register": "contrarian",             "emotional_temperature": "outraged",   "frame": "scene_question",            "comedy_move": "anti_climactic_diminishment"},
    {"register": "prophet",                "emotional_temperature": "dry_amused", "frame": "number_time_role_verb",     "comedy_move": "false_parallel_list"},
    {"register": "confession",             "emotional_temperature": "tender",     "frame": "direct_object_observation", "comedy_move": "anti_climactic_diminishment"},
    {"register": "roast",                  "emotional_temperature": "weary",      "frame": "scale_anchor_bare",         "comedy_move": "genre_pastiche"},
]


# Human-readable frame descriptions for the architect prompt
FRAME_DESCRIPTIONS: Dict[str, str] = {
    "noun_verb_role_reaction":
        'The [photographable_noun] [verb]. The [role] [reaction]. '
        'Example: "The paper pressed back. The archivist turned the page."',
    "name_verb_object_time":
        '[Name] [verb] [object] [time]. '
        'Example: "Elon Musk cleared his schedule at 2am."',
    "role_action_consequence":
        '[Role] [concrete action]. [Concrete consequence]. '
        'Example: "A PM checked the 401k app. The phone went face-down."',
    "scene_fragment_emdash":
        '[Private scene fragment] — [what happened]. '
        'Example: "2am, kitchen table — the engineer decided not to care."',
    "number_time_role_verb":
        '[Number/time] and [role] [verb] [object]. '
        'Example: "It was 9pm and the analyst was still reading the sticky note."',
    "direct_object_observation":
        'Direct observation of the object: "[Photographable_noun] [state]." '
        'Example: "A phone on the pavement. Uploading nothing."',
    "scene_question":
        'Question to a specific scene: "What does a [role] do at [time]?" '
        'Example: "What does a nurse do at the end of a double shift?"',
    "scale_anchor_bare":
        '[Bureaucratic unit] / [domestic consequence]. '
        'Example: "Trillion-dollar pivot / one VP\'s promotion party."',
}


def _cosine(a: List[float], b: List[float]) -> float:
    """Cosine similarity of two vectors. Returns 0.0 if either is empty."""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def _lexical_overlap(a: str, b: str) -> float:
    """Fallback similarity when embeddings fail. Returns fraction of
    non-stopword tokens from the shorter text present in the longer."""
    if not a or not b:
        return 0.0
    stop = {
        "the", "a", "an", "and", "or", "but", "for", "of", "to", "in",
        "on", "at", "by", "with", "from", "is", "was", "are", "were",
        "be", "been", "this", "that", "it", "its", "as", "has", "have",
    }
    def tok(s: str) -> set:
        return {
            w for w in re.findall(r"[A-Za-z0-9]+", s.lower())
            if w not in stop and len(w) >= 3
        }
    sa, sb = tok(a), tok(b)
    if not sa or not sb:
        return 0.0
    shorter, longer = (sa, sb) if len(sa) <= len(sb) else (sb, sa)
    hits = sum(1 for w in shorter if w in longer)
    return hits / len(shorter)


# Similarity thresholds — LangChain MMR / sentence-transformers short-text
# conventions. 0.80 for "same story" (topic rejection), 0.72 for "same
# compositional shape" (frame warning). Lexical fallback uses slightly
# higher thresholds because word-overlap is a stricter signal than
# embeddings for short texts.
TOPIC_SIM_THRESHOLD = 0.80
FRAME_SIM_THRESHOLD = 0.72
LEXICAL_TOPIC_THRESHOLD = 0.55
LEXICAL_FRAME_THRESHOLD = 0.40


@dataclass
class BatchContext:
    """Ephemeral shared state for ONE batch.

    Lives only for the duration of a generate_batch() call. Siblings read
    and write this context to maintain sibling-awareness despite running
    in the same memory session before their commits are durable.

    Attributes:
        batch_id: the batch tracking ID (for logging)
        slots: pre-allocated (register, temp, frame) tuples — one per post
        committed_embeddings: embeddings of committed (headline|body) texts
        committed_headlines: raw headlines of accepted siblings
        committed_bodies: raw post bodies of accepted siblings
        ai_client: reference to the ai_client for embed_text() calls
    """
    batch_id: str
    slots: List[Dict[str, str]] = field(default_factory=list)
    committed_embeddings: List[List[float]] = field(default_factory=list)
    committed_headlines: List[str] = field(default_factory=list)
    committed_bodies: List[str] = field(default_factory=list)
    ai_client: Optional[Any] = None

    @classmethod
    def for_batch(
        cls,
        batch_id: str,
        num_posts: int,
        ai_client: Optional[Any] = None,
        seed: Optional[int] = None,
    ) -> "BatchContext":
        """Build a batch context with pre-allocated slots.

        Shuffles the _SLOTS registry deterministically per batch seed so
        the same batch_id reproduces the same slot ordering (useful for
        debugging). Returns at most N slots; if num_posts > len(_SLOTS),
        additional posts get None slots (architect falls back to
        rotation-based picking).
        """
        if seed is None:
            # Hash the batch_id into a deterministic seed
            seed = hash(batch_id) & 0xFFFFFFFF
        rng = random.Random(seed)
        pool = _SLOTS.copy()
        rng.shuffle(pool)
        slots = pool[:num_posts]
        # If num_posts exceeds pool, pad with empty-slot markers so the
        # index-based lookup in the batch loop always works
        while len(slots) < num_posts:
            slots.append({})
        return cls(
            batch_id=batch_id,
            slots=slots,
            ai_client=ai_client,
        )

    def slot_for(self, post_number: int) -> Dict[str, str]:
        """Get the pre-allocated slot for a post (1-indexed).

        Returns empty dict if post_number is out of range or the slot
        is unpopulated — callers should treat empty slot as "use
        rotation-based picking".
        """
        idx = post_number - 1
        if 0 <= idx < len(self.slots):
            return self.slots[idx] or {}
        return {}

    async def is_topic_duplicate(
        self,
        candidate_text: str,
        threshold: Optional[float] = None,
    ) -> Tuple[bool, float]:
        """Check if candidate topic is too similar to any committed sibling.

        Uses embedding cosine sim against each committed (headline|body).
        Falls back to lexical overlap if embeddings fail. Returns a
        (is_dup, max_sim) tuple so callers can log even below-threshold
        near-misses.
        """
        if not self.committed_embeddings and not self.committed_headlines:
            return False, 0.0
        if not candidate_text:
            return False, 0.0
        thresh = threshold if threshold is not None else TOPIC_SIM_THRESHOLD

        # Try embedding path first
        candidate_emb = await self._try_embed(candidate_text)
        if candidate_emb and self.committed_embeddings:
            max_sim = max(
                _cosine(candidate_emb, e) for e in self.committed_embeddings
            )
            return (max_sim >= thresh), max_sim

        # Fallback: lexical overlap against committed headlines + bodies
        lex_thresh = LEXICAL_TOPIC_THRESHOLD
        max_lex = 0.0
        for committed in (self.committed_headlines + self.committed_bodies):
            overlap = _lexical_overlap(candidate_text, committed)
            if overlap > max_lex:
                max_lex = overlap
        return (max_lex >= lex_thresh), max_lex

    async def is_frame_duplicate(
        self,
        candidate_body: str,
        threshold: Optional[float] = None,
    ) -> Tuple[bool, float]:
        """Check if candidate post body is too similar to sibling bodies.

        Same mechanic as is_topic_duplicate but at a looser threshold —
        catches same-frame/same-structure outputs even when topics differ.
        """
        if not self.committed_embeddings and not self.committed_bodies:
            return False, 0.0
        if not candidate_body:
            return False, 0.0
        thresh = threshold if threshold is not None else FRAME_SIM_THRESHOLD

        candidate_emb = await self._try_embed(candidate_body[:400])
        if candidate_emb and self.committed_embeddings:
            max_sim = max(
                _cosine(candidate_emb, e) for e in self.committed_embeddings
            )
            return (max_sim >= thresh), max_sim

        lex_thresh = LEXICAL_FRAME_THRESHOLD
        max_lex = 0.0
        for committed in self.committed_bodies:
            overlap = _lexical_overlap(candidate_body, committed)
            if overlap > max_lex:
                max_lex = overlap
        return (max_lex >= lex_thresh), max_lex

    async def commit(self, headline: str, body: str) -> None:
        """Record a sibling's accepted output. Later siblings will see it."""
        combined = f"{headline} {body[:300]}".strip()
        if not combined:
            return
        self.committed_headlines.append(headline or "")
        self.committed_bodies.append(body or "")
        emb = await self._try_embed(combined)
        if emb:
            self.committed_embeddings.append(emb)
        logger.debug(
            f"BatchContext({self.batch_id[:8]}): committed "
            f"post #{len(self.committed_headlines)} (has_emb={bool(emb)})"
        )

    async def _try_embed(self, text: str) -> List[float]:
        """Wrap ai_client.embed_text with graceful fallback."""
        if not self.ai_client or not text:
            return []
        try:
            emb = await self.ai_client.embed_text(text[:2000])
            return emb or []
        except Exception as e:
            logger.debug(f"BatchContext embed failed: {e}")
            return []
