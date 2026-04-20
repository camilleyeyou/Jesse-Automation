"""
Viral-signal scoring for candidate trends.

Implements the "Techmeme trick": a story that 6 independent sources covered
in the last 4 hours is objectively hotter than a story 1 niche newsletter
wrote about. This module scores cross-source convergence so the curator
has an external signal to ground its recognizability judgment against.

Separate research synthesis (2026-04-20) identified 3 signals that matter
for "top viral story":
  1. Cross-source convergence — N sources, same entity cluster, short window
  2. Social velocity — Reddit/HN rank as proxy for share-velocity
  3. Named-entity saturation — hot stories always feature a recognizable
     proper noun; no proper noun = probably not on Morning Joe tomorrow

Phase A + B implements #1 and #3 + a light version of #2 (Reddit/HN source
tier as signal). Keeps it free + dependency-free — uses only stdlib regex
and set ops. No spaCy, no NLTK, no paid APIs.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Any, Dict, List, Optional, Set, Tuple


# Common English words that get capitalized at sentence start — filter to
# avoid false-positive "entities" like "The" or "This" or "Here"
_SENTENCE_START_WORDS = frozenset({
    "the", "a", "an", "this", "that", "these", "those", "here", "there",
    "it", "its", "his", "her", "their", "our", "my", "your",
    "he", "she", "they", "we", "you", "i", "who", "what", "when",
    "where", "why", "how", "if", "then", "but", "and", "or", "so",
    "yet", "because", "although", "while", "just", "only", "more",
    "most", "less", "much", "some", "any", "all", "every", "each",
    "to", "of", "in", "on", "at", "by", "for", "with", "from", "as",
    "is", "are", "was", "were", "be", "been", "being", "has", "have",
    "had", "do", "does", "did", "can", "could", "will", "would", "should",
    "may", "might", "must", "shall",
    # News-wire common starts
    "new", "news", "breaking", "report", "reports", "reported", "says",
    "said", "today", "yesterday", "tomorrow", "now", "recent", "recently",
    "latest", "update", "updated", "exclusive", "first", "last", "next",
})

# Common capitalized words that AREN'T entities (months, days, common
# uppercase adjectives that appear at sentence start)
_COMMON_CAPS_NON_ENTITY = frozenset({
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
    "january", "february", "march", "april", "may", "june", "july",
    "august", "september", "october", "november", "december",
    "spring", "summer", "fall", "autumn", "winter",
    "monday", "morning", "afternoon", "evening", "night",
})

# Low-info acronyms — too common to signal a specific story. Two stories
# that share only "AI" or "US" are not the same story. These are DROPPED
# from the entity set for clustering (but still acceptable as keywords).
_LOW_INFO_ACRONYMS = frozenset({
    "ai", "us", "uk", "eu", "un", "ok", "vs", "pm", "am",
    "ceo", "cfo", "cto", "coo", "cmo", "vp", "md",
    "it", "tv", "pr", "hr", "pc", "os", "ui", "ux", "api",
    # These CAN be entity-relevant (e.g. "GPT") but are so common in tech
    # news they over-cluster — leave out for now, can re-add if missing specific stories
})


def _norm_token(s: str) -> str:
    """Lowercase + strip punctuation for set-based matching."""
    return re.sub(r"[^\w]", "", s).lower()


def extract_entities(text: str) -> Set[str]:
    """Extract proper-noun entity candidates from text.

    Strategy:
      1. Find all-caps acronyms of length 2-6 (FBI, NATO, SCOTUS, IPO, AI).
      2. Find CamelCase compound words (OpenAI, ChatGPT, SpaceX, TikTok).
      3. Find multi-word capitalized sequences (Taylor Swift, New York Times).
      4. Find single capitalized words — anywhere — filtered against a
         common-English-starter list (rejects "The", "Here", "Now" but
         keeps "Trump", "Meta", "Musk").
      5. Dollar amounts ($8B, $115-135B).

    Returns lowercased entity tokens. Multi-word entities stored as
    space-separated strings.
    """
    if not text:
        return set()

    entities: Set[str] = set()

    # 1. All-caps acronyms (FBI, SCOTUS, NATO, etc). 2-6 caps.
    # Filter low-info acronyms ("AI", "US", "CEO") that are too generic to
    # signal a specific story — they over-cluster unrelated posts.
    acronym_re = re.compile(r"\b([A-Z]{2,6})\b")
    for m in acronym_re.finditer(text):
        acronym = m.group(1).lower()
        if acronym in {"i", "a"} or acronym in _LOW_INFO_ACRONYMS:
            continue
        entities.add(acronym)

    # 2. CamelCase compound words: OpenAI, ChatGPT, SpaceX, YouTube, TikTok,
    # iPhone etc. Pattern: optional lowercase leader + 2+ caps-lowercase runs
    # E.g. "OpenAI" = Open + AI; "ChatGPT" = Chat + GPT; "SpaceX" = Space + X
    camel_re = re.compile(r"\b[A-Za-z]*[A-Z][a-z]+[A-Z][a-zA-Z]*\b")
    for m in camel_re.finditer(text):
        word = m.group(0)
        if len(word) >= 3:
            entities.add(word.lower())

    # 3. Multi-word capitalized sequences (2+ consecutive Cap words)
    multi_word_re = re.compile(
        r"\b[A-Z][a-zA-Z]+(?:\s+(?:[A-Z][a-zA-Z]+|of|the|and|&)\s*){1,4}[A-Z][a-zA-Z]+\b"
    )
    for m in multi_word_re.finditer(text):
        phrase = m.group(0).strip()
        tokens_lower = [t.lower() for t in phrase.split()]
        # Drop leading articles/connectors so "The New York Times" matches "New York Times"
        while tokens_lower and tokens_lower[0] in {"the", "a", "an", "of", "and"}:
            tokens_lower.pop(0)
        if len(tokens_lower) < 2:
            continue
        entities.add(" ".join(tokens_lower))

    # 4. Single capitalized words of length 4+ that aren't common starters.
    # This catches "Trump", "Meta", "Musk" at sentence-start — the previous
    # lookbehind approach was dropping them. Filter does the work instead.
    single_cap_re = re.compile(r"\b([A-Z][a-z]{3,})\b")
    for m in single_cap_re.finditer(text):
        word = m.group(1).lower()
        if word in _SENTENCE_START_WORDS or word in _COMMON_CAPS_NON_ENTITY:
            continue
        entities.add(word)

    # 5. Dollar amounts ($8B, $115-135B, $4 billion)
    money_re = re.compile(r"\$\d[\d,.\-]*\s*(?:[BMK]|billion|million|trillion)?", re.IGNORECASE)
    for m in money_re.finditer(text):
        entities.add(m.group(0).lower().strip())

    return entities


def extract_salient_keywords(text: str, top_k: int = 5) -> Set[str]:
    """Extract non-stopword keywords from text as fallback cluster signal.

    Complements entity extraction — two stories about Meta's layoffs should
    cluster even if they phrase "Meta" differently (e.g. "Meta Platforms
    Inc." vs "Meta"). Keyword overlap provides a second signal.

    Returns lowercase tokens of length 4+, stopwords removed.
    """
    if not text:
        return set()

    stopwords = _SENTENCE_START_WORDS | _COMMON_CAPS_NON_ENTITY | frozenset({
        "about", "after", "again", "against", "also", "amid", "around",
        "before", "between", "both", "during", "into", "just", "like",
        "over", "same", "since", "still", "such", "than", "through",
        "under", "until", "upon", "when", "where", "which", "while",
        "would", "could", "should", "might", "must", "shall", "into",
        "year", "years", "month", "months", "week", "weeks", "day", "days",
        "hour", "hours", "minute", "minutes", "second", "seconds",
        "thing", "things", "time", "times", "way", "ways", "make", "made",
        "making", "get", "got", "getting", "take", "took", "taking",
        "come", "came", "coming", "goes", "went", "going",
        "people", "someone", "anyone", "everyone", "nobody", "many", "most",
        "other", "others", "another", "across", "within", "without",
    })

    # Tokenize and normalize
    words = re.findall(r"\b[a-zA-Z]{4,}\b", text.lower())
    words = [w for w in words if w not in stopwords]

    if not words:
        return set()

    # Frequency-based pick
    counts = Counter(words)
    top_words = [w for w, _ in counts.most_common(top_k)]
    return set(top_words)


def candidate_feature_set(headline: str, summary: str = "") -> Dict[str, Set[str]]:
    """Build the feature set used for clustering comparison.

    Returns a dict with:
      - 'entities': high-confidence proper-noun entities
      - 'keywords': salient keywords (fallback signal)
      - 'named_entity_present': True if entities has >=1 meaningful proper noun
    """
    text = f"{headline or ''} {summary or ''}".strip()
    entities = extract_entities(text)
    keywords = extract_salient_keywords(text)
    return {
        "entities": entities,
        "keywords": keywords,
        "named_entity_present": bool(entities),
    }


def score_cluster(
    target_features: Dict[str, Any],
    all_features: List[Dict[str, Any]],
    entity_threshold: int = 1,
    keyword_threshold: int = 2,
) -> Tuple[int, List[int]]:
    """Score how many OTHER candidates cluster with the target.

    A candidate C clusters with target T if:
      - C shares >= entity_threshold entities with T, OR
      - C shares >= keyword_threshold salient keywords with T (fallback)

    Returns (cluster_size, peer_indices). cluster_size counts the target
    itself, so a story with no peers has cluster_size=1.

    cluster_size >= 3 means at least 3 independent sources wrote about the
    same entity-cluster — strong "this is hot" signal.
    """
    target_entities = target_features.get("entities", set())
    target_keywords = target_features.get("keywords", set())

    peers: List[int] = []
    for i, feat in enumerate(all_features):
        if feat is target_features:
            continue  # don't count self
        # Primary: entity overlap
        overlap_entities = len(target_entities & feat.get("entities", set()))
        if overlap_entities >= entity_threshold:
            peers.append(i)
            continue
        # Fallback: keyword overlap (only when BOTH have few entities — stories
        # that share proper nouns are much stronger signal than keyword-only)
        if (
            len(target_entities) < 2
            and len(target_keywords & feat.get("keywords", set())) >= keyword_threshold
        ):
            peers.append(i)

    # +1 for self so cluster_size is the total count
    return len(peers) + 1, peers


def annotate_candidates_with_viral_signals(
    candidates: List[Any],
) -> None:
    """Attach cluster_score, cluster_peers, and named_entity_present to each
    candidate trend object in-place.

    Called once per candidate-pool fetch, before the curator evaluates. The
    curator's prompt then receives these as objective features the LLM
    can't self-inflate.

    Operates in-place: sets `candidate.cluster_score`, `candidate.cluster_peers`,
    `candidate.named_entity_present` as attributes.

    Safe to call on any object — falls back to setattr if attribute doesn't
    pre-exist on the TrendingNews dataclass.
    """
    if not candidates:
        return

    # Compute features for every candidate once
    feature_list: List[Dict[str, Any]] = []
    for c in candidates:
        headline = getattr(c, "headline", "") or ""
        summary = getattr(c, "summary", "") or ""
        feature_list.append(candidate_feature_set(headline, summary))

    # Score each candidate against all others
    for i, c in enumerate(candidates):
        cluster_size, peers = score_cluster(feature_list[i], feature_list)
        # Attach as attributes — not all TrendingNews subclasses declare these,
        # so use setattr which always works
        try:
            setattr(c, "cluster_score", cluster_size)
            setattr(c, "cluster_peers", peers)
            setattr(c, "named_entity_present", feature_list[i]["named_entity_present"])
            # Store small debug payload for post-diagnostics — the top entities
            # the candidate matched on. Caps to avoid log spam.
            top_entities = sorted(feature_list[i]["entities"])[:6]
            setattr(c, "viral_entities", top_entities)
        except Exception:
            # Some exotic object types may not accept setattr — skip silently
            pass
