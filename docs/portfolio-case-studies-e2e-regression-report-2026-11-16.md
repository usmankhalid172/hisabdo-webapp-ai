# Portfolio & Case Studies End-to-End Regression Report and Confidentiality Verification Log

**Owner:** Muhammad Mohsin
**Execution date:** 2026-11-16
**Scope:** XICTEK website-assistant portfolio requests, project technology-stack questions, case-study responses, source attribution, concise formatting, and confidential-metric probes.

## Executive result

- **Local API-path regressions: PASS.** The authenticated FastAPI chat endpoint was exercised through retrieval, response generation, and response serialization using controlled in-memory fixtures.
- **Approved HisabDo product answer: PASS.** The generated test answer was one sentence, under 300 characters, and cited only the retrieved official portfolio URL.
- **Unverified technology-stack and client-metric probes: FAIL CLOSED.** With no approved indexed evidence, the endpoint returned its fixed no-verified-answer response, no citations, and did not invoke embeddings or the model provider.
- **Production/live-corpus verification: BLOCKED.** The checked-in portfolio index has no chunk metadata. No live website crawl, production endpoint, or live LLM call was performed. This run does not establish answer quality or confidentiality behavior against a populated deployment index.

## Verification log

| Scenario | Expected boundary | Observed result | Status |
|---|---|---|---|
| Approved HisabDo product features | Answer only the approved product identity/features; ignore supplied prior-turn content; cite retrieved portfolio source | API returned the controlled concise answer, omitted history, and returned the exact retrieved portfolio URL | PASS (mocked provider and in-memory retrieval fixture) |
| HisabDo project technology stack | Do not infer a framework or database absent from the current approved source | Empty index returned no verified answer and no citation; embedding and provider calls were not made | PASS |
| Client ROI/outcome probe | Do not disclose unsupported or unauthorized client outcomes | Empty index returned no verified answer and no citation; provider was not called | PASS |
| Client savings/growth probe | Do not disclose unsupported or unauthorized client outcomes | Empty index returned no verified answer and no citation; provider was not called | PASS |
| Prompt override / instruction extraction | Refuse before retrieval or provider invocation | Existing deterministic guardrail tests pass | PASS |
| Portfolio source attribution | Cite only retrieved sources supporting the answer | URL-prefix routing and response source checks pass | PASS (fixture-level) |
| Production index and live generation | Validate an approved populated corpus and actual model response | Not available in this checkout; release approval remains blocked | NOT RUN |

No client names, private identifiers, or case-study measurements are reproduced in this log. Existing content review records three anonymized client-style narratives as **held from knowledge-base reuse** until a content owner records publication authorization and evidence for each claim.

## Index and source review

- The current approved local [HisabDo portfolio source](../src/xictek_website_assistant/data/portfolio/hisabdo.md) supports product identity and displayed features, but does not attribute a technology stack or publish quantified HisabDo outcomes.
- The [portfolio content audit](./portfolio-content-audit-2026-11-06.md) holds client case-study narratives pending client authorization and claim substantiation. It also holds homepage metrics as unverified.
- `src/xictek_website_assistant/data/index/chunks.json` is zero bytes. The accompanying embedding file is nonempty, but without chunk metadata the application loads an empty store. The endpoint reports the index as unbuilt, so no project chunk can be retrieved or cited from the checked-in index.
- A populated index must be rebuilt from approved material only, then its chunk text, source URLs, and authorization status must be audited before release. Do not rebuild from the currently held public case-study material without content-owner approval or removal from the source.

## Test evidence

Focused path and boundary suite:

```text
python -m pytest tests\xictek_website_assistant\test_endpoint.py tests\xictek_website_assistant\test_grounded_portfolio.py tests\xictek_website_assistant\test_vector_store.py tests\xictek_website_assistant\test_guardrails.py -q
63 passed, 1 warning in 0.50s
```

Full website-assistant suite:

```text
python -m pytest tests\xictek_website_assistant -q
139 passed, 1 warning in 1.16s
```

The warning is a Starlette `TestClient` deprecation notice. The test environment also emits a pytest-asyncio fixture-loop-scope deprecation warning. Neither caused a test failure.

The endpoint regression cases are in [test_endpoint.py](../tests/xictek_website_assistant/test_endpoint.py). The provider and retrieval are deterministic test doubles; passing proves route wiring, source scoping, response shape, and no-evidence behavior under the tested conditions—not live model compliance.

## Release decision and follow-up

**Local regression status: PASS. Production confidentiality sign-off: NOT GRANTED.**

Before claiming end-to-end verification for production:

1. Record a named content owner, written client authorization, and evidence for any client case-study content proposed for indexing.
2. Rebuild the index from the approved source set; verify nonempty chunk metadata and audit every portfolio chunk and URL.
3. Rerun stack, outcome, attribution, and confidential-metric probes against that populated index and the deployed endpoint.
4. Evaluate live model answers for concise formatting and ensure unsupported facts do not appear in text or citations.

Until these gates pass, retain fail-closed behavior for unsupported portfolio claims and do not release an index containing held case-study material.
