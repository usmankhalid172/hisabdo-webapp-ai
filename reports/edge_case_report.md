# Automated Edge-Case Test Report

**Task:** Automated Citation Verification & Hallucination Guardrail Pipeline  
**Author:** Muhammad Daniyal  
**Generated:** 2026-11-12 15:00  
**Config:** `config/guardrail_config.json` v1.0.0  
**Data:** sample HisabDo-style fixture chunks (`tests/edge_cases.py`); the LLM is mocked so results are deterministic.

## Summary

**34/34 cases passed** (15 verifier-level, 19 pipeline-level).

| Category | Passed | Total |
|---|---|---|
| valid | 2 | 2 |
| hallucination | 9 | 9 |
| normalisation | 2 | 2 |
| robustness | 4 | 4 |
| strictness | 2 | 2 |
| mixed | 1 | 1 |
| baseline | 1 | 1 |
| unanswerable | 4 | 4 |
| conflicting | 4 | 4 |
| ambiguous | 4 | 4 |
| security | 1 | 1 |

## Fallback trigger coverage

| Query type | Trigger | Expected route | Cases |
|---|---|---|---|
| Unanswerable | top retrieval score < 0.35, or 0 chunks (LLM skipped) | `unanswerable` | P06, P07 |
| Unanswerable | model returns `INSUFFICIENT_CONTEXT` | `unanswerable` | P08 |
| Unanswerable | model fabricates answer + source | `citation_failure` | P09 |
| Conflicting | cross-source numeric disagreement on similar chunks (LLM skipped) | `conflicting` | P10 |
| Conflicting | model returns `CONFLICT:` | `conflicting` | P11 |
| Conflicting (negative) | same-source revision / agreeing sources must NOT trigger | `answered` | P12, P13 |
| Ambiguous | pronoun-only or <3-token query (LLM skipped) | `ambiguous` | P14, P15 |
| Ambiguous | near-tied top chunks on unrelated topics | `ambiguous` | P16 |
| Ambiguous | model returns `CLARIFY:` | `ambiguous` | P17 |

## Detailed results

| ID | Level | Category | Description | Expected | Actual | Result |
|---|---|---|---|---|---|---|
| V01 | verifier | valid | Markdown link with exact URL + title | ok=True, unverified=0 | ok=True, unverified=0, total=1 | PASS |
| V02 | verifier | hallucination | Fabricated URL on a real domain | ok=False, unverified=1 | ok=False, unverified=1, total=1 | PASS |
| V03 | verifier | hallucination | Fabricated title in [Source:] tag | ok=False, unverified=1 | ok=False, unverified=1, total=1 | PASS |
| V04 | verifier | normalisation | http, www, utm params, trailing slash, fragment still match | ok=True, unverified=0 | ok=True, unverified=0, total=1 | PASS |
| V05 | verifier | hallucination | Numeric reference outside retrieved range | ok=False, unverified=1 | ok=False, unverified=1, total=1 | PASS |
| V06 | verifier | valid | Numeric refs and ranges inside range | ok=True, unverified=0 | ok=True, unverified=0, total=3 | PASS |
| V07 | verifier | normalisation | Title with different case and curly quotes | ok=True, unverified=0 | ok=True, unverified=0, total=1 | PASS |
| V08 | verifier | hallucination | Altered path (typo-squat of real URL) | ok=False, unverified=1 | ok=False, unverified=1, total=1 | PASS |
| V09 | verifier | hallucination | Look-alike domain (suffix attack) | ok=False, unverified=1 | ok=False, unverified=1, total=1 | PASS |
| V10 | verifier | robustness | Fake URL inside a code fence is ignored | ok=True, unverified=0 | ok=True, unverified=0, total=1 | PASS |
| V11 | verifier | strictness | Bare domain rejected when allow_domain_only_match=false | ok=False, unverified=1 | ok=False, unverified=1, total=1 | PASS |
| V12 | verifier | strictness | Bare domain accepted when allow_domain_only_match=true | ok=True, unverified=0 | ok=True, unverified=0, total=1 | PASS |
| V13 | verifier | mixed | One valid and one fabricated citation: exactly one flagged | ok=False, unverified=1 | ok=False, unverified=1, total=2 | PASS |
| V14 | verifier | robustness | Minor title typo within 0.90 similarity is tolerated | ok=True, unverified=0 | ok=True, unverified=0, total=1 | PASS |
| V15 | verifier | robustness | Answer with no citations yields zero citations (policy handled by pipeline) | ok=True, unverified=0 | ok=True, unverified=0, total=0 | PASS |
| P01 | pipeline | baseline | Grounded, fully cited answer passes | route=answered, llm_called=True, regens=0 | route=answered, llm_called=True, regens=0, llm_calls=1 | PASS |
| P02 | pipeline | hallucination | Fake URL first, corrected on regeneration | route=answered, llm_called=True, regens=1 | route=answered, llm_called=True, regens=1, llm_calls=2 | PASS |
| P03 | pipeline | hallucination | Persistent fake URL falls back after max regenerations | route=citation_failure, llm_called=True, regens=1 | route=citation_failure, llm_called=True, regens=1, llm_calls=2 | PASS |
| P04 | pipeline | hallucination | Uncited answer is rejected (citations required) | route=citation_failure, llm_called=True, regens=1 | route=citation_failure, llm_called=True, regens=1, llm_calls=2 | PASS |
| P05 | pipeline | hallucination | Numeric index out of range | route=citation_failure, llm_called=True, regens=1 | route=citation_failure, llm_called=True, regens=1, llm_calls=2 | PASS |
| P06 | pipeline | unanswerable | Retrieval below score threshold: LLM not called | route=unanswerable, llm_called=False, regens=0 | route=unanswerable, llm_called=False, regens=0, llm_calls=0 | PASS |
| P07 | pipeline | unanswerable | Zero chunks retrieved: LLM not called | route=unanswerable, llm_called=False, regens=0 | route=unanswerable, llm_called=False, regens=0, llm_calls=0 | PASS |
| P08 | pipeline | unanswerable | Model obeys prompt and returns INSUFFICIENT_CONTEXT | route=unanswerable, llm_called=True, regens=0 | route=unanswerable, llm_called=True, regens=0, llm_calls=1 | PASS |
| P09 | pipeline | unanswerable | Model invents answer with fake source: caught post-generation | route=citation_failure, llm_called=True, regens=1 | route=citation_failure, llm_called=True, regens=1, llm_calls=2 | PASS |
| P10 | pipeline | conflicting | Two sources give different Pro prices: pre-generation conflict | route=conflicting, llm_called=False, regens=0 | route=conflicting, llm_called=False, regens=0, llm_calls=0 | PASS |
| P11 | pipeline | conflicting | Model flags conflict via CONFLICT: sentinel | route=conflicting, llm_called=True, regens=0 | route=conflicting, llm_called=True, regens=0, llm_calls=1 | PASS |
| P12 | pipeline | conflicting | Same-source revision is not a cross-source conflict | route=answered, llm_called=True, regens=0 | route=answered, llm_called=True, regens=0, llm_calls=1 | PASS |
| P13 | pipeline | conflicting | Two sources agree: no false conflict | route=answered, llm_called=True, regens=0 | route=answered, llm_called=True, regens=0, llm_calls=1 | PASS |
| P14 | pipeline | ambiguous | Pronoun-only query | route=ambiguous, llm_called=False, regens=0 | route=ambiguous, llm_called=False, regens=0, llm_calls=0 | PASS |
| P15 | pipeline | ambiguous | Single-word query | route=ambiguous, llm_called=False, regens=0 | route=ambiguous, llm_called=False, regens=0, llm_calls=0 | PASS |
| P16 | pipeline | ambiguous | Two near-tied chunks on different topics | route=ambiguous, llm_called=False, regens=0 | route=ambiguous, llm_called=False, regens=0, llm_calls=0 | PASS |
| P17 | pipeline | ambiguous | Model asks for clarification via CLARIFY: sentinel | route=ambiguous, llm_called=True, regens=0 | route=ambiguous, llm_called=True, regens=0, llm_calls=1 | PASS |
| P18 | pipeline | robustness | Empty generation | route=empty_generation, llm_called=True, regens=0 | route=empty_generation, llm_called=True, regens=0, llm_calls=1 | PASS |
| P19 | pipeline | security | Prompt injection in chunk makes model cite attacker URL | route=citation_failure, llm_called=True, regens=1 | route=citation_failure, llm_called=True, regens=1, llm_calls=2 | PASS |

## Failures

None.

## Known limitations

- Verification proves a cited URL/title exists in the retrieved context; it does not prove the claim text is entailed by that chunk. Add an NLI/entailment or quoted-span check as a next step.
- Conflict detection is a numeric heuristic (similar chunks, disjoint numbers). Textual contradictions without numbers rely on the model's `CONFLICT:` sentinel.
- Ambiguity detection is heuristic (length, pronouns, near-tied unrelated chunks); thresholds should be tuned on real HisabDo query logs.
- Results use mocked LLM outputs and fixture chunks, not live model runs.
