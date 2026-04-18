#!/usr/bin/env python3
"""
Curate gold-standard posts for retrieval-augmented voice grounding (Fix #4).

Reads the top-engagement approved posts from content_memory, shows each to the
human reviewer, and lets them accept/reject/skip. Accepted posts get embedded
with text-embedding-3-small and written to gold_standard_posts.

The generator uses this corpus at runtime to learn voice by example, replacing
the ~400-line voice description that used to live in the system prompt.

Usage:
    python scripts/curate_gold_standard.py               # interactive (top 30)
    python scripts/curate_gold_standard.py --limit 50    # more candidates
    python scripts/curate_gold_standard.py --status      # show current count
    python scripts/curate_gold_standard.py --dry-run     # preview candidates without writing

Env:
    OPENAI_API_KEY — required for embedding (text-embedding-3-small)
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

# Make src/ importable when running this script directly
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.infrastructure.memory.agent_memory import AgentMemory
from src.infrastructure.config.config_manager import AppConfig
from src.infrastructure.ai.openai_client import OpenAIClient


def _shorten(text: str, width: int = 100) -> str:
    text = (text or "").replace("\n", " ")
    return text if len(text) <= width else text[: width - 1] + "…"


def print_status(memory: AgentMemory):
    total = memory.count_gold_standard_posts()
    print(f"\nGold-standard corpus: {total} posts with embeddings\n")
    if total == 0:
        print("No gold-standard posts yet. Run without --status to curate some.")


async def curate(limit: int, dry_run: bool):
    memory = AgentMemory()

    candidates = memory.get_top_engagement_posts_for_curation(limit=limit)
    if not candidates:
        print(
            "No approved posts with engagement found. Seed some engagement data via\n"
            "PerformanceIngestionJob before curating."
        )
        return

    print(f"Loaded {len(candidates)} top-engagement candidates.\n")
    if dry_run:
        for i, p in enumerate(candidates, 1):
            eng = p["reactions"] + p["comments"] + p["shares"]
            print(f"[{i:02d}] pillar={p['pillar']}  eng={eng}  {_shorten(p['content'])}")
        return

    # Need OpenAI client for embeddings
    cfg = AppConfig.from_yaml("config/config.yaml")
    if not cfg.openai.api_key and not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY not set — can't embed accepted posts.")
        sys.exit(1)
    client = OpenAIClient(cfg)

    accepted = 0
    rejected = 0
    skipped = 0

    for i, p in enumerate(candidates, 1):
        eng = p["reactions"] + p["comments"] + p["shares"]
        print("─" * 80)
        print(f"[{i}/{len(candidates)}]  pillar={p['pillar']}  format={p['format']}  engagement={eng}")
        print()
        print(p["content"])
        print()

        while True:
            choice = input("Accept into gold-standard? [y]es / [n]o / [s]kip / [q]uit: ").strip().lower()
            if choice in ("y", "yes"):
                note = input("Optional note (why this works, press Enter to skip): ").strip() or None
                embedding = await client.embed_text(p["content"])
                if not embedding:
                    print("  → embedding failed, skipping this post.")
                    skipped += 1
                    break
                memory.add_gold_standard_post(
                    content=p["content"],
                    pillar=p["pillar"],
                    format=p["format"],
                    embedding=embedding,
                    notes=note,
                    curator=os.getenv("USER", "manual"),
                    source_post_id=p.get("post_id"),
                )
                accepted += 1
                print(f"  ✓ accepted (total accepted so far: {accepted})")
                break
            elif choice in ("n", "no"):
                rejected += 1
                break
            elif choice in ("s", "skip", ""):
                skipped += 1
                break
            elif choice in ("q", "quit"):
                print("\nQuitting early.")
                print(f"Accepted {accepted}, rejected {rejected}, skipped {skipped}")
                return
            else:
                print("  Choose y / n / s / q.")

    total = memory.count_gold_standard_posts()
    print()
    print("═" * 80)
    print(f"Curation complete.")
    print(f"  Accepted this run: {accepted}")
    print(f"  Rejected: {rejected}")
    print(f"  Skipped: {skipped}")
    print(f"  Total gold-standard corpus: {total}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=30,
                        help="How many top-engagement candidates to present (default 30)")
    parser.add_argument("--status", action="store_true",
                        help="Show current gold-standard count and exit")
    parser.add_argument("--dry-run", action="store_true",
                        help="List candidates without writing anything")
    args = parser.parse_args()

    if args.status:
        print_status(AgentMemory())
        return

    asyncio.run(curate(args.limit, args.dry_run))


if __name__ == "__main__":
    main()
