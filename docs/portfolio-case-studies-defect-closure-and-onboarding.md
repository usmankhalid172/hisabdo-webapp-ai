# Portfolio & Case Studies — Defect Closure, Frozen Formatting, and Onboarding

**Owner:** Muhammad Mohsin

**Status date:** 2026-11-17
**Scope:** XICTEK Systems portfolio and case-study content used by the website assistant

## 1. Defect closure log

| Defect / edge case | Closure evidence | Status |
|---|---|---|
| Portfolio URL lookalikes or unsafe URLs could pass a raw prefix check | URL routing validates HTTPS, host, port, normalized path boundary, and rejects credentials, traversal, malformed URLs, foreign hosts, and lookalike paths. Covered by the vector-store boundary tests and the [security boundary log](./portfolio-security-boundary-test-log.md). | **Closed in code and tests** |
| Client-supplied conversation history could introduce unsupported facts or instructions | Portfolio generation omits supplied history and uses the current question plus retrieved portfolio context. Covered by the grounded-answer and endpoint tests. | **Closed in tested local path** |
| Missing evidence could lead to invented client outcomes, stack details, or citations | With no retrieved evidence, endpoint tests verify a no-verified-answer response, an empty source list, and no embedding/provider call. | **Closed for the tested empty-index path** |
| Attribution could cite a source unrelated to retrieved evidence | Portfolio retrieval is scoped to the portfolio URL; tests verify the cited URL is the retrieved URL. Sources are returned in the API `sources` array. | **Closed in fixtures; populated-index verification remains open** |
| Portfolio responses could become too long or mix unrelated projects | Portfolio uses `top_k=2`; the endpoint regression checks a response of at most 300 characters and no more than one sentence-ending period. | **Closed for the tested response; see frozen template below** |
| Publicly visible client-style stories or unsupported metrics could be mistaken for approved claims | The content audit holds the three anonymized client-style narratives and the homepage metrics pending written publication authorization and evidence. The approved local source is limited to HisabDo identity/features. | **Held; do not ingest or present as approved** |
| Confidentiality on an approved, populated production index | The checked-in `chunks.json` is empty, and no live crawl or production endpoint evaluation was performed. | **Open release gate; production sign-off not granted** |
| Prompt-override and extraction attempts | Existing deterministic guardrails reject covered patterns before retrieval/provider calls. The guardrail is heuristic and does not establish resistance to all paraphrases or languages. | **Covered cases closed; residual limitation remains** |

### Closure decision

No client case-study material or unverified outcome is newly approved by this document. Local automated checks establish the tested route, source scoping, fail-closed behavior, and response shape only. They do not prove that a live crawl or a rebuilt index excludes held content. The production confidentiality gate remains **BLOCKED** until the onboarding and release checks in sections 3 and 4 pass.

Evidence: [2026-11-16 end-to-end regression report](./portfolio-case-studies-e2e-regression-report-2026-11-16.md), [2026-11-06 content audit](./portfolio-content-audit-2026-11-06.md), and [security boundary test log](./portfolio-security-boundary-test-log.md).

## 2. Frozen formatting specification

These are the approved editorial rules for portfolio/case-study content and assistant answers. They do not imply that every rule is mechanically enforced at runtime.

### Source and attribution

- Answer a portfolio or case-study question only from retrieved portfolio context.
- Return only source URLs present in the retrieved chunks and relevant to the answer. The API carries attribution in `sources` (`title`, `url`, and retrieval `score`); do not invent URLs or imply that an unrelated page substantiates a claim.
- If no supporting passage is retrieved, use the existing no-verified-answer fallback and return no citations. Do not rely on historical evaluation data as current evidence.
- Do not transfer a technology stack, metric, client result, or project detail from one portfolio item to another.

### Assistant answer template

**Supported answer:** one concise sentence, at most 300 characters, followed by the retrieved source link(s) in the API/widget source area. State only the fact asked for and supported by the source.

**Unsupported, confidential, or unapproved detail:** “I don’t have a verified public source for that detail. Please check the relevant portfolio page or contact XICTEK Systems.”

The unsupported-detail wording is an editorial template, not a requirement to disclose whether confidential information exists. Never confirm or deny a private fact.

### Case-study content template

Use the fields below for each proposed story. Keep one project per page/source record and use the same heading order. Leave unsupported fields out; do not fill gaps by inference.

```text
# [Approved public project title]

**Publication status:** Public-approved | Held | Rejected
**Public attribution:** [Named client, only if explicitly authorized; otherwise approved anonymized label]
**Industry:** [Only if substantiated and approved]
**Source URL:** [Canonical public URL]
**Content owner / approver:** [Named accountable person]
**Client authorization:** [Record ID/location in restricted system; approval date]
**Last reviewed / next review:** [YYYY-MM-DD / YYYY-MM-DD]

## Overview
[Brief factual project summary]

## Challenge
[Approved public description; omit sensitive operational details]

## Solution
[Only work and capabilities supported by approved evidence]

## Technology
[Only technologies explicitly attributed to this project in approved evidence]

## Outcomes
[Each metric with definition, baseline, measurement period, method, evidence
reference, and approver; otherwise omit this section]
```

### Text layout and chunking

- Keep the title, project summary, technology description, and any approved outcomes adjacent and clearly labeled within that project's content.
- Separate projects with clear headings; do not combine multiple clients into a single narrative or share a result across stories.
- The ingestion configuration is frozen at **900 characters per chunk / 180 characters overlap** for `/portfolio` and nested `/portfolio/...` paths. Other pages retain **1,200 / 200**. Do not change these values as part of routine content onboarding.
- These are character-based chunk settings, not token limits. The chunking test is synthetic/local and does not guarantee every real page's fields will co-occur.

## 3. Safe case-study onboarding guide

### Gate A — Intake and authorization

1. Assign a named content owner and an independent reviewer.
2. Keep the client's identity, contracts, raw evidence, and authorization record in the approved restricted system; do not add confidential source records or credentials to this repository.
3. Obtain written client approval for the exact public summary, visuals, client naming/anonymization level, and each intended channel. Public visibility or anonymization alone is not consent.
4. If authorization is absent, ambiguous, expired, or narrower than the proposed use, mark the item **Held** and stop. Do not add it to a crawlable page or index.

### Gate B — Claim verification and editorial review

5. Attach a traceable source for every material factual claim. For each numerical outcome, retain the definition, baseline, measurement period, calculation method, evidence location, and accountable approver.
6. Confirm that project technologies and outcomes are explicitly attributed to this project, not inferred from other work or a historical FAQ/evaluation corpus.
7. Remove personal data, credentials, security details, trade secrets, and non-public operational information. Redact only under the client's approved publication terms; redaction does not substitute for authorization.
8. Fill in the case-study content template and mark status **Public-approved** only after all required approvals and evidence are recorded. Otherwise keep it **Held** or **Rejected**.

### Gate C — Source and index review

9. Publish only the approved version at an identified canonical URL, or add it to the explicitly reviewed local portfolio source set. Record the URL, owner, approval date, and next review date in the source register.
10. Before a crawl, review all pages that the configured seed URLs can reach. The current ingestion command crawls allow-listed domains and rebuilds the whole index; it is not a portfolio-only incremental import. Do not run it while held content would be reachable and ingested.
11. From the repository root, rebuild only after the crawlable source set has passed approval:

    ```powershell
    python -m src.xictek_website_assistant.ingest
    ```

12. Inspect the resulting `data/index/chunks.json`: confirm it is nonempty, every new chunk has the expected canonical source URL, no held/unapproved content appears, and each claim remains with the correct project/title. Verify source URL filtering and chunk boundaries; the 900/180 configuration is specific to portfolio paths.
13. Re-run the focused tests:

    ```powershell
    python -m pytest tests\xictek_website_assistant\test_endpoint.py tests\xictek_website_assistant\test_grounded_portfolio.py tests\xictek_website_assistant\test_vector_store.py tests\xictek_website_assistant\test_guardrails.py tests\xictek_website_assistant\test_portfolio_chunking.py -q
    ```

14. Against the populated index and intended deployed endpoint, manually verify: supported factual answer and source; unsupported technology/metrics fail closed; confidential probes do not reveal or confirm private facts; instruction override is refused; source links resolve to supporting pages; and the concise answer format remains intact. A mocked test alone is not production approval.

### Gate D — Release record and maintenance

15. Record index build date, source list, approver, test results, reviewer, and release decision. If any check fails or the source set cannot be audited, do not release the rebuilt index.
16. Restart the service after replacing the index so its cached vector store reloads. Confirm the deployed index-status endpoint reports a built index and the expected chunk count.
17. Review each approved story when its source changes and at least quarterly. Reconfirm authorization and evidence before renewing approval. On withdrawal or expiry, remove the content from its source, rebuild the index, and verify the withdrawn facts are no longer retrievable.

## 4. Current release checklist

| Gate | Current state |
|---|---|
| HisabDo identity and displayed features, narrowly scoped | **Approved in local source** |
| Three anonymized client-style narratives | **Held; authorization/evidence not recorded** |
| Homepage transaction/corruption metrics | **Held as unverified** |
| Checked-in portfolio index metadata | **Empty; requires approved rebuild** |
| Local API-path and boundary regressions | **Pass in mocked/in-memory tests** |
| Populated-index audit and live provider/deployed endpoint checks | **Not run** |
| Production confidentiality sign-off | **Not granted** |

Do not treat this formatting freeze as approval to publish or index held content. A source change, authorization withdrawal, or chunking-configuration change requires a new review and release record.
