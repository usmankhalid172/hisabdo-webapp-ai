# Portfolio Query Rewriting Test Log

**Owner:** Muhammad Mohsin
**Run date:** 2026-11-11
**Command:** `python scripts\evaluate_portfolio_query_rewrites.py`

## Scope and method

This diagnostic compares unexpanded and expanded query terms on portfolio-only
facts in the historical FAQ corpus. It uses term-count cosine (“vector”) and a
lexical hybrid score (65% expanded cosine + 35% exact-token coverage). It does
not use the application embedding model or a live index. The current approved
HisabDo source excludes client case-study material and does not attribute a
technology stack; historical matches must not be used as answer evidence.

The four-query set is intentionally small and diagnostic. Its relevance
anchors are keyword checks, not human-reviewed judgments. Position `-` means no
anchored passage appeared in top-2; `1` means a keyword-anchored passage was at
rank 1. No passage text or held case-study results are included here.

## Rewrite cases

| ID | Original query | Added terms | Term-vector result (original → expanded) | Hybrid result (original → expanded) | Decision |
|---|---|---|---|---|---|
| `industry-logistics` | Have you done projects for logistics companies? | transportation, freight, distribution, supply chain | `-` → `-` | `-` → `-` | No evidence retrieved; do not infer or auto-expand into a case-study answer. |
| `industry-healthtech` | Do you have HealthTech case studies? | healthcare, medical, patient, telehealth | `-` → `-` | `-` → `-` | No evidence retrieved; defer until approved content exists. |
| `industry-fintech-saas` | Have you built FinTech or B2B SaaS products? | financial technology, billing, subscription, payments | `-` → `-` | `-` → `-` | No evidence retrieved; defer until approved content exists. |
| `technology-hisabdo` | Which framework and database power HisabDo? | Flutter, Supabase, PostgreSQL | `1` → `1` | `1` → `1` | Historical match only. The current approved source excludes this attribution; suppress as unsupported. |

## Aggregate and threshold sweep

| Ranker | Original hit@2 | Expanded hit@2 | Original precision@2 | Expanded precision@2 |
|---|---:|---:|---:|---:|
| Term-vector cosine | 0.250 | 0.250 | 0.125 | 0.125 |
| Lexical hybrid | 0.250 | 0.250 | 0.125 | 0.125 |

The expanded-query hybrid sweep was unchanged across thresholds:

| Threshold | Hit@2 | Precision@2 |
|---:|---:|---:|
| 0.10 | 0.250 | 0.125 |
| 0.15 | 0.250 | 0.125 |
| 0.20 | 0.250 | 0.125 |
| 0.25 | 0.250 | 0.125 |
| 0.30 | 0.250 | 0.125 |

The single match in each aggregate is the unapproved historical HisabDo
technology fact. It is not a supported true positive. Removing that stale
match leaves **0/4** supported answer hits for both original and expanded
queries. Industry expansion produced no anchored hit.

## Resulting rewrite policy

- Do not add specific technologies, vendors, or client industries to a query
  unless those terms are grounded in an approved source passage.
- General language normalization may be retained, but do not treat increased
  lexical overlap as evidence that an answer is supported.
- Keep no-evidence behavior for these unsupported queries. After approved
  source material is available and indexed, rerun with actual embeddings and
  human-reviewed passage labels before enabling expansions.

See the
[Day 1 retrieval evaluation](./portfolio-day1-retrieval-evaluation-2026-11-11.md)
for the 12-query benchmark and threshold recommendation.
