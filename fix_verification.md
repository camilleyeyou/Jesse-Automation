# Four-Fix Content Quality Remediation — Verification Record

Date: 2026-04-17
Scope: Content quality fixes to the Jesse A. Eisenbalm generation pipeline.
Each fix was applied in isolation with its own verification.

---

## Fix #1 — Pipe the `jesse_angle` through as a structured four-field angle

### Diagnosis (carried forward)

The news curator was generating a `jesse_angle` string and attaching it to the
trend, but the strategist's `execute()` only received a `trending_context: str`.
The angle never arrived. Then the strategist's `_generate_specific_angle()` did
`random.choice()` over six generic methodology strings ("React to the news.
Don't summarize it.") — which aren't angles. Under that load the generator
regressed to the most densely reinforced system-prompt pattern: "Diagnosed:
[Condition Name]".

### What changed

- `src/infrastructure/trend_service.py` — added `structured_angle: Optional[dict]`
  field to `TrendingNews`.
- `src/agents/news_curator.py`
  - Rewrote the output-format section to require four discrete fields:
    `observation` (what Jesse noticed), `take` (Jesse's one-sentence POV),
    `concrete_details` (array of real strings from the source, minimum 3),
    `tension` (where claim and reality diverge).
  - Parses those fields from the response and writes them to
    `trend.structured_angle`. Also keeps a legacy `jesse_angle` string for
    backward compat with anything that still reads the freeform form.
  - Logs each structured field at INFO level; warns when the curator returns none.
- `src/agents/content_strategist.py`
  - Added `StructuredAngle` dataclass with `is_usable()` gating (requires `take`
    + at least one anchor).
  - Added `structured_angle` kwarg to `execute()`. Accepts either a dataclass or a
    raw dict.
  - Killed the `random.choice()` fallback in `_generate_specific_angle()`. When a
    structured angle is present, the prompt injects the four fields verbatim.
    When a trend is present but no structured angle, the strategist gives the
    generator a single grounded instruction instead of rolling dice. When there's
    no trend at all (evergreen posts), a small LLM call derives an angle —
    replacing the hardcoded-list random selection.
  - Added `_build_angle_block()` that renders the four fields as a prominent
    prompt block labeled "express this — do not regenerate it".
  - Added `_coherent_voice_and_ending()` — a small LLM call (still on
    GPT-4o-mini) that picks the `voice_modifier` and `ending_style` that actually
    fit the angle, instead of six independent dice rolls.
- `src/services/orchestrator.py` — extracts `trend.structured_angle` and
  forwards it to `content_generator.execute(structured_angle=...)`.

### Verification

Structural plumbing verified with synthetic tests:
- `StructuredAngle.from_dict` + `is_usable()` correctly gate on take + anchor.
- `TrendingNews.structured_angle` round-trips.
- `_build_angle_block()` renders the four fields as a prompt block when present
  and falls back to the legacy slot when absent.
- Orchestrator passes the angle through to the strategist.

**Not verified here** (requires live API + running service): that Claude, given
a real angle, references the concrete details in its output; that the
"Diagnosed:" opener stops dominating generations; that the tension surfaces in
posts. Those checks belong to a live 3-post dry-run the user can do via
`POST /api/automation/generate-content` once keys are set.

---

## Fix #2 — Switch the generator to Claude Sonnet

### Diagnosis

GPT-4o-mini collapses into template openers under the weight of the 400-line
system prompt. Sonnet holds character voice better at higher temperature and is
stronger with specific-detail metaphors.

### What changed

- `src/infrastructure/config/config_manager.py` — added `AnthropicConfig` with
  model=`claude-sonnet-4-6`, temperature=0.9, max_tokens=600, timeout=60.
  Wired to the singleton `AppConfig`. `ANTHROPIC_API_KEY` env var supported.
- `config/config.yaml` — added `anthropic:` section with the same defaults.
- `requirements.txt` — added `anthropic>=0.30.0`.
- `src/infrastructure/ai/openai_client.py`
  - Added an `AsyncAnthropic` client in `__init__` (graceful when SDK/key missing).
  - Added `_infer_provider(model)` — routes by prefix: `claude-*` → anthropic,
    `gemini-*` → google (text), default → openai.
  - Extended `generate()` with routing. The OpenAI path is unchanged.
  - Added `_generate_with_anthropic()` that speaks to `messages.create`, supports
    structured JSON via prompted schema hint (Anthropic doesn't have strict
    `json_schema` mode), cleans code fences, and adapts the response shape to
    match the OpenAI return shape so nothing downstream has to change.
- `src/agents/base_agent.py` — extended `generate()` with `model` and
  `max_tokens` kwargs. Agents that don't specify these stay on their default.
- `src/agents/content_strategist.py` — the main generation call in `execute()`
  now passes `model=anthropic.model, temperature=anthropic.temperature,
  max_tokens=anthropic.max_tokens`. Auxiliary sub-calls (evergreen angle,
  voice/ending coherence) are left on the default (GPT-4o-mini) — only the
  heavy creative generation hits Claude.

### Verification

- Provider routing table verified: `gpt-*` → openai, `claude-*` → anthropic,
  `gemini-*` → google, others → openai fallback.
- Config loader sees the new `anthropic:` section.
- Anthropic SDK is installed in the environment; client init gracefully degrades
  when key is missing.

**Not verified here**: live generation quality comparison between 4o-mini and
Sonnet on the same trends. That requires API keys and belongs to a before/after
run the user should do when deploying.

---

## Fix #3 — Validators ask diagnostic questions on three different providers

### Diagnosis

All three validators ran on the same GPT-4o-mini and all asked for holistic
1-10 scoring with generic booleans (`screenshot_worthy`, `would_send_to_friend`,
`approved`). Persona-swapped prompts on the same model produce correlated
judgments, not independent ones — so low-quality posts pass because the
structural checklist is satisfied and three 4o-mini instances agree on it for
the same reasons.

### What changed

- `src/infrastructure/ai/openai_client.py` — added Gemini text support
  (`_generate_with_gemini_text`) via `google.genai`, wrapping the sync
  `generate_content` call in `asyncio.to_thread`. Routes `gemini-*` models.
- `src/agents/validators/sarah_chen.py` — rewrite. Runs on `claude-sonnet-4-6`.
  Four diagnostic questions:
  1. Name the emotion this post is trying to create (one word — or "none" → fails).
  2. Quote the single sentence most likely to be screenshotted (or quote the
     weakest and set found=false).
  3. "Any satirical brand" vs "only Jesse" — if any brand, name one concrete
     change.
  4. Name one detail that could only have come from this specific story.
  Approval requires all four to pass + length in [40,100].
- `src/agents/validators/marcus_williams.py` — rewrite. Runs on `gpt-4o`. Four
  diagnostic questions:
  1. Quote the weakest sentence with a one-clause reason (informational — always
     used in feedback).
  2. List every metaphor; for each, state the property being compared; flag any
     where both sides don't share it (the "glacier of red tape" test).
  3. Where does this read like an LLM wrote it? Quote the specific phrase.
  4. Does the post lean on a template crutch ("Diagnosed:", "Prescription:",
     etc.)? If yes, is it earned? If not, propose a non-template opener.
  Approval requires Q2, Q3, Q4 to pass + length in [40,100].
- `src/agents/validators/jordan_park.py` — rewrite. Runs on `gemini-2.5-pro`.
  Four diagnostic questions:
  1. State the insight in a sentence that isn't a rephrase of the post.
  2. Where is the surprise moment? Quote it.
  3. Describe the specific reader in ≤10 words (role + moment).
  4. Would someone who already knows the topic learn something specific? Name it.
  Approval requires all four to pass + length in [40,100].
- `src/agents/feedback_aggregator.py` — rewrite. Consumes the structured
  diagnostic answers from each validator; builds a revision brief that QUOTES
  the specific failures (broken metaphor text, LLM tell phrase, missing insight)
  rather than saying "make it punchier." Provides `quoted_failures`,
  `proposed_opener`, and per-validator `validator_breakdown` for the reviser.
- Approval aggregation: **no change needed**. The orchestrator already loops
  `while approvals < 2` (see `src/services/orchestrator.py:510`) — which
  matches the 2-of-3 rule exactly.

### Verification

- Each validator's `_parse_validation` correctly derives approval from
  diagnostic answers:
  - Sarah all 4 pass → score 9.0, approved=True
  - Sarah 3/4 pass → score 6.5, approved=False
  - Marcus all core pass → 9.0, approved=True
  - Marcus with broken metaphor → 6.5, approved=False, feedback quotes the
    broken metaphor
  - Jordan all 4 pass → 9.0, approved=True
  - Jordan insight-is-rephrase → 6.5, approved=False, feedback quotes the failure
- All three validator classes correctly hold distinct `self.model` values:
  claude-sonnet-4-6 / gpt-4o / gemini-2.5-pro.
- The `ValidationScore` pydantic validator (`approved = score >= 7.0`) agrees
  with the derived scores — all passes get ≥7, all failures get <7.

**Not verified here**: disagreement between validators on real posts; revision
quality when quoted failures are fed to the reviser.

---

## Fix #4 — Trim system prompt + retrieval-based voice grounding

### Diagnosis

The strategist system prompt was ~400 lines. Under that constraint pressure, a
small model retreats to the statistical mode — which in Jesse's prompt is the
clinical/diagnostic pattern. Even on Sonnet, shorter + retrieval anchors voice
more effectively than restating every rule.

### What changed

- `prompts/jesse_voice_reference.md` — created. Archives the Sentiment Range,
  LinkedIn Physics, Liquid Death Creative Rules 1-6, Dry Comedy Engine examples,
  and "How Jesse reacts to news" long-form. Reference for reviewers, not
  loaded into the prompt.
- `src/agents/content_strategist.py` — trimmed `_build_creative_system_prompt`
  from ~390 lines of prompt body down to **87 lines** (well below the ~150
  target). Kept: identity + double satire (condensed), dry comedy engine (two
  paragraphs), Five Questions (one line each), hard rules, formula traps,
  pointer to `jesse_voice_reference.md`, and a note that retrieved gold-standard
  examples will be injected into the user prompt.
- `src/infrastructure/memory/agent_memory.py`
  - Added `gold_standard_posts` table: id, content, pillar, format, embedding
    (BLOB), notes, curator, source_post_id, added_at. Indexed on pillar.
  - Added helper methods: `add_gold_standard_post`, `count_gold_standard_posts`,
    `search_gold_standard_by_embedding` (cosine similarity in Python — fine for
    small corpora, no numpy dependency), `get_top_engagement_posts_for_curation`.
  - Embeddings stored as `array('f').tobytes()` for compactness (6KB/row for
    text-embedding-3-small's 1536 dims).
- `src/infrastructure/ai/openai_client.py` — added `embed_text()` using
  `text-embedding-3-small` (cheap, sufficient, matches existing OpenAI
  infrastructure). Returns `[]` on failure so retrieval degrades gracefully.
- `src/agents/content_strategist.py`
  - Added `_retrieve_gold_standard_examples()` — embeds `observation + take`
    (or `creative_direction` if no structured angle), queries top-5 similar
    posts filtered by pillar (broadens silently if the pillar has no corpus).
  - Added `_build_gold_examples_block()` — labels the retrieved posts as
    "voice-matching reference — do NOT copy" and injects them into the user
    prompt (not the system prompt). Empty corpus → empty block, no disruption.
  - Wired both into `execute()` between strategy selection and prompt building.
- `scripts/curate_gold_standard.py` — created. CLI that pulls the top-N posts
  from `content_memory` sorted by engagement (reactions + comments + shares),
  presents each for accept/reject, embeds accepted posts, writes them to
  `gold_standard_posts`. Supports `--status`, `--dry-run`, `--limit`. Blocks on
  missing `OPENAI_API_KEY` since embedding is required. Gracefully handles
  "no engagement data yet" — the user seeds via PerformanceIngestionJob first.

### Verification

- 87-line system prompt body confirmed by regex extraction.
- Gold-standard insert + retrieval verified end-to-end with synthetic
  embeddings: ranking is correct, pillar filter applies, empty-pillar query
  silently broadens to all pillars.
- Empty corpus path: `_retrieve_gold_standard_examples` short-circuits before
  embedding; `_build_gold_examples_block([])` returns empty string.
- All modified files parse and import cleanly.

**Not verified here**: that the retrieved examples actually improve voice
consistency across 10 generations. That requires a live run with curated corpus.

---

## Final-verification step (for the user to run)

The task calls for a 20-post generation with human grading on three axes: voice
(specifically Jesse), substance (real take + real details), craft (earned
metaphors + structure + opener). I cannot run that from this environment — it
needs live OpenAI + Anthropic + Google API keys and a running FastAPI server.

**Run order when you deploy:**

1. Make sure `.env` has `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`.
2. `pip install -r requirements.txt` to pick up the anthropic SDK bump.
3. Start the service: `uvicorn api.main:app` (or however you normally run it).
4. Optional but recommended: seed the gold-standard corpus once you have
   engagement data — `python scripts/curate_gold_standard.py`. Until the corpus
   is populated, retrieval is a no-op and the trimmed system prompt + structured
   angle alone are doing the work. That's fine for the first deployment.
5. Run 5 dry generations: `POST /api/automation/generate-content` (no LinkedIn
   post). Inspect the output against Fix #1 verification criteria:
   - Does the post reference the concrete details from the trend?
   - Is the take visible in the post?
   - Is the tension / gap visible?
   - Has the "Diagnosed:" opener stopped dominating?
6. Run the 20-post acceptance grading (voice / substance / craft). Target: 15+
   of 20 pass all three criteria before you turn LinkedIn posting back on.

## What was NOT done (per "Do not" list)

- No new agents added to the pipeline.
- No schema changes beyond `gold_standard_posts` and the `structured_angle`
  field on `TrendingNews` (in-memory only, not persisted).
- GPT-4o-mini stays for classification tasks (news curator, theme classifier,
  position extractor, strategist sub-calls).
- Scheduler, LinkedIn poster, dashboard, and weekly strategic agents were not
  touched.
- No edge-case prompt tuning yet — that should be driven by real output from
  your verification runs, not imagined scenarios.
