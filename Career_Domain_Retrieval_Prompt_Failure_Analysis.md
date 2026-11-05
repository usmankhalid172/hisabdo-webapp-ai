# Career Domain Retrieval & Prompt-Failure Review

**Task owner:** Muhammad Daniyal  
**Review date:** 5 November 2026  
**Repository archive reviewed:** `hisabdo-webapp-ai-main (3).zip` (latest supplied main-branch archive)  
**Scope:** XICTEK Systems Careers and Internship FAQs  
**Review type:** Repository/index inspection + analysis of the 10 live chatbot transcripts supplied for the previous Day 7 evaluation  
**Status:** Findings documented; corrective work not yet implemented

## 1. Executive summary

The career FAQ content exists in the saved index, but retrieval and answer-generation behavior are not consistently turning it into complete, company-specific answers.

The 10 supplied live chatbot responses were previously graded as **5 pass, 1 partial, and 4 fail**. The repeated failure pattern is especially clear for internship questions: eligibility, benefits, and the learning roadmap received the same duration-only answer (“The internship program lasts 12 weeks.”). A UI/UX skills question also failed once with a generic job list, then passed when paraphrased.

The repository inspection identifies four principal causes:

1. **No company/domain filter:** XICTEK and HisabDo pages are stored in the same 976-chunk index. Retrieval can return `hisabdo.app` Careers chunks for a question explicitly about XICTEK.
2. **Weak target-chunk retrieval for multi-part questions:** the internship-benefits chunk `faq-92` is not returned for the “benefits and duration” query. In a raw similarity inspection, its score was approximately 0.196, just below the configured 0.20 threshold.
3. **Prompt/answer-selection weakness:** the system prompt says to answer only from context and not guess, but does not require the model to identify every requested sub-question, prioritize exact FAQ matches, distinguish XICTEK from HisabDo, or verify that each part is answered. For eligibility and roadmap questions, the relevant chunk can be retrieved, yet the supplied live answer still repeats duration.
4. **Coarse fallback state:** the service labels a response `answered` whenever at least one chunk passes the threshold. It does not establish that the retrieved chunks answer the actual question. A weak or cross-domain match can therefore be treated as sufficient context instead of triggering a clarification or safe fallback.

**Overall assessment:** The content corpus is not simply missing the career facts, and the FAQ chunks are generally small and question/answer-specific. The higher-impact issues are source filtering, retrieval threshold/ranking, and prompt-level completeness checks.

## 2. Evidence and review method

### Sources examined

- Latest supplied repository ZIP: `hisabdo-webapp-ai-main (3).zip`.
- `src/xictek_website_assistant/prompts.py`
- `src/xictek_website_assistant/service.py`
- `src/xictek_website_assistant/embeddings.py`
- `src/xictek_website_assistant/vector_store.py`
- `src/xictek_website_assistant/config.py`
- `src/xictek_website_assistant/ingest.py`
- `src/xictek_website_assistant/data/xictek_faq_raw.jsonl`
- `src/xictek_website_assistant/data/index/chunks.json`
- `src/xictek_website_assistant/data/index/metadata.json`
- User-supplied `Live_Chatbot_10_Query_Results.csv` and previous Day 7 evaluation report.

### Method

- Inspected the persisted index and identified the exact FAQ chunk IDs for XICTEK Careers, XICTEK Internship, and HisabDo Careers.
- Re-ran local query embedding and vector retrieval against the saved index using the repository's current query expansion, MMR selection, `top_k=8`, and `relevance_threshold=0.20`.
- Compared expected target FAQ chunks against the returned top-eight list.
- Compared the ten supplied live answers with the relevant source facts.
- Reviewed the prompt, response assembly, source construction, and fallback conditions in code.

**Important boundary:** The ten chatbot transcripts are user-supplied live outputs from the previous evaluation. This review did not make a new production request or claim fresh production behavior. The retrieval checks are local/offline against the saved repository index; they are not a production API benchmark.

## 3. Failure classification

| Failure class | Finding | Evidence | Severity |
|---|---|---|---|
| Missing/weak retrieval | Benefits fact exists but target chunk is not retrieved for combined benefits/duration questions | `faq-92` is present in the index but is absent from the relevant top-eight retrieval; one combined query gave it a raw score around 0.196, below threshold 0.20 | High |
| Wrong source selection | XICTEK and HisabDo Careers chunks compete in one global index | `faq-187`, `faq-192`, `faq-191`, and `faq-195` are HisabDo content and can appear in XICTEK Careers results | High |
| Prompt/answer completeness | Model repeats duration instead of answering eligibility, benefits, or roadmap | Live Q7, Q9, Q10; relevant chunks `faq-93`, `faq-92`, and `faq-94` exist in the saved index | High |
| Fallback/intent classification | Any non-empty match set is treated as an answered request | `service.py` sets `intent="answered"` when `matches` is non-empty, without checking that the chunks support the requested fact | High |
| Content ambiguity | Open-positions FAQ appends “Student or Recent Graduate?” to the role list | XICTEK Careers raw fact and `faq-74`; the audience phrase can be mistaken for a fifth job title | Medium |
| Citation/source relevance | Live answers sometimes cite broad technical blog pages rather than the role-specific Careers page | Q2 cites a full-stack guide; Q3 cites general mobile-development articles | Medium |
| Configuration/provenance drift | README and index metadata do not fully reflect the current retrieval implementation | README describes the older multilingual embedding model/defaults; `embeddings.py` uses TF-IDF; `metadata.json` still names the multilingual sentence-transformer | Medium |

## 4. Repository retrieval-flow review

### 4.1 Current flow

The inspected request path is:

1. Input length and prompt-injection checks run in `guardrails.py`.
2. The message is transformed by `embed_query()` in `embeddings.py`.
3. `VectorStore.query()` selects up to eight chunks using the configured threshold and MMR diversification.
4. The selected chunk text is concatenated into one context string.
5. `GroqLLMProvider` sends the system prompt, conversation history, context, and current question to the LLM.
6. The service returns the generated answer and the URLs for all retrieved chunks.

### 4.2 Retrieval configuration

- Index size: **976 chunks**.
- Configured `top_k`: **8**.
- Configured relevance threshold: **0.20**.
- MMR lambda: **0.5** (balanced relevance/diversity).
- Current query embedder: TF-IDF with a query-side synonym dictionary.
- The index includes both `xicteksystems.com` and `hisabdo.app` content.

The retrieval code does not filter candidates by the company/product named in the question. The source URL is stored on each chunk, but it is used to construct citations after retrieval rather than to constrain retrieval.

### 4.3 Target-chunk retrieval results

Expected target IDs used for the ten-question review:

| Query | Expected chunk | Position in local top 8 | Observation |
|---|---|---:|---|
| Q1 Current positions | `faq-74` | 3 | XICTEK remote-work chunk and a HisabDo Careers chunk appear before it |
| Q2 Senior Full-Stack skills | `faq-75` | 1 | Correct role chunk retrieved |
| Q3 Mobile App skills | `faq-76` | 1 | Correct role chunk retrieved |
| Q4 Cloud Architect skills | `faq-77` | 1 | Correct role chunk retrieved |
| Q5 UI/UX skills | `faq-78` | 1 | Correct role chunk retrieved despite live answer failure |
| Q6 Internship offer + duration | `faq-89` | 1 | Duration dominates; benefit chunk not selected |
| Q7 Internship eligibility | `faq-93` | 2 | Eligibility chunk retrieved, but live answer only gave duration |
| Q8 UI/UX paraphrase | `faq-78` | 1 | Correct chunk retrieved and live answer passed |
| Q9 Internship benefits | `faq-92` | Not in top 8 | Benefit chunk missed; HisabDo internship and unrelated XICTEK chunks appear |
| Q10 Internship roadmap | `faq-94` | 2 | Roadmap chunk retrieved, but live answer only gave duration |

Local retrieval summary from the prior Day 7 benchmark: **Hit Rate@5 90%, Precision@5 18%, MRR@5 0.7333**. These metrics use one designated target FAQ per query; precision is therefore intentionally strict and low when the remaining returned chunks are merely adjacent or irrelevant.

### 4.4 Chunking assessment

The inspected career FAQ index entries are mostly clean atomic Q/A chunks:
- `faq-74` to `faq-83`: XICTEK Careers.
- `faq-89` to `faq-96`: XICTEK Internship.
- `faq-184` to `faq-196`: HisabDo Careers.

This is not evidence of widespread character-splitting or broken paragraph boundaries. The main chunking/metadata concern is that each chunk stores only ID, title, URL, and text. It has no explicit `brand`, `domain`, `content_type`, `faq_intent`, or `role_name` fields for filtering. The `faq-74` content also combines job titles with “Student or Recent Graduate?” in a single answer, creating a content-boundary ambiguity.

## 5. Prompt-template review

The current `SYSTEM_PROMPT` contains useful high-level safeguards:
- Answer only from retrieved Context.
- Do not invent company facts.
- If the context does not contain an answer, say so and direct the visitor to the relevant page/contact channel.
- Keep responses concise.
- Match the visitor's language and script.

However, it does not include career-domain-specific response rules. Missing controls include:

1. **Sub-question coverage:** no instruction to answer every requested component in a multi-part question.
2. **Fact targeting:** no instruction to match the requested intent (eligibility vs. duration vs. benefits vs. roadmap) to the exact FAQ rather than repeating the most prominent retrieved fact.
3. **Entity isolation:** no explicit rule that a question about XICTEK must not use HisabDo Careers facts, or vice versa.
4. **Evidence-to-claim validation:** no requirement that every career claim be supported by the chunk/source that specifically states it.
5. **Conflict handling:** no explicit policy for conflicting, stale, or ambiguous career facts.
6. **Answer checklist:** no final self-check such as “Did I answer eligibility/benefits/roadmap, not merely repeat duration?”

### Prompt-level recommendation

Add a compact career-answer policy to the system prompt or a dedicated career prompt template:
- Detect the organization/product explicitly named in the question.
- Use only chunks from that organization’s approved domain.
- Identify all requested slots before drafting (e.g., offer + duration).
- Prefer the exact FAQ question/answer match over broad related chunks.
- Answer each requested slot in a separate sentence or bullet.
- If any requested slot is unsupported, state exactly which part is unavailable; do not substitute a related fact.
- Cite only URLs that support the claims actually included.
- Do not turn internship eligibility/audience into a job title.

This prompt change must be paired with retrieval filtering; prompt wording alone cannot reliably compensate for wrong-source chunks or a missing target chunk.

## 6. Fallback behavior review

The service currently has three relevant outcomes:

- **No retrieved matches:** `context=None`; the prompt is expected to provide a safe “not in the supplied context” response.
- **One or more retrieved matches:** all selected chunks are concatenated and sent to the model; the response intent is set to `answered`.
- **LLM/provider exception:** a fixed temporary-unavailability message is returned with no sources.

The gap is between the first and second states. There is no query-to-evidence coverage check. If the retriever returns a duration chunk for an eligibility question, the service still marks the request as answered. If a HisabDo chunk is among the matches, it is also included in the context. The fallback therefore depends on whether any chunk passes a generic similarity threshold, not whether the requested fact is actually supported.

**Recommended fallback behavior:** after retrieval, validate domain and intent alignment. If no career chunk supports the requested slot, ask a focused clarification or state that the detail is not available in the current XICTEK Careers context and provide the official Careers/Internship URL. Keep the response intent distinguishable as `insufficient_context` (or an equivalent explicit status) rather than treating every non-empty match list as a successful answer.

## 7. Live chatbot failure review

The ten supplied live outputs produced:
- **Pass:** 5/10 (50%)
- **Partial:** 1/10 (10%)
- **Fail:** 4/10 (40%)

Key observations:
- Q5 returned the general role list instead of UI/UX tools; Q8 paraphrased the same intent and passed with “Figma, Design Systems, Prototyping.” This indicates inconsistent answer selection, not a missing UI/UX fact.
- Q6 correctly returned the 12-week duration but omitted the offer/benefits.
- Q7, Q9, and Q10 all returned only the 12-week duration. The relevant eligibility and roadmap chunks are present and retrievable locally; benefits is the notable retrieval miss.
- Q2 and Q3 returned correct technologies but cited general technical articles instead of the role-specific Careers page. The facts are correct, but citation relevance should be improved.

No new live production run or latency measurement was performed for this review.

## 8. Prioritized issue ownership log

The accompanying `Career_Domain_Issue_Ownership_Log.csv` records the proposed owner role, priority, evidence, action, and acceptance criteria.

Named assignees were not supplied in the task brief. Therefore, the log assigns **functional owner roles** and marks the named assignee as **TBD by team lead** rather than inventing employee names. Muhammad Daniyal is the review/report owner.

Recommended order:
1. P1 — Add company/domain-aware retrieval filtering.
2. P1 — Fix internship FAQ intent retrieval and ensure `faq-92` appears for benefits queries.
3. P1 — Add multi-part answer completeness and evidence checks to the career prompt.
4. P1 — Replace the “any match = answered” fallback rule with a relevance/coverage-aware status.
5. P2 — Separate job titles from internship audience wording in the Careers source fact.
6. P2 — Improve role-specific citation selection.
7. P2 — Reconcile README, embedding implementation, index metadata, and dependency versions.

## 9. Acceptance criteria for closure

The domain should not be considered ready for handover until all of the following are demonstrated:

- XICTEK Careers queries retrieve only XICTEK-approved career sources; HisabDo career chunks are excluded unless the user explicitly asks about HisabDo.
- The benefits FAQ chunk `faq-92` is returned in the top five for benefits and combined offer/duration questions.
- Eligibility queries return eligibility requirements, not duration alone.
- Roadmap queries return all four stages (weeks 1–2, 3–6, 7–10, 11–12).
- Combined questions answer every requested part or explicitly identify the unsupported part.
- UI/UX questions consistently return Figma, Design Systems, and Prototyping.
- The job-opening list does not present “Student or Recent Graduate” as a fifth job title.
- Every displayed citation supports the specific answer claim.
- Empty/weak/wrong-domain retrieval triggers an explicit safe fallback rather than a falsely successful `answered` status.
- Retrieval and prompt regression tests pass against a fixed career-domain evaluation set.

## 10. Limitations

- Live response transcripts are supplied evidence from the previous evaluation; no new production session was run.
- The local retrieval benchmark uses the saved repository index, not a freshly crawled live website.
- No code changes, prompt deployment, or production release action was performed.
- Functional owner roles are proposed; actual staff assignees require team-lead confirmation.
- Similarity scores are implementation diagnostics, not calibrated probabilities of answer correctness.

## 11. Files reviewed

- `src/xictek_website_assistant/prompts.py`
- `src/xictek_website_assistant/service.py`
- `src/xictek_website_assistant/embeddings.py`
- `src/xictek_website_assistant/vector_store.py`
- `src/xictek_website_assistant/config.py`
- `src/xictek_website_assistant/ingest.py`
- `src/xictek_website_assistant/data/xictek_faq_raw.jsonl`
- `src/xictek_website_assistant/data/index/chunks.json`
- `src/xictek_website_assistant/data/index/metadata.json`
- `src/xictek_website_assistant/README.md`
- `Live_Chatbot_10_Query_Results.csv`
- `Career_Day7_Final_Evaluation_Report.md`
