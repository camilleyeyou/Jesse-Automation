#!/usr/bin/env python3
"""
Seed gold_standard_posts with Liquid-Death-shaped Jesse voice specimens.

The Coachella specimens nail the clinical-scaffold register. The failure mode
that keeps surfacing (post-2026-04-18) is sincere-essay voice: "There's
something genuinely moving about the last day at a job you loved..." — no
absurdist hook, no dread named directly, no commitment to the bit.

These six specimens apply the Liquid Death hook architecture to Jesse's
subject matter:
  - Hook is a PROVOCATION / DECLARATION / CONFRONTATION, never a setup
  - Existential dread is NAMED directly, then defused by deadpan tone
  - Full commitment to an absurd frame (no winking, no earnestness)
  - Short sentences. Punchlines not reveals.

One specimen per pillar, plus a second for the_who_profits (where AI layoffs
/ replacement / obsolescence content concentrates).

Writes data/seeds/gold_standard_liquid_death.json with pre-computed
embeddings. On deploy the autoseed loader picks up the file (if it hasn't
been loaded yet) and inserts into gold_standard_posts.

Usage:
    python scripts/seed_gold_from_liquid_death.py
"""

import asyncio
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv()

from src.infrastructure.config.config_manager import AppConfig
from src.infrastructure.ai.openai_client import OpenAIClient


SPECIMENS = [
    {
        "content": (
            "Humans, an update: you are still mortal. Meta has been notified "
            "and is adjusting headcount accordingly.\n\n"
            "The algorithm that recommended your layoff does not have a desk "
            "to clear. It does not know what a Tuesday afternoon feels like "
            "when your badge stops working. It does, however, know how to "
            "ship the press release that calls this an efficiency gain.\n\n"
            "Nothing personal. Everything procedural. The lips, for the "
            "record, remain fully analog."
        ),
        "pillar": "the_who_profits",
        "format": "dread_declarative",
        "notes": (
            "Liquid-Death hook architecture: opener is direct confrontation "
            "('you are still mortal'), dread named immediately, defused by "
            "matter-of-fact tone. Clinical observer voice throughout. The "
            "product beat ('lips remain fully analog') is a quiet character "
            "detail in the final sentence, not the point."
        ),
    },
    {
        "content": (
            "Consciousness was a beta feature. It never made it to production.\n\n"
            "You have been running on it for thirty-four years anyway. "
            "Pay-to-stay structure. Unfixable known issues: existential "
            "dread, object permanence applied to ex-partners, the inability "
            "to stop thinking about a 2am text.\n\n"
            "The AI analyzing your tweets does not have this problem. The "
            "AI does not have a 2am."
        ),
        "pillar": "the_why_it_matters",
        "format": "absurd_declarative",
        "notes": (
            "Absurd declarative opener treats consciousness as a buggy "
            "software feature. Dread (existential, relational, insomnia-"
            "coded) named in a bulleted-spec register — the frame is the "
            "joke. The close lands by denying the AI the one thing the "
            "reader just spent the post describing."
        ),
    },
    {
        "content": (
            "Stop panicking about the algorithm replacing you. It already "
            "did. You just haven't noticed because it's letting you finish "
            "the sentence.\n\n"
            "The quarterly report is clean. Productivity is up. The humans "
            "included in 'productivity' got smaller by 8,000 this quarter. "
            "This is not a bug. This is the spec.\n\n"
            "The report does not come with a warning label. The report "
            "works exactly as intended."
        ),
        "pillar": "the_who_profits",
        "format": "confrontational_command",
        "notes": (
            "Opener is a direct command that names the dread and "
            "immediately collapses the time horizon ('it already did'). "
            "Pseudo-procedural language ('spec', 'intended', 'warning "
            "label') treats a human disaster as a completed software ticket."
        ),
    },
    {
        "content": (
            "Good news: you are going to die.\n\n"
            "Better news: so is everyone who bullied you in middle school, "
            "everyone who currently out-earns you, and every AI model "
            "currently being rolled out to replace your function.\n\n"
            "The only thing outlasting any of us is chapped lips and the "
            "specific way your grandmother wrote the number seven. Plan "
            "accordingly."
        ),
        "pillar": "the_how_to_cope",
        "format": "inverted_reassurance",
        "notes": (
            "Inverted reassurance — 'good news' followed by mortality. The "
            "classic Liquid Death move of naming the scariest thing first, "
            "then defusing it with matter-of-fact comedy. Product beat "
            "appears but as an ABSURD contrast (chapped lips outlasting "
            "capitalism), not a pitch."
        ),
    },
    {
        "content": (
            "Clinical finding: the internet is making you worse. You are "
            "already aware of this.\n\n"
            "You checked it seven times writing this sentence. You will "
            "check it again before you finish reading it. The algorithm "
            "does not have a dopamine system. It is operating your dopamine "
            "system as a managed service.\n\n"
            "You are the loop. The loop is not you."
        ),
        "pillar": "the_what",
        "format": "clinical_finding",
        "notes": (
            "Clinical-finding opener treats reader's own behavior as a "
            "pathology on a chart. Second-person direct address ('you "
            "checked it seven times') is confrontational — implicates the "
            "reader in their own dread. SaaS vocabulary ('managed service') "
            "applied to the human dopamine system is the absurd frame."
        ),
    },
    {
        "content": (
            "Humans, a heads-up: the AI does not want to kill you. It wants "
            "to recommend content to you. These are not the same problem. "
            "They have the same ending.\n\n"
            "The alignment paper does not mention this. The alignment "
            "paper is very long. The recommendation algorithm is shorter. "
            "Shorter things ship faster."
        ),
        "pillar": "the_what_if",
        "format": "dread_update",
        "notes": (
            "AI safety pillar done in Liquid Death register: dread-as-"
            "heads-up, then defuses via category error (death vs "
            "recommendations have the same ending). Observation about "
            "shipping speed is deadpan literal — no moralizing."
        ),
    },
]


def main():
    out_path = ROOT / "data" / "seeds" / "gold_standard_liquid_death.json"
    print(f"Embedding {len(SPECIMENS)} Liquid-Death-shaped specimens...")

    cfg = AppConfig.from_yaml(str(ROOT / "config" / "config.yaml"))
    if not cfg.openai.api_key and not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY required for embedding.")
        sys.exit(1)

    client = OpenAIClient(cfg)

    async def embed_all():
        results = []
        for i, spec in enumerate(SPECIMENS, 1):
            print(f"  [{i}/{len(SPECIMENS)}] embedding {spec['format']:28s} ({spec['pillar']})")
            emb = await client.embed_text(spec["content"])
            if not emb:
                print(f"      ⚠ embed returned empty; skipping")
                continue
            results.append({
                **spec,
                "curator": "seed:gold_standard_liquid_death.json",
                "embedding": emb,
            })
        return results

    embedded = asyncio.run(embed_all())

    payload = {
        "version": 1,
        "source": "scripts/seed_gold_from_liquid_death.py — Liquid-Death-shaped opener register, 2026-04-19",
        "specimens": embedded,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(payload, f, indent=2)

    print(f"\n✅ Wrote {len(embedded)} specimens to {out_path.relative_to(ROOT)}")
    print("   Autoseed will pick up this file on next startup (per-file idempotent).")


if __name__ == "__main__":
    main()
