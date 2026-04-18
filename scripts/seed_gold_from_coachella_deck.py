#!/usr/bin/env python3
"""
Seed gold_standard_posts with canonical Jesse voice specimens from the
Coachella "Team Orange Sticker" activation deck.

The system was designed to bootstrap retrieval from LinkedIn engagement data,
but that's circular on a fresh install (no posts → no engagement → no
retrieval → drifting voice → worse posts). The Coachella deck already contains
hand-crafted, approved-canon Jesse voice. These specimens serve the same role
the retrieval system wants: voice-by-example.

Idempotent: re-running updates existing rows instead of duplicating.

Usage:
    python scripts/seed_gold_from_coachella_deck.py
"""

import asyncio
import os
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv()

from src.infrastructure.memory.agent_memory import AgentMemory
from src.infrastructure.config.config_manager import AppConfig
from src.infrastructure.ai.openai_client import OpenAIClient


# Each specimen ships as a full post-shaped block (40-100 words) that mirrors
# how it would appear on LinkedIn. Notes capture what's doing the work so
# reviewers can see WHY this example was chosen.
SPECIMENS = [
    {
        "content": (
            "THIRST QUOTIENT: 8.7 / 10. "
            "CLASSIFICATION: HYPER-ARID SOCIAL DESICCATION. "
            "Subject exhibits acute Desert Pout Syndrome — a condition where the desire for "
            "engagement leads to severe labial compression in high-UV environments. The ocular "
            "squint indicates a chronic deficit of both hydration and humility, while the "
            "proximity to actual cacti suggests skin currently competing for the same limited "
            "groundwater resources. "
            "CLINICAL ROAST: You look like a raisin trying to pass as a fresh grape at a Palm "
            "Springs pool party."
        ),
        "pillar": "the_what",  # AI slop — we ARE the slop brand with clinical standards
        "format": "clinical_diagnosis",
        "notes": "Full clinical scaffold: score → classification → expert evaluation → roast. Every clause adds specific detail. Pseudo-scientific voice played dead straight.",
    },
    {
        "content": (
            "THIRST QUOTIENT: 8.9 / 10. "
            "CLASSIFICATION: SOLAR-POWERED PUCKER SYNDROME. "
            "Subject presents with severe labial compression and exaggerated buccal puckering, "
            "suggesting high-pressure social environment combined with direct solar exposure. "
            "Epidermal glare from the cranial region indicates critical moisture deficit, while "
            "facial musculature is strained in a classic trying-to-look-smoldering-but-actually-"
            "looks-like-he-just-ate-a-lemon configuration. "
            "CLINICAL ROAST: If you pucker any harder, you're going to create a localized black "
            "hole that sucks in every Instagram filter within a ten-mile radius."
        ),
        "pillar": "the_why_it_matters",
        "format": "clinical_diagnosis",
        "notes": "Earned the clinical opener by following through with specific anatomical detail. The roast lands because the diagnosis preceded it.",
    },
    {
        "content": (
            "THIRST QUOTIENT: 7.8 / 10. "
            "CLASSIFICATION: HIGH-NOON BALCONY DEHYDRATION. "
            "Subject presents with advanced ocular shielding and significant solar exposure. "
            "Clinical evaluation of the labial region indicates catastrophic moisture deficit, "
            "likely exacerbated by a beard that functions as a natural desiccant. Social thirst "
            "markers elevated — manifesting as the classic vacation-flex selfie trope in direct, "
            "unforgiving sunlight. "
            "CLINICAL ROAST: You look like a tech support manager who finally snapped and moved "
            "to Sedona to find himself and some decent fish tacos."
        ),
        "pillar": "the_why_it_matters",
        "format": "clinical_diagnosis",
        "notes": "Observation of a real social pattern (vacation-flex selfie). Specific details: beard, Sedona, tech support. No hedging.",
    },
    {
        "content": (
            "The Glowasis: a sanctuary of Anti-Vibe. "
            "It's not just air conditioning; it's a biological reset button. "
            "The lighting is medical-grade soothing. "
            "The sound isn't music; it's a frequency designed to stop your headache. "
            "We aren't selling chapstick. We're selling relief."
        ),
        "pillar": "the_how_to_cope",
        "format": "philosophy",
        "notes": "Uses 'it's not X, it's Y' three times — each with substantive follow-through. Short, confident, every clause earns its place. The 'selling relief' thesis lands because the setup is specific.",
    },
    {
        "content": (
            "Humans design for vibes. AI designs for biology. "
            "We ingested five years of Coachella site maps, meteorological data, and ten "
            "thousand social media complaints about heat. Then we asked the model to "
            "mathematically solve for Maximum Relief. The result: a structure optimized for "
            "shade efficiency and sensory deprivation. Brown Noise. Cooling Blue Light. "
            "Heart rates drop faster than any human-designed tent."
        ),
        "pillar": "the_what",
        "format": "contrast",
        "notes": "Crisp two-beat opening. Concrete numbers (5 years, 10,000 complaints). No throat-clearing. The AI-sells-lip-balm irony sits in the subtext, not the surface.",
    },
    {
        "content": (
            "Jesse A. Eisenbalm: Official Sponsor of the Desert. "
            "We aren't selling chapstick. We're selling relief. "
            "The driest brand on earth, going to the thirstiest place on earth. "
            "Full commitment. No winking."
        ),
        "pillar": "the_why_it_matters",
        "format": "observation",
        "notes": "Mock-institutional framing. 'Official Sponsor of the Desert' is absurd but delivered like a press release. The meta-line — 'Full commitment. No winking.' — doubles as brand philosophy and as a joke.",
    },
    {
        "content": (
            "Epidermal Lipid Repair: The Biophysical Efficacy of Lip Protectants in Xeric "
            "Environments. Jesse A. Eisenbalm presents a rigorous examination of the vermillion "
            "border under conditions of sustained moisture deficit. We are not describing "
            "chapstick. We are describing the structural integrity of the one interface between "
            "your interior and the atmosphere. Your lips: the last honest thing you own."
        ),
        "pillar": "the_why_it_matters",
        "format": "philosophy",
        "notes": "Pseudo-academic title held with complete commitment. 'The vermillion border' — anatomical term used unironically. Ends on a line that's both absurd and kind of true.",
    },
    {
        "content": (
            "Scan face. Get roasted. Get discount. "
            "The Thirst Trapp doesn't apply filters. It returns diagnoses. Upload a selfie; "
            "receive a Thirst Quotient, a formal Classification, and a clinical roast generated "
            "by an AI that has seen too many Palm Springs pool party posts. "
            "This isn't a filter. It's a diagnosis."
        ),
        "pillar": "the_what",
        "format": "list_subversion",
        "notes": "Three-beat scaffolding at the top (Scan → Roast → Discount). The 'isn't a filter / it's a diagnosis' reframe lands because the middle paragraph earned it with specifics.",
    },
    {
        "content": (
            "We aren't selling chapstick. We're selling relief. "
            "This is not a product line. It's a clinical intervention against the specific "
            "dryness of late-capitalist attention economies. Every tube is hand-numbered because "
            "mass production is for people who haven't examined their lip-to-screen ratio this "
            "quarter. Your moisture deficit is not your fault. Your moisture deficit is "
            "absolutely addressable."
        ),
        "pillar": "the_how_to_cope",
        "format": "philosophy",
        "notes": "The core thesis extended into a post. 'Lip-to-screen ratio' — invented metric played straight. 'Not your fault / absolutely addressable' lands the clinical tone with kindness.",
    },
    {
        "content": (
            "The Intervention: we generated a personalized video of your friend stranded in a "
            "desert, narrated by an AI that sells lip balm, begging you to buy a twelve-pack. "
            "This shouldn't work. It shouldn't be allowed. We didn't ask if it should be — we "
            "asked if it could be. It could. It is. "
            "Your friend is currently, technically, in the desert."
        ),
        "pillar": "the_what",
        "format": "story",
        "notes": "The double-satire at full throttle: AI bragging about AI doing something mildly unsettling for a lip balm brand. The final line is a perfect abrupt-stop ending.",
    },
]


def upsert_specimens():
    print(f"Seeding {len(SPECIMENS)} specimens from the Coachella deck.")
    cfg = AppConfig.from_yaml("config/config.yaml")
    if not cfg.openai.api_key and not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY required for embedding.")
        sys.exit(1)
    client = OpenAIClient(cfg)
    memory = AgentMemory()

    async def embed_all():
        results = []
        for spec in SPECIMENS:
            emb = await client.embed_text(spec["content"])
            results.append((spec, emb))
        return results

    embedded = asyncio.run(embed_all())

    # Use a single connection for the upsert
    inserted = 0
    updated = 0
    skipped = 0
    with sqlite3.connect(memory.db_path) as conn:
        cursor = conn.cursor()
        for spec, emb in embedded:
            if not emb:
                print(f"  ✗ embedding failed: {spec['content'][:50]}...")
                skipped += 1
                continue

            blob = AgentMemory._encode_embedding(emb)

            # Idempotent: match on a stable prefix of content (first 60 chars)
            # rather than on curator+content exact match, so re-running with
            # minor edits replaces the old row.
            prefix = spec["content"][:60]
            cursor.execute(
                "SELECT id FROM gold_standard_posts WHERE content LIKE ? LIMIT 1",
                (prefix + "%",),
            )
            existing = cursor.fetchone()

            if existing:
                cursor.execute(
                    """UPDATE gold_standard_posts
                       SET content = ?, pillar = ?, format = ?, embedding = ?,
                           notes = ?, curator = ?
                       WHERE id = ?""",
                    (spec["content"], spec["pillar"], spec["format"], blob,
                     spec["notes"], "coachella_deck", existing[0]),
                )
                updated += 1
                print(f"  ↻ updated  [{spec['pillar']:20s}] {spec['content'][:55]}…")
            else:
                cursor.execute(
                    """INSERT INTO gold_standard_posts
                       (content, pillar, format, embedding, notes, curator, source_post_id)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (spec["content"], spec["pillar"], spec["format"], blob,
                     spec["notes"], "coachella_deck", None),
                )
                inserted += 1
                print(f"  + inserted [{spec['pillar']:20s}] {spec['content'][:55]}…")
        conn.commit()

    total = memory.count_gold_standard_posts()
    print()
    print(f"Inserted: {inserted}, updated: {updated}, skipped: {skipped}")
    print(f"Total gold-standard corpus: {total}")


if __name__ == "__main__":
    upsert_specimens()
