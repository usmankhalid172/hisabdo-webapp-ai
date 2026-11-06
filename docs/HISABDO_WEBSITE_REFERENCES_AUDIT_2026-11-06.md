# HisabDo Website References Audit

**Audit date:** 6 November 2026  
**Scope:** Public HisabDo product landing pages, public product documentation, and feature reference links  
**Purpose:** Record approved-source candidates, compare claims across the public site, and flag claims that need product-owner confirmation before ingestion or chatbot use.

## Executive summary

The official HisabDo website provides useful references for the product's basic purpose and advertised capabilities: offline-first record keeping, customer and transaction records, expense tracking, PDF statements, voice entry, analytics, and optional sign-in/cloud synchronization. The FAQ and Privacy Policy use more qualified wording about **supported** records and synchronization; that wording should control over broad landing-page copy.

The site is not a single consistent specification. The landing page contains high-precision performance, security, user-count, and accuracy claims that are not substantiated by the public documentation reviewed. Some checked-in retrieval chunks also disagree with the current FAQ or policy. Treat these as documentation and source-freshness findings, not proof that the product itself does or does not implement the claims.

**Recommendation:** Use the FAQ, Privacy Policy, About/App pages, and the official Google Play listing as source candidates, with page-level citations and crawl dates. Keep legal/data-handling answers tied to the Privacy Policy. Do not state exact security protocols, performance figures, adoption counts, guaranteed accuracy, or broad sync coverage unless the product owner supplies current approved specifications and evidence.

## Audit method and limits

- Reviewed the public pages listed in the source inventory below on 6 November 2026; the site is mutable.
- Compared product statements with the repository's checked-in retrieval snapshot at `src/xictek_website_assistant/data/index/chunks.json`.
- The repository snapshot contains **421 chunks whose URLs are on `hisabdo.app`** across product, legal, blog, career, and other pages. Chunk records include an ID, title, URL, and text, but no crawl timestamp, content hash, or source-version field. This audit did not inspect the deployed production index.
- This is a public-reference audit. No app binary, source code, backend configuration, or internal approved product specification was supplied for independent verification.
- “Verified” below means the claim is explicitly present in a reviewed official public page. It does **not** mean independently tested in the app.

## Verified source inventory

| Source | URL | Intended use | Audit status |
|---|---|---|---|
| HisabDo home / product landing page | <https://hisabdo.app/> | Product overview, advertised feature summaries, links to help/legal/product pages | Official page reviewed. Marketing copy includes unsupported precision claims; do not use it alone for security/performance answers. |
| About HisabDo | <https://hisabdo.app/about> | Product purpose, users, core workflow, offline-first positioning | Official overview reviewed. Supports broad feature statements; directs readers to FAQ and Privacy Policy for behavior/data handling. |
| App overview and workflow | <https://hisabdo.app/about-app> | Dashboard, voice entry, statements, analytics, supported languages/currencies, local records and sync | Official page reviewed. Useful for feature summaries; use qualified wording for sync and supported data. |
| Help Center FAQ | <https://hisabdo.app/faq> | Answers on features, guest mode, sync, backup, languages, currencies, platform and support | Official product Q&A reviewed. Preferred public source for user-facing feature answers; contains details that conflict with some other pages/index chunks. |
| Privacy Policy | <https://hisabdo.app/privacy-policy> | Data categories, local/cloud storage, sync scope, third parties, security, retention, user rights | Official policy reviewed; effective date shown as 24 September 2026. Preferred source for privacy/data-handling responses. |
| Terms & Conditions | <https://hisabdo.app/terms> | Use terms, data ownership, limitations and legal contact | Official legal page reviewed; effective date shown as January 2025. It may be older than the Privacy Policy and should be reviewed for freshness. |
| Disclaimer | <https://hisabdo.app/disclaimer> | Limits on accuracy/availability, financial advice boundary, external links | Official legal page reviewed; effective date shown as April 2026. Useful for advice and reliability boundaries. |
| HisabDo web app | <https://app.hisabdo.app/> | Separate web app product surface, ledger/expense overview | Official app surface reviewed. Keep distinct from mobile-app claims; its brief landing page does not document all mobile features. |
| XICTEK company page | <https://hisabdo.app/company> | Product/company relationship and high-level product description | Official company/product relationship page reviewed. Not a detailed mobile feature specification. |
| Google Play listing | Linked from the HisabDo pages | Distribution and store-listed app details | Official distribution link is present, but store listing details were not independently audited in this pass. |

## Audit log: claim status and handling

| ID | Claim area | What public sources say | Finding | Priority / recommended handling |
|---|---|---|---|---|
| HDO-01 | Product purpose | About/FAQ describe HisabDo as an offline-first khata/ledger for shopkeepers, freelancers, and small businesses, covering money in/out, customer balances, and expenses. | Consistent at a high level. | **P2 — Approved for grounded answers** when cited to About or FAQ. |
| HDO-02 | Core features | About/FAQ and app overview describe customer records/history, transactions, expenses, receivables/payables, PDF statements, voice entry, and analytics. | Broad features recur across official pages. Specific feature availability should still be qualified by app/platform/version. | **P2 — Approved with source citation**; avoid promising every feature on every platform or account mode. |
| HDO-03 | Offline support | Landing page uses “100% offline” wording. FAQ and Privacy Policy qualify this as supported local/offline functionality; login, registration, account recovery, and cloud sync require internet. | Broad marketing copy is less precise than the documentation. | **P1 — Normalize wording** to “supported local features can be used offline”; state online-dependent exceptions when relevant. |
| HDO-04 | Cloud synchronization | FAQ and Privacy Policy say only supported customer, income, and expense records may sync when signed in and online; they explicitly do not promise every local record syncs. | Supported data scope is limited. Some checked-in chunks use broader “sync data” wording. | **P1 — Restrict retrieval content** to supported data types and conditions. Do not claim full-device or every-record sync. |
| HDO-05 | Backup and restore | FAQ distinguishes local backup from synchronization; Privacy Policy says local backup/restore is not cloud restore. Landing copy sometimes groups backup and cloud restore together. | Concepts are easy to conflate and current public pages are not uniformly precise. | **P1 — Separate local backup, cloud sync, and restore** in the KB. Ask the product owner to confirm the supported restore paths. |
| HDO-06 | Security and encryption | Home page claims encrypted SQLite, AES-256 cloud encryption, “zero data leakage,” and “air-gapped” data. Privacy Policy documents HTTPS, authentication, access control, Supabase, and reasonable security measures, but does not specify AES-256 or describe the app as air-gapped. It also identifies third-party services/advertising technology. | Landing-page security claims exceed or conflict with the reviewed policy. “Air-gapped” is especially inconsistent with optional cloud sync and website third-party services. | **P1 — Hold precise claims** (AES-256, zero leakage, air-gapped, no external transmission) until security/product owner approves exact wording and evidence. Cite the Privacy Policy for current data handling. |
| HDO-07 | Supported currencies | FAQ and app overview list PKR, USD, and INR. The landing page's trade-specific copy mentions EUR and AED for multi-currency invoicing. | Public pages provide different scopes; no product specification confirms whether EUR/AED are supported app-wide or only promotional examples. | **P1 — Do not merge into a single currency list.** Confirm supported currency behavior with product owner; until then use the FAQ list and note the discrepancy. |
| HDO-08 | Supported languages | App overview lists Urdu, English, Hindi, Arabic, and Roman Urdu. A checked-in home-page chunk says “more than five” but names only those five. | “More than five” is internally inconsistent with the named list and lacks a sixth language. | **P2 — Use only the five named languages** unless an approved source enumerates more. |
| HDO-09 | Android compatibility | The current FAQ says Android 6.0+ and recommends Android 8.0+. An older indexed FAQ chunk states Android 8.0+ as the minimum. | Repository retrieval snapshot disagrees with the currently reviewed FAQ. | **P1 — Refresh stale chunk** and preserve “minimum” versus “recommended” distinction. Verify against the current Play listing before giving device compatibility advice. |
| HDO-10 | Price/free claims | Home/FAQ/About describe free download/use and no mandatory subscription or hidden fees. | Broadly consistent on reviewed pages, but future pricing/availability can change. | **P2 — Cite current FAQ or store listing** and avoid “free forever” as an unconditional guarantee. |
| HDO-11 | Quantified performance, accuracy, adoption | Home page includes 0s/11ms latency, 99.4% voice accuracy, 100K+ records, 35K+ shopkeepers, and 4.8/5 rating. The public documentation reviewed gives no methodology, date, or supporting measurement for most of these precise figures. | Claims are present as marketing copy, not independently verifiable product specifications in the reviewed material. | **P1 — Mark unverified.** Do not present as factual chatbot answers without dated evidence, measurement methodology, and owner approval. |
| HDO-12 | Financial record accuracy/advice | Terms and Disclaimer say the app does not verify/audit user-entered records and is not financial, tax, accounting, or legal advice. | Clear scope boundary in legal sources. | **P1 — Preserve as a safety boundary**; never promise “100% calculation accuracy” or personalized financial advice. |
| HDO-13 | Support response time/contact | Current FAQ says the team aims to respond within 48 hours and lists official support routes. | Response-time promise is an aim, not a guarantee; old repository material may contain a different time. | **P2 — Phrase as “aims to respond within 48 hours”** and cite FAQ. Refresh older response-time claims. |
| HDO-14 | Sign-out/local data retention | Privacy Policy states signing out currently clears the local SQLite database, while cloud data remains associated with the account. | Important behavioral detail documented only in the policy reviewed. | **P1 — Keep tied to the current Privacy Policy** and ensure the app behavior remains accurate; this should not be paraphrased as deletion of cloud data. |

## Source and ingestion recommendations

1. Use the Privacy Policy for privacy, storage, synchronization, third parties, deletion, and retention. Use the FAQ for feature Q&A. Use About/About-App for overview only.
2. Add provenance to each indexed chunk: canonical URL, page title, crawl timestamp, content hash or version, section heading, and an approved-source status. The current chunk schema has only `id`, `title`, `url`, and `text`.
3. Maintain an approved-claims register for sensitive/quantified claims (security protocols, performance, usage counts, app compatibility, pricing, and data behavior), with an owner and evidence reference.
4. Use canonical page URLs and remove duplicate/stale chunks on re-ingestion. Prefer one current source per claim; avoid combining marketing copy with legal policy into a stronger claim than either source supports.
5. Re-crawl the checked-in HisabDo chunks and compare them to current pages before release. At minimum, update Android minimum version, the language count wording, currency scope, sync/backup boundaries, and support-response phrasing.
6. Treat Google Play as a separate source for current app availability/version/compatibility and record the listing date. This audit confirmed the official store link exists but did not validate its contents.

## Release recommendation

**Reference package status: Needs owner review before release as an authoritative HisabDo specification.** The public source inventory is usable for a grounded prototype after stale/contradictory claims are controlled. Security, synchronization, backup/restore, numeric performance claims, user counts, and device compatibility should remain flagged until confirmed against current product specifications or evidence.

This document records observed public-page and checked-in-index content as of the audit date. It does not certify the deployed chatbot's index, the current mobile binary, or implementation behavior.
