# How Jesse's Content System Works

*A simple tour — 5-minute read. No technical background needed.*

---

## The short version

Jesse isn't **one** AI writing posts. Jesse is a **team of 12 specialized AIs** — each with one job — working together like a small newsroom.

A story goes through a researcher → an editor → a writer → three critics → a fact-checker before it ever reaches LinkedIn.

Here's a tour of the team and what happens every time a post gets made.

---

## Meet the team

Think of Jesse's system as a newsroom. Each "staff member" is an AI specialist.

| Role | Their job | Think of them as |
|---|---|---|
| 🔍 **The Scout** | Fetches breaking news from 30+ sources | A 24/7 news wire reader |
| ⚖️ **The Balancer** | Ensures the news mix isn't all tech or all politics | Desk editor organizing the day's assignments |
| 🎯 **The Story Picker** | Chooses which ONE story Jesse should react to | A senior editor picking tomorrow's op-ed |
| 🧠 **The Strategist** | Decides HOW Jesse should write it — voice, angle, joke style | A creative director |
| ✍️ **The Writer** | Actually writes the post — drafts 3, picks the best | A staff writer |
| 📋 **Editor Sarah** | Checks: is this ON-BRAND? | Brand steward |
| 📋 **Editor Marcus** | Checks: is the WRITING good? | Copy chief |
| 📋 **Editor Jordan** | Checks: will this STOP the scroll? | Audience advocate |
| 🔄 **The Reviser** | Rewrites when editors raise concerns | Line editor |
| 📸 **The Art Director** | Creates the image for the post | Graphic designer |
| 📚 **The Librarian** | Remembers everything ever published | Archives + research |
| 📅 **The Planner** | Sets the weekly editorial calendar | Managing editor |
| 🔬 **The Analyst** | Studies what's working over time | Audience analyst |

---

## What happens when the system makes one post

### Step 1 — The Scout brings ideas *(~30 seconds)*
The Scout reads news wires (NYT, NPR, Axios), social media (Reddit, 7 subreddits), and search feeds. It returns about **20 candidate stories** — politics, business, sports, culture, celebrity news, tech.

### Step 2 — The Balancer diversifies the pool *(~1 second)*
Before the Picker sees anything, the Balancer checks: "Are 14 of these 20 stories corporate AI news?" If yes, it rebalances so the Picker sees something like:
- 1 politics story
- 1 celebrity moment
- 1 sports news
- 1 tech announcement
- 1 viral cultural moment
- 1 corporate absurdity
- + 2 more from the remaining buckets

**This is why Jesse's feed doesn't read like Bloomberg Terminal** — the Balancer prevents tech-monoculture before the Picker can pick.

### Step 3 — The Story Picker chooses ONE *(~3 seconds)*
Runs a 5-question checklist:
- Is this US-focused (our audience)?
- Does it have cultural heat (everyone talking about it)?
- Is there a Jesse-shaped angle?
- Can we pull specific named details from it?
- Does the source confirm the facts?

Picks one story, writes the "take" (the angle Jesse will use).

### Step 4 — The Strategist designs the post *(~5 seconds)*
This is the most important step. The Strategist produces a one-page brief called **the blueprint**. It decides:

- **Voice**, one of five:
  - 🩺 Clinical (like a doctor diagnosing culture)
  - 🎯 Contrarian (flip the popular take)
  - 🔮 Prophet (predict specifically, with a time horizon)
  - 🗣️ Confession (Jesse admits something absurd about being an AI)
  - 🔥 Roast (name a target, be sharp, like Wendy's Twitter)

- **Joke technique**, one of four:
  - Pretend to BE a recall notice (not write about one)
  - Talk like a lawyer or insurance adjuster the whole post
  - Use a surprise-third-item list
  - End on something mundane (to shrink the post retroactively)

- **Emotional anchor**, four specific details:
  - WHO in the story is a real human (not "employees" — "a PM at Microsoft")
  - WHERE they are in a private moment (2:47am, kitchen table)
  - WHAT concrete object is in the scene (a phone face-down, a yellow legal pad)
  - WHAT's the gap between a big institutional number and a small personal moment

- **Length and shape** (short, medium, or long; one or several paragraphs)

### Step 5 — The Writer drafts 3 versions, picks the best *(~10 seconds)*
Writer takes the blueprint and writes **3 drafts** at slightly different "creativity settings." A scorer checks each draft for how well it weaves in the Strategist's specific details. The best draft advances.

### Step 6 — Three editors review simultaneously *(~15 seconds)*

All three run at the same time. Each asks their own questions:

- **Sarah** asks 4 brand questions: *is this on Jesse's voice? Does it have a point of view? Is it drifting into generic LinkedIn essay?*
- **Marcus** asks 6 craft questions: *what's the weakest sentence? Any broken metaphors? Any grammar errors? Is the post clipped mid-sentence? Does it land an emotional moment?*
- **Jordan** asks 5 audience questions: *will the first line stop a scroll? Does it hit shareability triggers? Would my friend forward this?*

**The post needs 2 of 3 to approve.** If fewer → goes to revision.

### Step 7 — The Reviser fixes issues *(only if needed, ~10 seconds)*
If editors flagged problems, the Reviser reads all 3 critiques and rewrites the post. Goes back through the same 3 editors. Up to 3 revision rounds.

### Step 8 — Final safety check *(~1 second)*
Before the post can escape, it runs through **25+ automatic filters** for things Jesse must never do:
- No hashtags
- No "In a world where..." openers
- No "Jesse A. Eisenbalm is the balm for..." brand-stamp closers
- No non-US stories (Lenskart in India → blocked)
- No mid-sentence truncations
- No "The AI doesn't feel / The bots don't sleep" AI-admits-limits clichés

**If ANY filter trips, the post is hard-rejected.** It does not reach the queue.

### Step 9 — Publish
If the post cleared every stage:
- The **Art Director** creates the image
- The **Librarian** archives the post and all its metadata
- Post enters the queue for scheduled LinkedIn publishing
- After posting, an auto-CTA comment is added

**Total time: ~45-60 seconds per post.**

---

## How the team members talk to each other

They don't "chat." They pass documents.

Think of it like a newsroom where every story idea is on paper. A member of staff picks up the document, writes their contribution, and places it on the next desk. Nobody guesses what the others are thinking — everything is on the page.

Here's the order of documents, using a real post from our most recent batch as an example:

### 📄 Real example: the RFK Jr. hearing post (scored 9.0, shipped)

#### Document 1 — "Story Candidates" sheet
*From: The Scout → To: The Balancer*

> Today's 20 stories. Example row:
> ```
> HEADLINE: "RFK Jr. faces seventh congressional hearing this month"
> SOURCE: Politico
> URL: politico.com/...
> CATEGORY: politics_hot
> ```

#### Document 2 — "Balanced Slate" sheet
*From: The Balancer → To: The Story Picker*

> Filtered down to 8 stories, spread across 4 different topic buckets.
> RFK Jr. survives the filter. Non-US stories dropped. Tech-heavy stories trimmed to 2 of 8.

#### Document 3 — "Story Pick" sheet
*From: The Story Picker → To: The Strategist*

> ```
> CHOSEN: RFK Jr. 7th hearing this month
> OBSERVATION: Congressional hearings have become spectacle, not governance
> TAKE: The junior staffer waiting outside at 7pm knows this better than anyone
> CONCRETE DETAILS: ["RFK Jr.", "seventh hearing", "junior staffer"]
> TENSION: Spectacle vs. the real cost to people downstream of the theater
> ```

#### Document 4 — "Post Blueprint" (the most important doc)
*From: The Strategist → To: The Writer*

> ```
> VOICE: roast  (target is RFK Jr.)
> COMEDY TECHNIQUE: false_parallel_list
>   → Pivot on "seven" (the number of hearings) as the list-breaking device
>
> EMOTIONAL ANCHOR (all four required):
>   - WHO:   a junior staffer at the hearing
>   - WHERE: 7pm, outside the hearing room
>   - OBJECT: stack of agendas in hand
>   - SCALE: seven hearings / one missed dinner
>
> OPENING TARGET (first 10 words must be a scroll-stopper):
>   "RFK Jr. is back for his seventh congressional hearing this month."
>
> CLOSING TARGET: end on something mundane (anti-climactic diminishment)
>
> LENGTH: medium (55-75 words)
> SHAPE: 4 paragraphs, ski-jump (punch at the end)
> ```

#### Document 5 — "The Post" (3 drafts, one picked)
*From: The Writer → To: The 3 Editors (simultaneously)*

> ```
> RFK Jr. is back for his seventh congressional hearing this month.
> Seven. The number of dwarfs. The number of deadly sins. A number that,
> in any functioning workplace, would trigger an HR review.
>
> The hearings serve more for spectacle than substance. Everyone knows
> this. The junior staffer waiting outside the hearing room at 7pm —
> stack of agendas in hand, missing dinner again — knows this most of all.
>
> By the end, even the coffee machine will need a vacation.
> ```

#### Documents 6, 7, 8 — "Editor Verdicts" (three separate critiques)
*From: Each Editor → To: The Orchestrator*

> **Sarah's verdict sheet:**
> ```
> SCORE: 7.5 / APPROVED
> NOTES: Strong POV on hearing spectacle. On-brand roast. 4/4 passes.
> ```
>
> **Marcus's verdict sheet:**
> ```
> SCORE: 9.0 / APPROVED
> NOTES: Weakest sentence: none found. No broken metaphors.
> No voice drift. "Seven. The number of dwarfs..." lands hard.
> Grammar clean. Emotional contact present: junior staffer detail.
> 3/3 craft passes.
> ```
>
> **Jordan's verdict sheet:**
> ```
> SCORE: 8.5 / APPROVED
> NOTES: Opener "RFK Jr. is back..." stops scroll. STEPPS: 3/6.
> Will generate comments. Shareable. 2/3 audience passes.
> ```

#### Document 9 — "Approval Tally"
*Computed by The Orchestrator*

> ```
> APPROVALS: 3 of 3  ✅
> AVERAGE SCORE: 8.33
> → Cleared. No revision needed.
> → Proceed to safety check.
> ```

#### Document 10 — "Safety Check Report"
*From: Auto-filter → To: The Orchestrator*

> ```
> BANNED PATTERNS CHECKED: 25
> VIOLATIONS FOUND: 0  ✅
> → Proceed to publish.
> ```

#### Document 11 — "Archive Record"
*From: The Orchestrator → To: The Librarian*

> Everything filed permanently for learning: the original story, the pick sheet, the blueprint, the post, all 3 editor verdicts, the engagement data (added later when LinkedIn reports back).

---

### The big point

**Every handoff is a document, not a conversation.** The Strategist doesn't message the Writer — it hands over a filled-in blueprint form. The editors don't confer — each writes a separate verdict sheet.

This is why the system is:

- **Debuggable.** If a bad post ever reaches the queue, we can read every document that led to it and see exactly where it went wrong.
- **Swappable.** We could replace any single agent without the others noticing, as long as the new agent accepts the same input document and produces the same output document.
- **Learnable.** Every document is archived. The Sunday Analyst reads thousands of these documents and learns patterns: *"Roast posts with named politicians average 2× more comments than generic criticism."*
- **Safe.** Because every document is inspectable, there's never a "the AI just did something weird and we don't know why" moment. Every decision is on the page.

---

## Why three editors instead of one?

One editor has one taste and catches one type of issue. Three editors with narrow mandates catch different things:

- **Sarah (brand)** catches: *"This sentence doesn't sound like Jesse"*
- **Marcus (craft)** catches: *"This metaphor doesn't work / this sentence is 28 words long / there's a typo"*
- **Jordan (audience)** catches: *"The opener won't stop anyone's scroll / this isn't shareable"*

A single editor would miss some. Three editors with specific jobs = broader coverage + much more actionable feedback for the Reviser.

---

## The weekly rhythm

### 🌅 Sunday morning *(automatic)*
- **The Analyst** reads last week's engagement data from LinkedIn (reactions, comments, shares, impressions)
- **The Analyst** writes 2–3 new "lessons learned" to the library (e.g., *"Posts with a named person at the center get 2.3× more comments"*)
- **The Planner** reads those lessons and writes Monday-Friday's editorial calendar

### 📆 Monday through Friday
- One post per day runs through the 9-step process above
- Each post arrives around 8-9am PT

### 🌙 Friday evening
- **Portfolio reviewer** evaluates the entire week's posts as a collection. Did Jesse drift? Too many of one theme? Still recognizably Jesse?
- Flags concerns for next week's planning

### 🎯 Daily guardrails (Tuesday through Saturday)
- **Quality Drift supervisor** scans for recycled phrases or patterns accidentally repeating across recent posts
- Adds them to the writer's "don't use" list automatically

---

## What makes this different from "ChatGPT writing LinkedIn posts"

1. **A story has to earn its way in.** 20 candidates → 1 picked. Most don't make it.
2. **Voice is architecturally varied.** The system mathematically won't let 5 posts in a row sound the same. It has hard rules forcing prophet/confession/roast to show up on rotation.
3. **Every post has to pass 3 editors.** Not 1.
4. **25+ automatic filters.** Nothing can slip through the banned-list. New patterns added every time a bad post is caught in review.
5. **The system learns.** Sunday analytics feed back into next week's plan. What worked in week 4 shapes week 5.
6. **Every handoff is logged.** If you ever ask *"why did Jesse pick that story?"* — the system can show you the exact reasoning at each step.

---

## The numbers

| Measure | Per post |
|---|---|
| News sources monitored | 30+ |
| Stories considered | ~20 |
| AI specialists involved | 9 |
| Quality checks | 25 automatic filters + 15 editor questions |
| Cost (API usage) | ~$0.05 |
| Time end-to-end | 45–60 seconds |
| Approval threshold | 2 of 3 editors |

Over the course of a week that's **~300 candidate stories filtered down to 5 published posts.**

---

## Quick Q&A your client might ask

**Q: What if the AI generates something off-brand or offensive?**
A: Three editors + 25 filters + hard-reject gate. Even if one layer fails, the others catch it. And the system keeps learning — every flagged failure becomes a new filter.

**Q: Can the system repeat itself?**
A: Architecturally no. Voice rotation is enforced. Topics are tracked. Openers are tracked. Compositional frames are tracked. If the system tries to write "Somewhere, a [role] at 3am..." too many times, it's automatically blocked.

**Q: How does it stay timely?**
A: The Scout reads 30+ live sources every hour. By the time a story trends on LinkedIn, Jesse has already seen it twice.

**Q: Can we adjust Jesse's voice or priorities?**
A: Yes. Editorial directives go into the Strategist's prompt. Brand rules go into editor checklists. Topic focus is a config change. Everything is tunable.

**Q: What happens if OpenAI or Claude goes down?**
A: Every boundary has graceful degradation. If image generation fails → post ships without image. If stratifier fails → raw pool goes through. If an editor fails → the other two still vote. The system keeps working.

---

*Questions about any layer? All the logic is inspectable and debuggable — every agent logs its decisions.*
