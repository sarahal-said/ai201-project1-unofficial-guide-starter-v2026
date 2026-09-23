"""
scorer.py — decides whether an answer was right.

run_eval.py imports this module and calls
    judge(question, expects, answer, results) -> bool
once per question per run. Don't rename judge or change its arguments, or
run_eval.py runs UNSCORED and the Run columns come out blank.

judge() answers ONE question: did the answer contain the `expects` phrase I
wrote in questions.py in unit 1? That's the pass/fail column in results/.

My five criteria measure different things, so on every call judge() also
records a few more checks to a sidecar file (results/scores_<label>_<time>.jsonl).
run_log.py turns that file into the one-row-per-criterion table the README
wants:

  criterion 1  retrieval_hit     a retrieved chunk contains the answer's source sentence
  criterion 2  names_source      the answer names at least one corpus file
  criterion 3  (gate)            not scored here — run_eval.py::check_out_of_scope
  criterion 4  (chunks)          not scored here — chunks don't depend on a run; see run_log.py
  criterion 5  own_town_cited    a town-named question's answer cites that town's own guide

Known limits of a substring test:
  - False FAIL: the answer is right but worded differently from `expects`.
  - False PASS: `expects` is there, and so is an invented extra sentence.
    It catches a missing fact, never an added one. Read the answers too.
"""

import datetime as dt
import json
import re
import sys
from collections import defaultdict

import config

# ─── Where each answer actually lives in the corpus ──────────────────────────
# Criterion 1 is about RETRIEVAL: did a chunk containing the answer come back?
# Checking chunks for `expects` doesn't measure that — `expects` is how I
# expected the ANSWER to be worded, and it isn't always the corpus's wording
# ("does not run" appears only in a sentence about Kestrelford, not
# Brightwater). So for retrieval I check for the sentence the answer comes
# from, copied verbatim from the document. `expects` in questions.py is unchanged.
EVIDENCE = {
    "How often do buses run to Brightwater on Sundays?":
        "stops entirely on sundays",                     # guide_brightwater.md
    "What time do most kitchens in Marchwood stop serving food?":
        "kitchens serve until 10:30pm",                  # guide_marchwood.md
    "Why should visitors check tide tables before going to Elder Ness?":
        "floods at the highest spring tides",            # guide_elder_ness.md, guide_walking.md
    "How long does the Corry Vale circuit walk take, and how much climbing does it involve?":
        "500 metres of ascent",                          # guide_corry_vale.md, guide_walking.md
    "When does the Givens Mill watermill close for the season?":
        "closed entirely in winter",                     # guide_givens_mill.md
}

# Town guides, e.g. guide_elder_ness.md -> "elder ness". Built from the corpus
# folder so it's never out of date.
TOWN_FILES = {
    p.stem.removeprefix("guide_").replace("_", " "): p.name
    for p in config.corpus_path().glob("guide_*.md")
}
TOPIC_GUIDES = {"accessibility", "eating", "regional transport", "seasons", "walking"}
for _topic in TOPIC_GUIDES:
    TOWN_FILES.pop(_topic, None)

FILENAME = re.compile(r"\b([a-z0-9_]+)\.(?:md|txt)\b", re.IGNORECASE)
REFUSAL_MARKERS = ("don't have enough information", "do not have enough information")


def _norm(text):
    """Lowercase, straighten quotes, collapse whitespace."""
    text = str(text or "").lower().replace("’", "'")
    return " ".join(text.split())


def _town_in(question):
    q = _norm(question)
    for town, filename in TOWN_FILES.items():
        if town in q:
            return town, filename
    return None, None


def _label():
    """The --label run_eval.py was started with, so the sidecar file matches."""
    argv = sys.argv[1:]
    for i, arg in enumerate(argv):
        if arg == "--label" and i + 1 < len(argv):
            return argv[i + 1]
        if arg.startswith("--label="):
            return arg.split("=", 1)[1]
    return "unlabelled"


_STAMP = dt.datetime.now().strftime("%Y-%m-%d_%H%M")
_run_counter = defaultdict(int)
SIDECAR = config.RESULTS_DIR / f"scores_{_label()}_{_STAMP}.jsonl"


def retrieval_hit(evidence, results):
    """Did we RETRIEVE the right information?"""
    return any(_norm(evidence) in _norm(r.text) for r in results)


def judge(question, expects, answer, results):
    """Did the answer contain the phrase I said a correct answer would contain?"""
    _run_counter[question] += 1
    answer_n = _norm(answer)

    passed = bool(expects) and _norm(expects) in answer_n

    evidence = EVIDENCE.get(question, expects)
    hit = retrieval_hit(evidence, results)
    hit_rank = next(
        (i + 1 for i, r in enumerate(results) if _norm(evidence) in _norm(r.text)), None
    )

    corpus_files = {p.name.lower() for p in config.corpus_path().iterdir()}
    named = sorted({m.group(0).lower() for m in FILENAME.finditer(answer or "")}
                   & corpus_files)

    town, own_file = _town_in(question)
    other_towns = [f for f in named if f in TOWN_FILES.values() and f != own_file]

    refused = any(m in answer_n for m in REFUSAL_MARKERS)

    # slide 27: hit but no pass = generation problem; neither = retrieval problem
    stage = "OK" if passed else ("generation?" if hit else "retrieval?")
    print(f"    judge: {'PASS' if passed else 'FAIL'} | retrieval_hit={hit} "
          f"(rank {hit_rank}) | names={named or 'none'} | {stage}")

    record = {
        "question": question,
        "run": _run_counter[question],
        "expects": expects,
        "judge_pass": passed,
        "evidence": evidence,
        "retrieval_hit": hit,
        "hit_rank": hit_rank,
        "expects_in_chunks": bool(expects) and any(_norm(expects) in _norm(r.text) for r in results),
        "names_source": bool(named),
        "sources_named": named,
        "town": town,
        "own_town_file": own_file,
        "own_town_cited": (own_file in named) if own_file else None,
        "other_town_cited": other_towns,
        "refused": refused,
        "retrieved": [{"label": r.label, "distance": round(r.distance, 4)} for r in results],
        "answer": answer,
    }
    config.RESULTS_DIR.mkdir(exist_ok=True)
    with SIDECAR.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

    return passed