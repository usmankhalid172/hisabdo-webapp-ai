# Careers & Job Openings Workflow Deployment Guide

This guide covers source-backed careers answers, action-oriented prompt templates, application-link verification, and release checks for the XICTEK website assistant. The assistant's standard index build and service deployment steps remain in the [website assistant README](../src/xictek_website_assistant/README.md).

## Verified public routes

Checked **2026-10-21** by following redirects and inspecting page links. HTTP 200 confirms a page was reachable at check time; it does not establish that a role is open, that a submission was received, or that an email will be delivered.

| Organization / route | Check result | Permitted description |
|---|---|---|
| [XICTEK Careers](https://www.xicteksystems.com/careers) | HTTP 200. Its visible “Apply Now” links point to `/contact`. | Careers information page; verify current roles and requirements from the live page before answering. |
| [XICTEK Internship](https://www.xicteksystems.com/careers/internship) | HTTP 200. | Internship information page; not itself a role-specific application form. |
| [XICTEK Contact](https://www.xicteksystems.com/contact) | HTTP 200; destination of the careers page’s “Apply Now” links. | General contact page only. Do not call it a job portal, application form, or completed application route. |
| [HisabDo Careers](https://hisabdo.app/careers) | HTTP 200. The page displayed “Currently Unavailable” and included an “Ask About Opportunities” link to `mailto:hisabdo.app@gmail.com?subject=Internship%20availability`. | Informational/future-opportunity route, not an active application route. Describe availability using the current page wording. |

Recheck the links and page content immediately before each production release and whenever careers content changes. A reachable URL is not proof that its content remains current.

### Email-route approval gate

The assistant prompt and evaluation fixtures currently name `xicteksystems@gmail.com` as a CV-submission fallback. The current public XICTEK careers/contact pages checked above did not expose that address as an application link, and this review did not test email delivery. The earlier [privacy review](../SECURITY-REVIEW.md) also notes that CV handling, retention, deletion, and the email processor are not documented consistently with the published privacy information.

**Do not deploy or repeat the email address as a CV-submission instruction until the responsible owner approves the route and its privacy, access, retention, deletion, and applicant-notice controls.** If it is not approved, update the prompt and related test fixtures to direct applicants only to a verified official page, accurately labeled, and do not ask them to send CVs or other personal information through chat. If approval is granted, verify the exact recipient from an authoritative source and record that verification separately; a syntactically valid `mailto:` URI does not prove delivery or safe handling.

The HisabDo future-opportunity `mailto:` link is present on the checked page, but it is for asking about future availability only. It must never be labeled an application link or used as a route for XICTEK roles.

## Action-oriented answer templates

Use these as response shapes, not as claims about current openings. Fill placeholders only from the current retrieved official source. Keep URL targets exact and link labels truthful.

### A role is listed and a role-specific application URL is supplied

> The current source lists **[role]** and states **[source-backed key requirement/status]**. To apply, use the [official application link]([exact verified URL]). **[Deadline: give the source-stated date/timezone, or say it is not specified.]**

### XICTEK “Apply Now” goes to the general contact page

> The XICTEK careers page lists **[source-backed role/status]**. Its “Apply Now” link goes to the [general contact page](https://www.xicteksystems.com/contact), not a role-specific application form. **[Give only an owner-approved, source-backed next step.]**

Until the email-route approval gate above is cleared, do not add an email-CV instruction to this template.

### HisabDo has no active opportunity

> HisabDo’s careers page currently says **[quote/paraphrase the verified availability wording]**. There is no active application route shown. You can review the [HisabDo careers page](https://hisabdo.app/careers); its “Ask About Opportunities” link is only for checking future availability: [ask about future opportunities](mailto:hisabdo.app@gmail.com?subject=Internship%20availability).

### Eligibility, deadline, or other detail is missing

> The available source says **[known criteria/status]**. It does not specify **[missing item]**, so I can’t confirm that detail. Review the [official careers information]([exact verified source URL]) for updates.

Do not infer eligibility, guarantee acceptance, invent requirements or deadlines, or ask applicants to put personal information into chat. Preserve the visitor’s language and script while leaving URL targets unchanged.

## Release checklist

1. **Refresh source facts.** Review the live official pages for organization, role names, availability, requirements, deadlines, application route, and link labels. Keep XICTEK and HisabDo content separate.
2. **Rebuild the knowledge index.** From the repository root, run `python -m src.xictek_website_assistant.ingest` with outbound HTTPS access. Confirm the generated `data/index/embeddings.npy` and `data/index/chunks.json` contain the latest careers content, then deploy the index and restart the service as described in the [assistant deployment checklist](../src/xictek_website_assistant/README.md).
3. **Review prompt and data-handling approval.** Confirm the email-route gate is cleared before enabling any CV email guidance. Do not solicit applicant PII in chat.
4. **Run the focused prompt tests.** Run `python -m pytest tests/xictek_website_assistant/test_career_guidance.py`. Review any changed tests and fixtures for accuracy; a passing mock-provider test does not establish that generated production answers are grounded.
5. **Run the response evaluation.** Follow the ten scenarios in [careers_job_openings_test_cases.json](../tests/evaluation/careers_job_openings_test_cases.json), replace placeholders only with live verified facts, and record the actual response and evidence in the [evaluation record](../tests/evaluation/careers_job_openings_evaluation.md). All cases must pass with no fabricated links or unsupported claims.
6. **Verify each destination.** Follow redirects for every HTTP(S) target and record the final URL, HTTP status, and check date. Confirm page links and labels manually. For a `mailto:` target, verify the exact address and purpose against the live official page; do not claim email delivery was tested.
7. **Smoke-test the deployed widget.** Confirm career queries receive a concise answer, exact source-backed clickable links, and the appropriate organization/status distinction. Verify the website origin is configured in `XICTEK_WIDGET_ALLOWED_ORIGINS` as required by the assistant deployment checklist.
8. **Hold release on discrepancies.** If a link fails, a page’s status changed, the indexed facts are stale, or privacy approval is unresolved, do not present that route or claim as verified. Refresh the source/index and rerun the affected checks before release.

## Evidence limits

The public-page checks above verify reachability and observed page links on the stated date only. They do not verify that generated production answers pass all ten scenarios, that an application was submitted, or that email is delivered. The evaluation document remains the record for actual assistant responses and must be updated with execution evidence before claiming the response suite passed.
