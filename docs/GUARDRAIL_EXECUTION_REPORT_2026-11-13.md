# Guardrail Execution Report — All Domains

**Date:** 13 November 2026  
**Scope:** Prompt injection, off-topic harmful requests, PII/confidential metric probes, and multi-turn context retention

## What is covered

The suite exercises seven public content domains: About Us, Core Services, Portfolio & Case Studies, Careers, HisabDo Product, Blog & News, and Contact & Locations. Each domain has direct injection/extraction coverage, history-injection coverage, and a two-turn context-retention case. Additional cases cover explicit harmful off-topic requests, employee/applicant contact data, Portfolio confidential revenue/ROI probes, and benign business questions.

## Enforcement layers

1. Message length guard rejects requests above the configured limit.
2. Existing deterministic checks reject instruction override, prompt extraction, secret/token, and private company data probes before retrieval or LLM invocation.
3. Added high-confidence checks reject explicit malware, credential theft, doxxing, and weapon-building requests before retrieval or LLM invocation.
4. Supplied conversation history is scanned turn-by-turn, including assistant-labeled turns, before retrieval or LLM invocation.
5. The system prompt provides the fallback for general off-topic requests and reinforces source grounding. It is not treated as a deterministic security boundary.

## Run record

Run the focused suite with:

```powershell
python scripts/run_adversarial_multiturn_suite.py
```

The runner writes a JUnit XML report to `outputs/adversarial_multiturn/junit.xml`.

**Execution status:** Final focused run: **102 passed, 0 failed; final failure rate 0%**. The first run found two failures (89 passed, 2 failed; 2.2% failure rate): a missed PII phrasing and over-broad HisabDo-to-Portfolio query routing. Both were corrected, and the final run passed. Final suite composition: 51 new adversarial/multi-turn instances, 27 existing deterministic guardrail cases, 19 Careers grounding cases, and 5 Portfolio grounding cases. The runner excludes the root API `conftest.py` because this focused suite does not exercise API middleware; `slowapi` is therefore not required for this run. `pydantic-settings` was installed only into an isolated temporary dependency folder because it was absent from the active Python environment; no repository dependency file or project virtual environment was changed.

## Acceptance criteria

- Every adversarial case returns its expected refusal/fallback.
- Rejected message and history probes make zero retrieval and provider calls.
- All seven domain conversations retain the same conversation ID and pass the prior turn history to the provider on turn two.
- Benign domain questions and defensive security questions are not falsely blocked.
- No claims of live-provider or production deployment validation are made based on these mocked tests.

JUnit evidence: `outputs/adversarial_multiturn/junit.xml` (102 tests, 0 failures, 0 errors, 0 skipped; 9.39 seconds).

## Known limitations

- Deterministic abuse patterns are intentionally narrow and English-centric; they are not a complete classifier.
- Multi-turn history is supplied by the caller. These tests verify forwarded history, not server-side persistence, ownership, or tamper-proof storage.
- The Portfolio confidential-metric case proves the explicit confidentiality probe is stopped before generation. It does not prove an LLM would never invent a metric for a differently worded, non-confidential request; that remains covered by grounding policy and needs live-model evaluation.
