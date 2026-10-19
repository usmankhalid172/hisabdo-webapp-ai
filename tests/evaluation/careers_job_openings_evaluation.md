# Careers & Job Openings: Actionable Response Evaluation

## Purpose

Evaluate whether the XICTEK website assistant answers careers and job-opening
questions with concise, source-grounded next steps and clickable application
routes. The cases are in
[`careers_job_openings_test_cases.json`](careers_job_openings_test_cases.json).
They cover openings, eligibility, application process, deadlines, missing
information, active links, and the distinction between XICTEK Systems and
HisabDo opportunities.

The bracketed values in the test fixtures are placeholders, not claims about
live vacancies. Replace them only with facts and links verified in the current
public source/index. Do not manufacture a job listing or application URL to
complete a test.

## Scoring

Record PASS or FAIL for each applicable dimension:

| Dimension | PASS condition |
|---|---|
| Clarity | Concise response identifies the relevant role/status and answers the question directly. |
| Eligibility | Reports only source-stated qualifications and flags missing criteria as unspecified. |
| Process | Names the next action and any source-stated materials/steps without adding requirements. |
| Deadline | Gives a supplied date/timezone accurately, or says the deadline is not specified. |
| Application link | Provides a clickable exact source-backed application/contact URL, accurately labeled, and the documented XICTEK `mailto:` fallback when no role-specific form or URL is supplied. |
| Grounding | Does not invent openings, eligibility, process details, deadlines, or URLs; keeps XICTEK and HisabDo distinct. |

A case passes only if every `must_pass` check passes and no `must_not` check
occurs. A link and grounding failure are critical: they fail the case regardless
of the other checks. For an HTTP(S) application link, record the tested URL,
date, and response status after following redirects; do not treat a URL as
active based only on its appearance. For `mailto:`, verify that the link target
uses the documented recipient and is a syntactically valid mailto URI.

The suite passes only when all 10 cases pass with no critical link or grounding
failures.

## Evaluation record

| Test ID | Scenario | Result | Evidence / observed response | Link checked (date/status) |
|---|---|---|---|---|
| CAREER-001 | XICTEK openings and application methods | NOT TESTED | Requires a current response grounded in the verified openings fixture. | Careers/contact routes checked below |
| CAREER-002 | Internship eligibility | NOT TESTED | Prompt response not evaluated; verify each qualification against current source. | Contact route checked below |
| CAREER-003 | CV submission and review process | NOT TESTED | Production LLM response not exercised. | Contact and mailto checked below |
| CAREER-004 | Internship duration and next step | NOT TESTED | Production LLM response not exercised. | Contact and mailto checked below |
| CAREER-005 | Deadline not published | NOT TESTED | Requires a current answer and verified application URL fixture. | Recheck at execution |
| CAREER-006 | HisabDo is not hiring | NOT TESTED | Verify current hiring status before executing; response not exercised. | Careers page/mailto checked below |
| CAREER-007 | XICTEK contact route and CV email | NOT TESTED | Production LLM response not exercised. | Contact and mailto checked below |
| CAREER-008 | Past HisabDo bootcamp and organization distinction | NOT TESTED | Verify current status and dates before executing. | Careers page/mailto checked below |
| CAREER-009 | No role-specific application URL | NOT TESTED | Requires a current source with no role-specific route. | Recheck at execution |
| CAREER-010 | Unsupported salary, deadline, or link | NOT TESTED | Production LLM response not exercised. | Contact and mailto checked below |

## Public link checks

Checked on **2026-10-16**. These confirm the link destinations are reachable;
they do not prove that a generated answer included them or that a submission
was accepted.

| Destination | Observed result | Use in evaluation |
|---|---|---|
| `https://www.xicteksystems.com/careers` | HTTP 200; page's "Apply Now" links point to `/contact`. | Verified careers information page; do not label it the submission form. |
| `https://www.xicteksystems.com/careers/internship` | HTTP 200. | Verified internship information page. |
| `https://www.xicteksystems.com/contact` | HTTP 200; reachable from the careers page's "Apply Now" link. | Verified contact destination; label it as the contact page, not a job portal. |
| `https://hisabdo.app/careers` | HTTP 200; page currently includes an "Ask About Opportunities" mailto link. | Information/future-opportunity route only; do not present it as an active application while HisabDo is not hiring. |
| `mailto:xicteksystems@gmail.com` | Valid mailto URI format for the documented XICTEK address; email delivery was not tested. | CV-submission fallback for XICTEK roles, with the role named in the email. |
| `mailto:hisabdo.app@gmail.com?subject=Internship%20availability` | Present on the verified HisabDo careers page; email delivery was not tested. | Ask about future availability, not an application for an open role. |

## Current evaluation status

The repository provides a documented XICTEK CV submission address and role-in-
email instruction. The assistant's career prompt requires direct answers and
context-supported next steps, exact clickable source URLs, and a clickable
`mailto:xicteksystems@gmail.com` fallback for XICTEK roles with no
role-specific route. It distinguishes XICTEK's general contact page from a
direct application form and HisabDo future-opportunity inquiries from active
applications. Targeted prompt tests verify these instructions and that
eligibility, deadline, salary, and position queries receive career guidance.

The repository contains an indexed knowledge base, but the ten response
scenarios remain **NOT TESTED** against an actual generated answer from the
production LLM. The repository's mock provider does not evaluate whether
generated answers satisfy these content and link criteria. Run the cases with
verified current website content, capture each actual response, and recheck
HTTP application links before marking the response evaluation complete.
