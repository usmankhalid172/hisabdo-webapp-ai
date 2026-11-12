"""Run every edge case and write reports/edge_case_report.{md,json}."""
import json, os, datetime, collections
from edge_cases import run_all

root = os.path.join(os.path.dirname(__file__), "..", "reports")
os.makedirs(root, exist_ok=True)
res = run_all()
passed = sum(r["passed"] for r in res)
cats = collections.OrderedDict()
for r in res:
    c = cats.setdefault(r["category"], [0, 0]); c[1] += 1; c[0] += r["passed"]

L = ["# Automated Edge-Case Test Report", "",
     "**Task:** Automated Citation Verification & Hallucination Guardrail Pipeline  ",
     "**Author:** Muhammad Daniyal  ",
     f"**Generated:** {datetime.datetime.now():%Y-%m-%d %H:%M}  ",
     "**Config:** `config/guardrail_config.json` v1.0.0  ",
     "**Data:** sample HisabDo-style fixture chunks (`tests/edge_cases.py`); the LLM is mocked so results are deterministic.", "",
     "## Summary", "", f"**{passed}/{len(res)} cases passed** "
     f"({sum(1 for r in res if r['level']=='verifier')} verifier-level, "
     f"{sum(1 for r in res if r['level']=='pipeline')} pipeline-level).", "",
     "| Category | Passed | Total |", "|---|---|---|"]
L += [f"| {k} | {v[0]} | {v[1]} |" for k, v in cats.items()]
L += ["", "## Fallback trigger coverage", "",
      "| Query type | Trigger | Expected route | Cases |", "|---|---|---|---|",
      "| Unanswerable | top retrieval score < 0.35, or 0 chunks (LLM skipped) | `unanswerable` | P06, P07 |",
      "| Unanswerable | model returns `INSUFFICIENT_CONTEXT` | `unanswerable` | P08 |",
      "| Unanswerable | model fabricates answer + source | `citation_failure` | P09 |",
      "| Conflicting | cross-source numeric disagreement on similar chunks (LLM skipped) | `conflicting` | P10 |",
      "| Conflicting | model returns `CONFLICT:` | `conflicting` | P11 |",
      "| Conflicting (negative) | same-source revision / agreeing sources must NOT trigger | `answered` | P12, P13 |",
      "| Ambiguous | pronoun-only or <3-token query (LLM skipped) | `ambiguous` | P14, P15 |",
      "| Ambiguous | near-tied top chunks on unrelated topics | `ambiguous` | P16 |",
      "| Ambiguous | model returns `CLARIFY:` | `ambiguous` | P17 |", "",
      "## Detailed results", "",
      "| ID | Level | Category | Description | Expected | Actual | Result |", "|---|---|---|---|---|---|---|"]
for r in res:
    L.append(f"| {r['id']} | {r['level']} | {r['category']} | {r['description']} | {r['expected']} | "
             f"{r['actual']} | {'PASS' if r['passed'] else '**FAIL**'} |")
fails = [r for r in res if not r["passed"]]
L += ["", "## Failures", ""] + ([f"- {r['id']}: {r['description']} -> {r['actual']} ({r['detail']})" for r in fails] or ["None."])
L += ["", "## Known limitations", "",
      "- Verification proves a cited URL/title exists in the retrieved context; it does not prove the claim text is entailed by that chunk. Add an NLI/entailment or quoted-span check as a next step.",
      "- Conflict detection is a numeric heuristic (similar chunks, disjoint numbers). Textual contradictions without numbers rely on the model's `CONFLICT:` sentinel.",
      "- Ambiguity detection is heuristic (length, pronouns, near-tied unrelated chunks); thresholds should be tuned on real HisabDo query logs.",
      "- Results use mocked LLM outputs and fixture chunks, not live model runs."]
open(os.path.join(root, "edge_case_report.md"), "w").write("\n".join(L) + "\n")
json.dump({"passed": passed, "total": len(res), "results": res}, open(os.path.join(root, "edge_case_report.json"), "w"), indent=2)
print(f"{passed}/{len(res)} passed")
for r in fails: print("FAIL", r["id"], r["expected"], "|", r["actual"], "|", r["detail"])
