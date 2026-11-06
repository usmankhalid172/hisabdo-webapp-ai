# Portfolio Domain Approved Source Register and Content Audit Log

**Audit owner:** Muhammad Mohsin
**Last reviewed:** 2026-11-06
**Scope:** Public XICTEK Systems portfolio, case-study summaries, success-story claims, and related local assistant sources.

## Decision summary

- The current public portfolio page contains the HisabDo product showcase and three anonymized client-style case studies. Public visibility was confirmed on the review date.
- The repository contains no client release, publication consent, contract excerpt, or source evidence supporting the three case studies or their quantified results. Public visibility alone does not establish client authorization or the truth of a claim.
- **Do not approve the three anonymized case studies or their results for knowledge-base reuse** until a named content owner records client publication authorization and evidence for each claim.
- HisabDo's product identity and the features displayed in its official public portfolio are approved for narrowly scoped factual reuse. Do not transfer other case studies' results to HisabDo.
- The live index metadata file is empty. A fresh crawl would currently ingest the portfolio page, so production index rebuild/release remains blocked pending the approval decision or removal of the held material from the public source.
- No live website content was edited: this workspace has no CMS access or documented content-owner authorization. The local HisabDo source was narrowed to the approved product scope.

## Approved source register

| ID | Source | Source owner | Last reviewed | Approved scope / disposition |
|---|---|---|---|---|
| PORT-001 | [XICTEK Systems portfolio](https://www.xicteksystems.com/portfolio) | Unassigned. XICTEK Systems is the publisher; a named content approver is not identified in the reviewed source. | 2026-11-06 | Approved only for HisabDo identity and features already presented on the same official public page. This is not approval for unpublished claims or for client case-study material. |
| PORT-002 | [XICTEK Systems homepage](https://www.xicteksystems.com/) | Unassigned. The homepage identifies Mian Usman Khalid as Founder & CEO, but does not identify a source owner or metric approver. | 2026-11-06 | HisabDo's in-house product identity and public feature description may be used. The “100,000+ business transactions” and “zero data corruption” claims are held pending dated evidence and owner sign-off; do not use as verified success metrics. |
| PORT-003 | `src/xictek_website_assistant/data/portfolio/hisabdo.md` | No source owner recorded; audit reviewer is Muhammad Mohsin. | 2026-11-06 | Rewritten to limit this source to publicly displayed HisabDo identity/features. Client case studies, unrelated technologies, and cross-project outcomes are excluded. |
| PORT-004 | `src/xictek_website_assistant/data/xictek_faq_raw.jsonl` | Dataset curator not recorded. | 2026-11-06 | Historical lexical-evaluation corpus only; not approved as a current source of portfolio facts. Its “publishes work only when it can be shared responsibly” statement is absent from the current page and must not be used as current evidence. |

## Content audit log

| Item | Current public content observed | Authorization / evidence check | Decision and action |
|---|---|---|---|
| HisabDo product showcase | In-house digital khata/expense product with dashboard, ledger, voice entry, analytics, transaction categorization, and customer directory imagery/descriptions. | Presented by XICTEK Systems on its own public site. No external client approval is indicated or needed for the narrowly scoped product description; no independent performance evidence was reviewed. | **Approved with scope limits.** Use the product identity and displayed features only. |
| Logistics & Supply Chain — “AI-Powered Fleet Dispatch & Route Optimization” | Anonymous regional freight-fleet narrative; claims +32% daily delivery throughput, 24% less fuel consumption, sub-second tracking across 200+ vehicles. | No client identity, dated measurement, supporting evidence, or explicit client publication authorization was found in the repository. | **Hold / not approved for KB reuse.** Obtain source evidence and written authorization, or remove the case and claims from the public page before rebuilding the index. |
| HealthTech — “High-Concurrency Healthcare Patient Portal & Telehealth” | Anonymous medical-group narrative; claims 15,000+ monthly appointments, 99.98% uptime with zero data leaks, and 45% fewer no-shows. | No client identity, dated measurement, supporting evidence, or explicit client publication authorization was found in the repository. | **Hold / not approved for KB reuse.** Do not repeat the claims as verified results without evidence and written authorization. |
| FinTech & B2B SaaS — “Multi-Tenant SaaS Subscription & Billing Platform” | Anonymous software-vendor narrative; claims 10x faster onboarding, zero billing errors across thousands of transactions, and automated global VAT/tax reports. | No client identity, dated measurement, supporting evidence, or explicit client publication authorization was found in the repository. | **Hold / not approved for KB reuse.** Obtain source evidence and written authorization, or remove the case and claims from the public page before rebuilding the index. |
| Homepage HisabDo metrics | “100,000+ business transactions” and “zero data corruption.” | Visible publicly on the homepage, but no measurement period, methodology, source evidence, or named approver was found in the repository. | **Hold as unverified.** Do not present as independently verified outcomes until evidence and owner approval are recorded. |
| Legacy local HisabDo source | Previously included a technology stack and generalized custom-project statements not tied to HisabDo; it also described the absence of quantified business results without distinguishing HisabDo from other portfolio items. | Compared with the current live portfolio and homepage on 2026-11-06. | **Updated locally.** [The source file](../src/xictek_website_assistant/data/portfolio/hisabdo.md) now restricts claims to HisabDo and explicitly excludes other client-story results pending authorization. |
| Historical FAQ evaluation corpus | Contains older portfolio-derived facts, including the claim that work is published only when it can be shared responsibly. | The statement was not present on the current portfolio page during this review. The corpus is read by the offline evaluation script, not by the website ingestion pipeline. | **Retain as historical evaluation input only.** Do not treat as an approved current source. Rebaseline the benchmark against a reviewed source corpus before using its scores for current-content decisions. |

## Source ownership and records required

No named portfolio content owner or client-authorization records were found in
the reviewed workspace. Before approving a held item, record at minimum:

1. A named source owner and reviewer.
2. The client/project identity in a restricted internal record, without
   exposing it publicly unless separately authorized.
3. Written client approval for the specific public summary, visuals, and
   anonymization level.
4. Evidence, measurement period, calculation method, and accountable approver
   for each numerical result.
5. Approval date, last-reviewed date, and next review date.

## Knowledge-base and release controls

- Do not rebuild or release the portfolio index while held client stories or
  unsupported metrics would be ingested from the live portfolio/homepage.
- After approval, rebuild from the reviewed source, verify the indexed
  portfolio chunks and URLs, and rerun portfolio-answer checks. The current
  checked-in `chunks.json` is empty, so previous offline tests do not establish
  what a rebuilt index will contain.
- If approval is not obtained, remove the held summaries and claims from the
  public source before crawling it. This audit does not claim that public-site
  content was removed.
- Review this register whenever the source page changes and at least quarterly.

## Evidence reviewed

- Live [portfolio page](https://www.xicteksystems.com/portfolio) and
  [homepage](https://www.xicteksystems.com/), fetched 2026-11-06.
- Local source file `src/xictek_website_assistant/data/portfolio/hisabdo.md`.
- Historical fact corpus `src/xictek_website_assistant/data/xictek_faq_raw.jsonl`.
- [Portfolio retrieval evaluation](./portfolio-retrieval-evaluation.md),
  [security boundary test log](./portfolio-security-boundary-test-log.md),
  and [domain failure log](./portfolio-domain-failure-log-2026-11-05.md).
