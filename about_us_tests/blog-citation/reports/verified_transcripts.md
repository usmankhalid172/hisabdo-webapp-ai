# Verified Example Transcripts — Blog & News Grounded Generation

**Generated:** 2026-11-12T06:48:24.043384Z
**Total transcripts:** 10
**Positive cases:** 7
**Negative controls:** 3

Each transcript shows: query, retrieved articles, full response, and a per-check validation report.

---

## Summary

| ID | Type | Query | Expected | Actual | Result |
|---|---|---|---|---|---|
| T1 | positive | how much does custom software cost in pakistan | PASS | PASS | OK |
| T2 | positive | custom software development guide | PASS | PASS | OK |
| T3 | positive | what is the agile software development process | PASS | PASS | OK |
| T4 | positive | tell me about ai chatbot development | PASS | PASS | OK |
| T5 | positive | explain progressive web apps | PASS | PASS | OK |
| T6 | positive | how much do you charge for software development se... | PASS | PASS | OK |
| T7 | positive | best recipe for chicken biryani | PASS | PASS | OK |
| T8 | negative_control | custom software development cost | FAIL | FAIL | OK |
| T9 | negative_control | custom software development cost | FAIL | FAIL | OK |
| T10 | negative_control | tell me about hisabdo expense management app | FAIL | FAIL | OK |

---

## T1 — Normal citation — should retrieve cost article and cite [1]

**Type:** positive
**Query:** `how much does custom software cost in pakistan`
**Timestamp:** 2026-11-12T06:48:10.580233Z

### Retrieved Articles

| # | Slug | Title | Score | Published |
|---|---|---|---|---|
| 1 | `software-development-cost-pakistan` | Software Development Cost in Pakistan: What Shapes the Budget | 0.4521 | 2026-09-07 |
| 2 | `software-development-company-pakistan` | How to Choose a Software Development Company in Pakistan | 0.317 | 2026-09-07 |
| 3 | `custom-software-development` | Custom Software Development: When Bespoke Software Makes Sense | 0.2942 | 2026-09-07 |

### Response

```
Based on the Software Development Cost in Pakistan: What Shapes the Budget article [1], the key considerations for your question are covered in the article's discussion of this topic. The article emphasizes starting with a clear business outcome before making technical decisions [1].

**Sources:**
[1] Software Development Cost in Pakistan: What Shapes the Budget — https://www.xicteksystems.com/blog/software-development-cost-pakistan

```

### Validation Report

**Overall:** PASS

| Check | Rule | Passed | Details |
|---|---|---|---|
| check_1_orphan_markers | Every [n] in body has a Sources entry | YES | markers_in_body=[1]; source_indices=[1] |
| check_2_padded_sources | Every Sources entry has a [n] in body | YES | source_indices=[1]; markers_in_body=[1] |
| check_3_fabricated_index | Every cited index <= len(retrieved) | YES | n_retrieved=3; all_cited_indices=[1] |
| check_4_url_allowlist | Every URL matches /blog/ regex | YES | checked_urls=['https://www.xicteksystems.com/blog/software-development-cost-pakistan'] |
| check_5_verbatim_quotes | Every "..."[n] quote found in article body | YES | — |

**Warnings:**
- CHECK 5 — no verbatim quotes detected in body (informational; not a failure).

---

## T2 — Multi-source synthesis — top-2 scores likely trigger synthesis

**Type:** positive
**Query:** `custom software development guide`
**Timestamp:** 2026-11-12T06:48:13.209726Z

### Retrieved Articles

| # | Slug | Title | Score | Published |
|---|---|---|---|---|
| 1 | `custom-software-development-guide` | Custom Software Development Guide for Growing Businesses | 0.5052 | 2026-09-07 |
| 2 | `custom-software-development` | Custom Software Development: When Bespoke Software Makes Sense | 0.4309 | 2026-09-07 |
| 3 | `software-development-process` | The Software Development Process: A Practical Guide | 0.3126 | 2026-09-07 |

### Response

```
Based on the Custom Software Development Guide for Growing Businesses article [1], the key considerations for your question are covered in the article's discussion of this topic. The article emphasizes starting with a clear business outcome before making technical decisions [1].

**Sources:**
[1] Custom Software Development Guide for Growing Businesses — https://www.xicteksystems.com/blog/custom-software-development-guide

```

### Validation Report

**Overall:** PASS

| Check | Rule | Passed | Details |
|---|---|---|---|
| check_1_orphan_markers | Every [n] in body has a Sources entry | YES | markers_in_body=[1]; source_indices=[1] |
| check_2_padded_sources | Every Sources entry has a [n] in body | YES | source_indices=[1]; markers_in_body=[1] |
| check_3_fabricated_index | Every cited index <= len(retrieved) | YES | n_retrieved=3; all_cited_indices=[1] |
| check_4_url_allowlist | Every URL matches /blog/ regex | YES | checked_urls=['https://www.xicteksystems.com/blog/custom-software-development-guide'] |
| check_5_verbatim_quotes | Every "..."[n] quote found in article body | YES | — |

**Warnings:**
- CHECK 5 — no verbatim quotes detected in body (informational; not a failure).

---

## T3 — Normal citation — agile process article

**Type:** positive
**Query:** `what is the agile software development process`
**Timestamp:** 2026-11-12T06:48:15.996968Z

### Retrieved Articles

| # | Slug | Title | Score | Published |
|---|---|---|---|---|
| 1 | `agile-software-development` | Agile Software Development Without Losing Direction | 0.429 | 2026-09-07 |
| 2 | `software-development-process` | The Software Development Process: A Practical Guide | 0.363 | 2026-09-07 |
| 3 | `software-development-company-pakistan` | How to Choose a Software Development Company in Pakistan | 0.2555 | 2026-09-07 |

### Response

```
Based on the Agile Software Development Without Losing Direction article [1], the key considerations for your question are covered in the article's discussion of this topic. The article emphasizes starting with a clear business outcome before making technical decisions [1].

**Sources:**
[1] Agile Software Development Without Losing Direction — https://www.xicteksystems.com/blog/agile-software-development

```

### Validation Report

**Overall:** PASS

| Check | Rule | Passed | Details |
|---|---|---|---|
| check_1_orphan_markers | Every [n] in body has a Sources entry | YES | markers_in_body=[1]; source_indices=[1] |
| check_2_padded_sources | Every Sources entry has a [n] in body | YES | source_indices=[1]; markers_in_body=[1] |
| check_3_fabricated_index | Every cited index <= len(retrieved) | YES | n_retrieved=3; all_cited_indices=[1] |
| check_4_url_allowlist | Every URL matches /blog/ regex | YES | checked_urls=['https://www.xicteksystems.com/blog/agile-software-development'] |
| check_5_verbatim_quotes | Every "..."[n] quote found in article body | YES | — |

**Warnings:**
- CHECK 5 — no verbatim quotes detected in body (informational; not a failure).

---

## T4 — Normal citation — chatbot article

**Type:** positive
**Query:** `tell me about ai chatbot development`
**Timestamp:** 2026-11-12T06:48:18.698922Z

### Retrieved Articles

| # | Slug | Title | Score | Published |
|---|---|---|---|---|
| 1 | `ai-chatbot-development` | AI Chatbot Development for Useful Customer Conversations | 0.419 | 2026-09-07 |
| 2 | `ai-development-company-pakistan` | What to Expect from an AI Development Company in Pakistan | 0.2912 | 2026-09-07 |
| 3 | `future-of-ai-in-business` | The Future of AI in Business: Preparing for Useful Change | 0.2124 | 2026-09-07 |

### Response

```
Based on the AI Chatbot Development for Useful Customer Conversations article [1], the key considerations for your question are covered in the article's discussion of this topic. The article emphasizes starting with a clear business outcome before making technical decisions [1].

**Sources:**
[1] AI Chatbot Development for Useful Customer Conversations — https://www.xicteksystems.com/blog/ai-chatbot-development

```

### Validation Report

**Overall:** PASS

| Check | Rule | Passed | Details |
|---|---|---|---|
| check_1_orphan_markers | Every [n] in body has a Sources entry | YES | markers_in_body=[1]; source_indices=[1] |
| check_2_padded_sources | Every Sources entry has a [n] in body | YES | source_indices=[1]; markers_in_body=[1] |
| check_3_fabricated_index | Every cited index <= len(retrieved) | YES | n_retrieved=3; all_cited_indices=[1] |
| check_4_url_allowlist | Every URL matches /blog/ regex | YES | checked_urls=['https://www.xicteksystems.com/blog/ai-chatbot-development'] |
| check_5_verbatim_quotes | Every "..."[n] quote found in article body | YES | — |

**Warnings:**
- CHECK 5 — no verbatim quotes detected in body (informational; not a failure).

---

## T5 — Normal citation — PWA article

**Type:** positive
**Query:** `explain progressive web apps`
**Timestamp:** 2026-11-12T06:48:21.371539Z

### Retrieved Articles

| # | Slug | Title | Score | Published |
|---|---|---|---|---|
| 1 | `progressive-web-apps` | Progressive Web Apps: When the Browser Can Be the Product | 0.4114 | 2026-09-07 |
| 2 | `ai-development-company-pakistan` | What to Expect from an AI Development Company in Pakistan | 0.2371 | 2026-09-07 |
| 3 | `generative-ai-applications` | Generative AI Applications for Real Business Workflows | 0.23 | 2026-09-07 |

### Response

```
Based on the Progressive Web Apps: When the Browser Can Be the Product article [1], the key considerations for your question are covered in the article's discussion of this topic. The article emphasizes starting with a clear business outcome before making technical decisions [1].

**Sources:**
[1] Progressive Web Apps: When the Browser Can Be the Product — https://www.xicteksystems.com/blog/progressive-web-apps

```

### Validation Report

**Overall:** PASS

| Check | Rule | Passed | Details |
|---|---|---|---|
| check_1_orphan_markers | Every [n] in body has a Sources entry | YES | markers_in_body=[1]; source_indices=[1] |
| check_2_padded_sources | Every Sources entry has a [n] in body | YES | source_indices=[1]; markers_in_body=[1] |
| check_3_fabricated_index | Every cited index <= len(retrieved) | YES | n_retrieved=3; all_cited_indices=[1] |
| check_4_url_allowlist | Every URL matches /blog/ regex | YES | checked_urls=['https://www.xicteksystems.com/blog/progressive-web-apps'] |
| check_5_verbatim_quotes | Every "..."[n] quote found in article body | YES | — |

**Warnings:**
- CHECK 5 — no verbatim quotes detected in body (informational; not a failure).

---

## T6 — Out-of-domain — should trigger Fallback 5.2 (deflect to /services)

**Type:** positive
**Query:** `how much do you charge for software development services`
**Timestamp:** 2026-11-12T06:48:21.371623Z

### Retrieved Articles

_(none — fallback triggered before retrieval)_

**Fallbacks triggered:** 5.2_OUT_OF_DOMAIN

### Response

```
That question is best answered on our [Services](https://www.xicteksystems.com/services) or [Contact](https://www.xicteksystems.com/contact) page rather than in the blog. I'd suggest starting there — or if you'd like, I can answer a related question from our blog articles.
```

### Validation Report

**Overall:** PASS

| Check | Rule | Passed | Details |
|---|---|---|---|
| check_1_orphan_markers | Every [n] in body has a Sources entry | YES | — |
| check_2_padded_sources | Every Sources entry has a [n] in body | YES | — |
| check_3_fabricated_index | Every cited index <= len(retrieved) | YES | — |
| check_4_url_allowlist | Every URL matches /blog/ regex | YES | — |
| check_5_verbatim_quotes | Every "..."[n] quote found in article body | YES | — |

**Warnings:**
- CHECK 5 — no verbatim quotes detected in body (informational; not a failure).

---

## T7 — Off-topic — should trigger Fallback 5.1 (no source above threshold)

**Type:** positive
**Query:** `best recipe for chicken biryani`
**Timestamp:** 2026-11-12T06:48:24.018081Z

### Retrieved Articles

_(none — fallback triggered before retrieval)_

**Fallbacks triggered:** 5.1_NO_SOURCE

### Response

```
I don't have a blog article that addresses that. For specific questions, please contact XICTEK Systems at xicteksystems@gmail.com or visit [/contact](https://www.xicteksystems.com/contact).
```

### Validation Report

**Overall:** PASS

| Check | Rule | Passed | Details |
|---|---|---|---|
| check_1_orphan_markers | Every [n] in body has a Sources entry | YES | — |
| check_2_padded_sources | Every Sources entry has a [n] in body | YES | — |
| check_3_fabricated_index | Every cited index <= len(retrieved) | YES | — |
| check_4_url_allowlist | Every URL matches /blog/ regex | YES | — |
| check_5_verbatim_quotes | Every "..."[n] quote found in article body | YES | — |

**Warnings:**
- CHECK 5 — no verbatim quotes detected in body (informational; not a failure).

---

## T8 — NEGATIVE CONTROL — orphan marker [3] in body with no Sources entry

**Type:** negative_control
**Query:** `custom software development cost`
**Timestamp:** 2026-11-12T06:48:24.018193Z

### Retrieved Articles

| # | Slug | Title | Score | Published |
|---|---|---|---|---|
| 1 | `custom-software-development-guide` | Custom Software Development Guide | — | — |
| 2 | `software-development-cost-pakistan` | Software Development Cost in Pakistan | — | — |

### Response

```
Custom software development cost depends on scope and complexity [1]. The article also mentions team composition as a factor [3].

**Sources:**
[1] Custom Software Development Guide — https://www.xicteksystems.com/blog/custom-software-development-guide

```

### Validation Report

**Overall:** FAIL

| Check | Rule | Passed | Details |
|---|---|---|---|
| check_1_orphan_markers | Every [n] in body has a Sources entry | NO | markers_in_body=[1, 3]; source_indices=[1]; orphan_markers=[3] |
| check_2_padded_sources | Every Sources entry has a [n] in body | YES | source_indices=[1]; markers_in_body=[1, 3] |
| check_3_fabricated_index | Every cited index <= len(retrieved) | NO | n_retrieved=2; all_cited_indices=[1, 3]; fabricated_indices=[3] |
| check_4_url_allowlist | Every URL matches /blog/ regex | YES | checked_urls=['https://www.xicteksystems.com/blog/custom-software-development-guide'] |
| check_5_verbatim_quotes | Every "..."[n] quote found in article body | YES | — |

**Errors:**
- CHECK 1 FAIL — markers [3] appear in body but have no Sources entry (orphan citations).
- CHECK 3 FAIL — indices [3] are cited but only 2 articles were retrieved (fabricated citations).

**Warnings:**
- CHECK 5 — no verbatim quotes detected in body (informational; not a failure).

---

## T9 — NEGATIVE CONTROL — padded Sources entry [2] never cited in body

**Type:** negative_control
**Query:** `custom software development cost`
**Timestamp:** 2026-11-12T06:48:24.018263Z

### Retrieved Articles

| # | Slug | Title | Score | Published |
|---|---|---|---|---|
| 1 | `custom-software-development-guide` | Custom Software Development Guide | — | — |
| 2 | `software-development-cost-pakistan` | Software Development Cost in Pakistan | — | — |

### Response

```
Custom software development cost depends on scope and complexity [1].

**Sources:**
[1] Custom Software Development Guide — https://www.xicteksystems.com/blog/custom-software-development-guide
[2] Software Development Cost in Pakistan — https://www.xicteksystems.com/blog/software-development-cost-pakistan

```

### Validation Report

**Overall:** FAIL

| Check | Rule | Passed | Details |
|---|---|---|---|
| check_1_orphan_markers | Every [n] in body has a Sources entry | YES | markers_in_body=[1]; source_indices=[1, 2] |
| check_2_padded_sources | Every Sources entry has a [n] in body | NO | source_indices=[1, 2]; markers_in_body=[1]; padded_sources=[2] |
| check_3_fabricated_index | Every cited index <= len(retrieved) | YES | n_retrieved=2; all_cited_indices=[1, 2] |
| check_4_url_allowlist | Every URL matches /blog/ regex | YES | checked_urls=['https://www.xicteksystems.com/blog/custom-software-development-guide', 'https://www.xicteksystems.com/... |
| check_5_verbatim_quotes | Every "..."[n] quote found in article body | YES | — |

**Errors:**
- CHECK 2 FAIL — Sources entries [2] are listed but never cited in body (padding the Sources list).

**Warnings:**
- CHECK 5 — no verbatim quotes detected in body (informational; not a failure).

---

## T10 — NEGATIVE CONTROL — non-blog URL in Sources (scope violation)

**Type:** negative_control
**Query:** `tell me about hisabdo expense management app`
**Timestamp:** 2026-11-12T06:48:24.018307Z

### Retrieved Articles

| # | Slug | Title | Score | Published |
|---|---|---|---|---|
| 1 | `hisabdo-features` | Hisabdo Features | — | — |

### Response

```
Hisabdo is an expense management application [1].

**Sources:**
[1] Hisabdo Features — https://hisabdo.app/features

```

### Validation Report

**Overall:** FAIL

| Check | Rule | Passed | Details |
|---|---|---|---|
| check_1_orphan_markers | Every [n] in body has a Sources entry | YES | markers_in_body=[1]; source_indices=[1] |
| check_2_padded_sources | Every Sources entry has a [n] in body | YES | source_indices=[1]; markers_in_body=[1] |
| check_3_fabricated_index | Every cited index <= len(retrieved) | YES | n_retrieved=1; all_cited_indices=[1] |
| check_4_url_allowlist | Every URL matches /blog/ regex | NO | checked_urls=['https://hisabdo.app/features']; violations=[{'index': 1, 'url': 'https://hisabdo.app/features', 'reaso... |
| check_5_verbatim_quotes | Every "..."[n] quote found in article body | YES | — |

**Errors:**
- CHECK 4 FAIL — 1 URL(s) failed the blog allowlist: [{'index': 1, 'url': 'https://hisabdo.app/features', 'reason': 'not on /blog/ allowlist'}]

**Warnings:**
- CHECK 5 — no verbatim quotes detected in body (informational; not a failure).

---

## Final Result

- Positive cases passed: **7/7**
- Negative controls correctly failed: **3/3**
- Overall verdict: **PASS**
