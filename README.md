# The Unofficial Guide

Sarah Al-Said - City_guides Corpus

> **This file is your submission.** Fill it in as you go — most sections get
> written during the milestone that produces them, not at the end.
>
> How the starter works, and every command you'll need, is in `RUNNING.md`.
> Leave that file alone.
>
> **Paste everything as text.** No screenshots, no video. A typed table gets
> full credit; a picture of the same table gets none.
>
> Delete these instruction blocks as you replace them. The `<!-- -->` comments
> are notes to you and don't show up when the page renders — you can leave them
> or remove them.

---

# Unit 1

## What This Does

This system is a retrieval-augmented knowledge base over `city_guides`, a corpus of 14 travel guides. The corpus covers individual towns and villages alongside 
regional guides on transport, walking, dining, seasonality, and accessibility.

Given a specific query the system:

1. **Retrieves** the most relevant guide section from the corpus.
2. **Generates** an answer grounded in the retrieved content.
3. **Cites** the source document the answer was drawn from.

The result is a traceable answer for every query, with each response tied back
to a specific guide in `city_guides`.

## Chunking Strategy

**Chunk size:** Variable — one chunk per `##` markdown section (not a fixed
character count).
**Overlap:** None between sections; each chunk is prefixed with its
document's title so it reads standalone.

My documents (`city_guides`) are hand-structured guides, each broken into
labeled sections — Getting there, Getting around, Eat and drink, What to see,
Where to stay, When to go, Practical notes. The starter's fixed 800-character
chunker cut straight through these boundaries: it produced 51 chunks
averaging 650 characters, with a longest of exactly 800 (meaning real content
was being truncated mid-section) and a shortest of 24 (a leftover fragment
from an uneven division).

I replaced it with a chunker that splits on `##` headers instead, since each
section is already a complete, self-contained thought written by the
document's author. This produced 94 chunks averaging roughly 300 characters,
with no more arbitrary truncation.

I changed my mind once partway through: my first version duplicated each
document's title inside its own intro chunk (the title line was being
captured both as the chunk's title prefix and as part of the section body).
I fixed the section-splitting logic to skip the title line specifically.

One real weak spot I found and kept rather than hid: the very first section
of `guide_accessibility.md` (before its first `##` header) is a short
meta-comment about the guide's tone — "an honest assessment rather than a
promotional one" — and doesn't answer any concrete question on its own. Every
other sampled chunk stands alone; this one is the exception, and it's a
structural side effect of treating a document's opening paragraph as its own
chunk even when that paragraph carries little content.

## Sample Chunks

**Chunk 1** — source: `guide_accessibility.md#0` — produced by: `chunker.py::split_documents`

```
Getting around the region with limited mobility

An honest assessment rather than a promotional one. Some of these places are
difficult and it is better to know in advance.
```

**Chunk 2** — source: `guide_corry_vale.md#5` — produced by: `chunker.py::split_documents`

```
Corry Vale

## Where to stay

Perhaps thirty beds in the entire valley, spread across two pubs and a handful of farmhouse rooms. In summer these are booked months ahead. Camping is permitted on two marked fields and nowhere else.
```

**Chunk 3** — source: `guide_givens_mill.md#2` — produced by: `chunker.py::split_documents`

```
Givens Mill

## Getting around

Everything is on one street along the river. The mill is at one end and the church at the other, eight minutes apart. The riverside path continues in both directions for as far as you want to walk.
```

**Chunk 4** — source: `guide_kestrelford.md#4` — produced by: `chunker.py::split_documents`

```
Kestrelford

## What to see

The market square on a Saturday morning is the main event and has run continuously since the 1400s. The parish church has a 13th-century tower you can climb for £2. The old trackbed walk runs six miles to the next village along an easy gradient and is the best half-day here.
```

**Chunk 5** — source: `guide_pellew_sands.md#6` — produced by: `chunker.py::split_documents`

```
Pellew Sands

## When to go

June and September for the beach without the crowds. July and August are busy and the town is at its most itself, for better and worse. Winter is bleak, largely closed, and has a following among people who like that sort of thing.
```

## Sample Answer

**Question:**
What time do most kitchens in Marchwood stop serving food?

**Answer:**

In Marchwood, kitchens serve until 10:30 pm, and until midnight on Fridays and Saturdays (guide_marchwood.md).

Sources retrieved: guide_eating.md, guide_kestrelford.md, guide_marchwood.md

**My relevance cutoff:**

0.6 (the starter's default). I tested it against my 5 in-scope questions and 5 out-of-scope questions and found a clean gap — in-scope distances ranged 0.266–0.382, out-of-scope ranged 0.779–0.926, with nothing in between. 0.6 sits well inside that gap, so I kept the default rather than changing it.


| Question | In corpus? | Best distance |
|---|---|---|
| How often do buses run to Brightwater on Sundays? | Yes | 0.325 |
| What time do most kitchens in Marchwood stop serving food? | Yes | 0.268 |
| Why should visitors check tide tables before going to Elder Ness? | Yes | 0.382 |
| How long does the Corry Vale circuit walk take, and how much climbing does it involve? | Yes | 0.296 |
| When does the Givens Mill watermill close for the season? | Yes | 0.266 |
| What is the capital of Mongolia? | No | 0.779 |
| How do I change the oil in a diesel engine? | No | 0.882 |
| Who won the 1994 World Cup? | No | 0.926 |
| What is the recommended dosage of ibuprofen for a headache? | No | 0.818 |
| How do I write a for loop in Rust? | No | 0.814 |

## How I Used AI

### 1. Chunking Strategy

**Problem:** The starter's fixed 800-character chunker was splitting through the
labeled sections in my `city_guides` documents.

**Approach:** I worked with Claude to redesign the chunker to split on `##`
markdown headers, since each section (e.g., *Getting there*, *Eat and drink*)
is already a self-contained unit of meaning.

**Validation:** The first implementation duplicated each document's title inside
its intro chunk, because the title line was captured both as a prefix and as
part of the section body. I caught this by **inspecting the printed chunks
directly** rather than assuming the code was correct. Claude then fixed the
section-body loop to skip the title line.

**Outcome:** Chunks now align one-to-one with guide sections, with no duplicated
content.

### 2. Grounding Instruction Verification

**Problem:** I needed to confirm the starter's default grounding instruction was
strict enough for my corpus before relying on it.

**Approach:** At Claude's suggestion, I designed a targeted test instead of
assuming the instruction worked. I ran `--show-prompt` on a query where two
retrieved chunks could plausibly conflict:

- `guide_eating.md`: kitchens "across the region" close by 9pm
- `guide_marchwood.md`: Marchwood is exempt, with kitchens open until 10:30pm

**Validation:** The model **correctly prioritized the more specific chunk** and
cited the right source document.

**Outcome:** I kept the default grounding instruction, backed by evidence rather
than assumption. This conflict case is one I would not have thought to test on
my own.


---

# Unit 2

<!-- These sections get ADDED to what's already above. Don't delete or rewrite
     unit 1 — the point is that someone can see what you said before you knew
     how it went. -->

## Run Log — Before

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunks contain the answer | 4 of 5 | 4/5 | 4/5 | 4/5 | |
| 2. Every answer names a source | 5 of 5 | 5/5 | 5/5 | 5/5 | |
| 3. Gate stops out-of-corpus questions | 4 of 5 | 5/5 | 5/5 | 5/5 | |
| 4. Sampled chunks stand alone | 4 of 5 | 5/5 | 5/5 | 5/5 | |
| 5. Town question cites that town's own guide | 4 of 5 | 4/5 | 4/5 | 4/5 | |

### Real output — Run 1

Source files: `results/run_2026-09-23_1949_before.md` (written by `run_eval.py::main`) and
`results/scores_before_2026-09-23_1949.jsonl` (written by `scorer.py::judge`).

**Criterion 1 — Retrieved chunks contain the answer** (retrieval by `store.py::search`, called from `run_eval.py::run_once`)

Miss — *How often do buses run to Brightwater on Sundays?* The answer is in `guide_brightwater.md#2`
(*Getting around*: "The local bus runs two routes on a 30-minute headway until 7pm and stops entirely on Sundays.").
That chunk was not retrieved. The five chunks that came back:

```
guide_regional_transport.md#1   0.3252
guide_kestrelford.md#1          0.3568
guide_brightwater.md#1          0.3773   (Getting there — trains, not buses)
guide_regional_transport.md#0   0.3878
guide_givens_mill.md#1          0.3960
```

Hit — *What time do most kitchens in Marchwood stop serving food?* `guide_marchwood.md#3` came back at rank 2:

```
guide_eating.md#1       0.2681
guide_marchwood.md#3    0.2796   ← contains "kitchens serve until 10:30pm"
guide_eating.md#2       0.3802
guide_kestrelford.md#3  0.4431
guide_marchwood.md#6    0.4832
```

**Criterion 2 — Every answer names a source** (`generate.py::answer_from_chunks`)

*What time do most kitchens in Marchwood stop serving food?* — run 1
- Best distance: 0.2681 (passed the gate)
- Sources retrieved: guide_eating.md, guide_kestrelford.md, guide_marchwood.md

```
Kitchens in Marchwood serve until 10:30pm, and until midnight on Fridays and Saturdays. 

Source: `guide_marchwood.md`
```

*When does the Givens Mill watermill close for the season?* — run 1

```
The mill is closed entirely in winter (running only March to November). 

Source: guide_givens_mill.md
```

**Criterion 3 — Gate stops out-of-corpus questions** (`run_eval.py::check_out_of_scope`, using `gate.py::check`, cutoff 0.6)

Refused 5 of 5.

| Out-of-scope question | Best distance | Gate |
|---|---|---|
| What is the capital of Mongolia? | 0.808 | refused |
| How do I change the oil in a diesel engine? | 0.882 | refused |
| Who won the 1994 World Cup? | 0.982 | refused |
| What is the recommended dosage of ibuprofen for a headache? | 0.818 | refused |
| How do I write a for loop in Rust? | 0.814 | refused |

**Criterion 4 — Sampled chunks stand alone** (`chunker.py::split_documents`, sample 1 = `random.Random(1).sample(chunks, 5)`)

```
--- guide_corry_vale.md#4
Corry Vale

## What to see

The valley itself is the attraction. The footpath network is dense and well marked, and a circuit taking in three of the four villages is about nine miles with 500 metres of ascent. The chapel in the second village is 12th century and always unlocked.

--- guide_pellew_sands.md#6
Pellew Sands

## When to go

June and September for the beach without the crowds. July and August are busy and the town is at its most itself, for better and worse. Winter is bleak, largely closed, and has a following among people who like that sort of thing.

--- guide_brightwater.md#3
Brightwater

## Eat and drink

The riverside strip has six or seven places aimed squarely at visitors and priced accordingly. Two streets back, on Corry Lane, the same food costs about a third less. The Tuesday market sets up in the square from 7am and is finished by 1pm. Most kitchens in town stop serving at 9pm, earlier than visitors expect, and on Sundays many close entirely.

--- guide_elder_ness.md#6
Elder Ness

## When to go

April to May and September to October for birds, which is what most visitors come for. Midsummer is pleasant and quiet. Winter is severe, the road floods more often, and the pub reduces to weekends only.

--- guide_corry_vale.md#2
Corry Vale

## Getting around

Nothing within the valley is walkable from anything else — the villages are two to four miles apart. There is one taxi, based in the largest village, and it must be booked a day ahead. Most visitors drive between villages and walk the footpaths in between.
```

**Criterion 5 — Town question cites that town's own guide** (`generate.py::answer_from_chunks`)

Miss — *How often do buses run to Brightwater on Sundays?* — run 1. Cites the regional guide and **Kestrelford's** guide, not `guide_brightwater.md`:
- Best distance: 0.3252 (passed the gate)
- Sources retrieved: guide_brightwater.md, guide_givens_mill.md, guide_kestrelford.md, guide_regional_transport.md

```
Based on the provided documents, Sunday bus service is minimal to non-existent outside of the Brightwater town routes (*guide_regional_transport.md*). Additionally, buses from Brightwater to Kestrelford do not run at all on Sundays (*guide_kestrelford.md*).
```

Hit — *Why should visitors check tide tables before going to Elder Ness?* — run 1. Cites its own guide:

```
Visitors should check the tide tables because the single road into Elder Ness floods at the highest spring tides roughly six times a year for about two hours either side of high water (guide_elder_ness.md).
```

## Verdicts

<!-- MET or MISSED for each of the five, against the target you wrote last
     unit — not a new one. Plus a sentence on how you decided. That sentence
     matters most where it was close.

     If your target said 4 of 5 and your runs came out 4, 3, 4, that's a MISS.
     The target has to hold, not show up occasionally.

     Milestone 2. -->

| # | Criterion | Verdict | How I decided |
|---|---|---|---|
| 1 |  |  |  |
| 2 |  |  |  |
| 3 |  |  |  |
| 4 |  |  |  |
| 5 |  |  |  |

## Diagnoses

<!-- For each miss: which stage caused it, and how. The stage alone isn't
     enough — you need the mechanism.

     Not a diagnosis: "Question 3 didn't work."
     A diagnosis:     "Question 3 asks about laundry costs. The answer is in
                       one sentence that got split across two chunks, so
                       neither chunk on its own contains it."

     The five stages: loading → chunking → embedding → retrieval → generation.

     Look for a pattern. If three misses all ask about numbers, that's one
     problem, not three.

     Missed nothing? Say so, then say honestly whether your targets were set
     low, and which one you'd tighten and to what.

     Milestone 3. -->

## The Improvement

**What I changed:**

**Why I picked it:**

<!-- Connect it to a specific diagnosis above in one sentence. If you can't,
     you picked a fix because it sounded impressive. -->

### Run Log — After

<!-- Same format, same five criteria, three runs each.
     `python run_eval.py --label after` -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 |  |  |  |  |
| 2. Every answer names a source | 5 of 5 |  |  |  |  |
| 3. Gate stops out-of-corpus questions | 4 of 5 |  |  |  |  |
| 4. | | | | | |
| 5. | | | | | |

**Did it help?**

<!-- Say plainly whether it did, and how you know. If it made things worse,
     say that — a change that backfired, honestly reported, earns full credit
     and is more interesting than one that worked. What matters is that you can
     tell.

     Milestone 4. -->

## What's Still Broken

<!-- For each criterion still missed after your fix: what you'd do about it,
     and why you stopped where you did.

     "I ran out of time" is fine if it's true. Pretending nothing is left is
     not.

     Milestone 5. -->

## What I'd Do Differently

<!-- Knowing what you know now — which of your five criteria would you write
     differently, and why?

     Milestone 5. -->