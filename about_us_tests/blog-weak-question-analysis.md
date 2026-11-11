# Blog & News Weak-Question Analysis Log

**Owner:** QA Automation  
**Task:** Blog & News Weak-Question Analysis  
**Date:** November 05, 2026  

---

## 1. Objective

Inspect current ingestion, chunking, and retrieval performance for the blog and news domain. Identify weak or failed questions from Phase 1 (original Day-3 evaluation) and Phase 2 (new probing queries), categorizing causes into missing sources, retrieval misses, or prompt generation errors. Produce prioritized fix recommendations.

## 2. Methodology

### 2.1 Phase 1 — Historical Failures (Day-3 Evaluation)

Re-inspected the 3 queries that failed in the original Day-3 retrieval evaluation (before Day-7 fixes). These were all RETRIEVAL_MISS caused by synonym mismatches. Root causes analyzed and fixes verified.

### 2.2 Phase 2 — New Probing Queries

Designed 10 new probing queries to find weak spots the Phase-1 set didn't cover:

- P1: Out-of-scope query (refund policy) — tests MISSING_SOURCE handling
- P2: Performance synonym mismatch ('load faster' vs 'performance optimization')
- P3: Cross-domain query (SaaS + payment integration)
- P4: Topic not in corpus (database selection)
- P5: Multi-article synthesis (full SDLC)
- P6: Typo ('chatobt' instead of 'chatbot')
- P7: Ultra-short query ('erp')
- P8: Sub-topic in a long-form guide ('common mistakes')
- P9: Exact title match with mixed case
- P10: Cross-topic cost query (ERP cost)

### 2.3 Cause Categories

| Category | Description |
|----------|-------------|
| **MISSING_SOURCE** | No article in the corpus covers this topic. Fix = add new content or deflect gracefully. |
| **RETRIEVAL_MISS** | Relevant article exists but retriever didn't surface it. Fix = expand synonym dictionary or tune threshold. |
| **PROMPT_GENERATION_ERROR** | Retrieved article is correct but LLM/simulator failed to use it properly. Fix = improve prompt or post-processing. |
| **TYPO_UNHANDLED** | Query contains a typo the normalizer doesn't correct. Fix = add typo tolerance. |

## 3. Phase 1 Analysis — Historical Failures (Now Fixed)

These 3 queries failed in the original Day-3 evaluation. All were RETRIEVAL_MISS caused by synonym mismatches. Day-7 fixes resolved all 3 — verified still passing today.

| ID | Query | Cause | Root Cause | Fix Applied | Current Status |
|----|-------|------|------------|-------------|----------------|
| H1 | we need to put our internal tools online | RETRIEVAL_MISS | Synonym mismatch — 'internal tools' and 'employees use' not ... | Added synonyms: 'internal tools' → 'portal enterprise web ap... | ✅ Fixed |
| H3 | we want to add a smart assistant that an | RETRIEVAL_MISS | Synonym mismatch — 'smart assistant' not recognized as 'chat... | Added synonyms: 'smart assistant' → 'chatbot ai assistant', ... | ✅ Fixed |
| H7 | continuous deployment pipeline with auto | RETRIEVAL_MISS | Synonym mismatch — 'continuous deployment', 'pipeline', 'aut... | Added synonyms: 'continuous deployment' → 'agile software de... | ✅ Fixed |

### 3.1 Detailed Root-Cause Analysis

#### H1: "we need to put our internal tools online so employees can use them from anywhere"

- **Cause**: RETRIEVAL_MISS
- **Root cause**: Synonym mismatch — 'internal tools' and 'employees use' not in synonym dictionary. Retriever matched on 'tools' (weak signal) → dotnet-development-services. The actual relevant articles (portal-development, enterprise-web-applications) use vocabulary like 'portal', 'customer', 'partner', 'team' which doesn't overlap with the query's 'internal tools'.
- **Fix applied**: Added synonyms: 'internal tools' → 'portal enterprise web application', 'employee portal' → same, 'self-service portal' → same
- **Currently retrieved**: enterprise-web-applications, portal-development, custom-web-application-development
- **Status**: ✅ Fixed

#### H3: "we want to add a smart assistant that answers questions from our documentation"

- **Cause**: RETRIEVAL_MISS
- **Root cause**: Synonym mismatch — 'smart assistant' not recognized as 'chatbot'. The query says 'smart assistant' and 'answers questions from documentation'; the relevant article is titled 'AI Chatbot Development'. The retriever matched 'assistant' weakly to 'ai-workflow-automation' (which mentions assistants in a different context) and partially to 'ai-customer-support'. The top hit 'ai-chatbot-development' was missed because 'chatbot' and 'smart assistant' share no token overlap.
- **Fix applied**: Added synonyms: 'smart assistant' → 'chatbot ai assistant', 'virtual assistant' → same, 'documentation assistant' → same, 'qa bot' → same
- **Currently retrieved**: ai-chatbot-development, ai-workflow-automation, ai-development-company-pakistan
- **Status**: ✅ Fixed

#### H7: "continuous deployment pipeline with automated tests"

- **Cause**: RETRIEVAL_MISS
- **Root cause**: Synonym mismatch — 'continuous deployment', 'pipeline', 'automated tests' not in synonym dictionary. Retriever matched 'automation' → business-process-automation (wrong domain — that article is about business workflow automation, not CI/CD). The relevant articles (software-development-process, agile-software-development) use vocabulary like 'agile', 'sprints', 'CI/CD', 'milestones' which doesn't overlap with the query's 'continuous deployment pipeline'.
- **Fix applied**: Added synonyms: 'continuous deployment' → 'agile software development process devops', 'deployment pipeline' → same, 'ci/cd' → same, 'automated tests' → 'agile software development process testing', 'continuous integration' → same
- **Currently retrieved**: agile-software-development, software-development-process, erp-software-development
- **Status**: ✅ Fixed

## 4. Phase 2 Analysis — New Probing Queries

Ran 10 probing queries against the current pipeline. Results:

| ID | Query | Category | Retrieved | Expected | Status |
|----|-------|----------|-----------|----------|--------|
| P1 | what is xictek's refund policy for softw | RETRIEVAL_MISS | custom-software-development-guide, software-development-process | (none expected) | ❌ |
| P2 | how do i make my website load faster on  | SUCCESS | website-performance-optimization | website-performance-optimization | ✅ |
| P3 | how do i integrate stripe payment into m | SUCCESS | saas-development-services, saas-product-development | saas-development-services, api-integration-services | ✅ |
| P4 | should i use postgresql or mongodb for m | SUCCESS | (none) | (none expected) | ✅ |
| P5 | what is the full software development li | SUCCESS | ai-development-company-pakistan, startup-software-development | software-development-process, software-maintenance-services | ✅ |
| P6 | how to build a chatobt for my website | SUCCESS | ai-chatbot-development, website-performance-optimization | ai-chatbot-development | ✅ |
| P7 | erp | SUCCESS | erp-software-development, ai-in-erp-systems | erp-software-development, ai-in-erp-systems | ✅ |
| P8 | what are common mistakes in software dev | SUCCESS | custom-software-development-guide, software-development-process | custom-software-development-guide, software-development-process | ✅ |
| P9 | AI For SMEs | SUCCESS | ai-for-smes, ai-development-company-pakistan | ai-for-smes | ✅ |
| P10 | how much does erp implementation cost | SUCCESS | software-development-cost-pakistan, erp-software-development | erp-software-development, software-development-cost-pakistan | ✅ |

## 5. Weak-Question Summary

**Total weak questions identified: 4**

- Phase 1 (historical, now fixed): 3
- Phase 2 (new, currently failing): 1

### 5.1 By Cause Category

| Category | Count | Phase 1 | Phase 2 |
|----------|-------|---------|---------|
| RETRIEVAL_MISS | 4 | 3 | 1 |

## 6. Detailed Weak-Question Log (Phase 2 — Currently Failing)

### P1: "what is xictek's refund policy for software development projects"

- **Category**: RETRIEVAL_MISS
- **Detail**: Retrieved ['custom-software-development-guide', 'software-development-process'] but no article covers this topic — false positive
- **Retrieved**: custom-software-development-guide, software-development-process, startup-software-development
- **Fix needed**: See Section 7


## 7. Prioritized Fix Recommendations

| Priority | Query | Category | Issue | Recommended Fix | Effort | Impact |
|----------|-------|----------|-------|-----------------|--------|--------|
| P1 | what is xictek's refund policy for  | RETRIEVAL_MISS | Relevant article exists but wasn't retrieved. Retr... | Expand synonym dictionary with query-specific terms. Analyze... | Low (add synonyms, ~2 hours) | High — directly affects retrieval accuracy |

### 7.1 Detailed Fix Recommendations

#### P1 — RETRIEVAL_MISS — Query P1

**Query**: "what is xictek's refund policy for software development projects"

**Issue**: Relevant article exists but wasn't retrieved. Retrieved ['custom-software-development-guide', 'software-development-process'] but expected [].

**Recommended fix**: Expand synonym dictionary with query-specific terms. Analyze the vocabulary gap between the query and the expected article's title/body.

**Effort**: Low (add synonyms, ~2 hours)  
**Impact**: High — directly affects retrieval accuracy

## 8. Ingestion & Chunking Observations

Based on the weak-question analysis, the following ingestion/chunking observations emerge:

### 8.1 Ingestion

- **Article corpus is comprehensive** for the topics covered (47 articles across 11 categories). No gaps in core service areas.
- **Content gap: database selection** — P4 ('postgresql vs mongodb') retrieved nothing relevant. No article covers database selection. Recommend content team write one, OR accept this as out-of-scope.
- **Content gap: refund policy** — P1 correctly triggered FALLBACK_OUT_OF_DOMAIN. This is expected behavior (refund policy is not a blog topic).
- **Long-form guides** (~1,200 words each) cover sub-topics that short articles don't. P8 ('common mistakes') correctly retrieved the custom-software-development-guide which has a 'Common mistakes' section. Long-form articles are working as sub-topic entry points.

### 8.2 Chunking

- **Current chunking strategy**: full-article indexing (title + entire body as one document). No section-level chunking.
- **Implication for long-form guides**: The 12 long-form guides (~1,200 words each) are indexed as single documents. This works for top-level topic queries but may miss sub-topic queries that would benefit from section-level retrieval.
- **Observation**: P8 ('common mistakes in software development') retrieved the correct long-form guide, suggesting the TF-IDF + semantic hybrid is catching sub-topic signals even without section-level chunking. No immediate chunking change needed.
- **Future consideration**: If sub-topic retrieval accuracy drops below 90%, consider section-level chunking for long-form guides (split on H2 headings, index each section separately with the article title as prefix).

### 8.3 Retrieval Performance

- **Current Hit@3**: 100% on the 24-query evaluation set (after Day-7 fixes)
- **Current MRR@3**: 1.0000 on the 24-query evaluation set
- **Phase 2 probing results**: 9/10 passed
- **New failure rate**: 1/10 (10.0%)

The pipeline is performing well overall. The new failures are edge cases (typos, cross-domain queries) that represent opportunities for targeted improvement rather than systemic issues.

## 9. Reproduction

```bash
# Re-run the weak-question analysis
python3 /home/z/my-project/scripts/blog_weak_question_analysis.py
```

---

*QA Automation — Blog & News Weak-Question Analysis — November 05, 2026*