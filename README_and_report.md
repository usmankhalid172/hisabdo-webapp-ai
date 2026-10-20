# Blog Section Security & Link Regression — Submission

**Owner:** 6. Muhammad Daniyal  
**Task:** Run automated checks across Blog Section outputs to ensure injected URLs use HTTPS, paths are valid, and security headers have not been compromised.

## What is Included

This submission contains the automated validator, repeatable regression tests, real chatbot outputs captured from the live XICTEK Blog chatbot, and reports generated from live verification.

### Files

- `blog_security_link_regression.py` — automated URL, reachability, redirect, and security-header validator.
- `test_blog_security_link_regression.py` — repeatable offline unit/regression tests for the validator logic.
- `blog_outputs.jsonl` — five real Blog chatbot query/response pairs captured from the live website.
- `live_chatbot_output_report.json` — live verification report for URLs extracted from the captured chatbot responses.
- `live_blog_security_report.json` — live verification report for the XICTEK Blog page and discovered Blog links.
- `README_and_report.md` — this documentation and explanation of the test results.

## Test Approach

The validator uses three levels of testing:

1. **Offline regression testing** — verifies the validator's logic using controlled HTTP responses.
2. **Captured chatbot-output testing** — scans real chatbot responses for injected source URLs.
3. **Live network verification** — makes real HTTP requests to the XICTEK Blog and URLs extracted from the chatbot responses.

The offline tests are intentionally retained because they provide deterministic and repeatable regression coverage. They are not treated as evidence that the production website is healthy.

## Real Chatbot Output Audit

The `blog_outputs.jsonl` file contains five actual chatbot query/response pairs captured from the live XICTEK Blog chatbot.

The validator extracts URLs from those responses and checks whether they satisfy the Blog-section security and scope rules.

### Live chatbot-output command

```powershell
python blog_security_link_regression.py blog_outputs.jsonl --report live_chatbot_output_report.json
```

The live test performs network verification for the URLs found in the captured responses, including:

- HTTPS validation
- Approved XICTEK host validation
- `/blog` path validation
- HTTP status checking
- Redirect checking
- Verification that redirect destinations remain inside the approved Blog section

### Live chatbot-output result

The live verification produced:

**10 passed, 3 failed, 0 warnings**

The three failures were correctly detected as out-of-scope source URLs:

1. `https://xicteksystems.com/services/custom-software-development`  
   — HTTPS and XICTEK host are valid, but the path is outside `/blog`.

2. `https://hisabdo.app/blog`  
   — host is outside the approved XICTEK domain.

3. `https://hisabdo.app/blog/pdf-reports-for-businesses`  
   — host is outside the approved XICTEK domain.

These failures are retained as regression findings. They demonstrate that the validator can detect incorrect or unsafe source injection rather than silently accepting every URL returned by the chatbot.

## Live Blog Discovery and Link Regression

The validator can also inspect the live XICTEK Blog landing page and automatically discover Blog links.

### Command

```powershell
python blog_security_link_regression.py --discover-blog --report live_blog_security_report.json
```

This performs live checks against:

```text
https://www.xicteksystems.com/blog
```

The validator:

- fetches the live Blog page;
- discovers Blog links from the page HTML;
- checks the discovered URLs;
- verifies HTTP status codes;
- follows redirects;
- verifies that redirect destinations remain within the approved Blog section;
- checks the Blog page's security headers.

### Live Blog result

The live Blog scan produced:

**50 passed, 4 failed, 1 warning**

The validator successfully discovered **48 approved Blog links** and verified their reachability.

The security-header checks also identified four missing protections:

- `X-Content-Type-Options` — **missing**
- `Content-Security-Policy` — **missing**
- `Referrer-Policy` — **missing**
- Clickjacking protection through CSP `frame-ancestors` or `X-Frame-Options` — **missing**

The following was present:

- `Strict-Transport-Security` — **PASS**

`Permissions-Policy` was not present and was reported as an informational warning.

These results are reported as findings rather than being modified or hidden.

## Security Checks

The validator checks the following security properties:

### URL Security

- URL must use HTTPS.
- URL must use an approved XICTEK host.
- URL must point to the approved `/blog` section.
- Path traversal attempts are rejected.
- Encoded path separators are checked.
- URLs containing embedded credentials are rejected.
- Unexpected ports are rejected.

### Link Reachability

- HTTP status codes are checked.
- Broken links are detected.
- Redirects are followed.
- Redirect destinations must remain inside the approved Blog section.

### Security Headers

The validator checks:

- `Strict-Transport-Security`
- `X-Content-Type-Options`
- `Content-Security-Policy`
- `Referrer-Policy`
- Clickjacking protection through CSP `frame-ancestors` or `X-Frame-Options`
- `Permissions-Policy` as an informational warning when absent

## Offline Regression Tests

The included regression suite provides deterministic tests for the validator logic.

Run:

```powershell
python -m pip install pytest
python -m pytest -q test_blog_security_link_regression.py
```

Current result:

```text
15 passed in 0.11s
```

These tests use controlled/mock HTTP responses. They verify that the validator correctly handles expected PASS and FAIL cases without depending on network availability.

They are **not** presented as proof that the production XICTEK website is healthy.

## Live Verification Evidence

The live reports were generated from a machine with outbound internet/DNS access.

The following files contain the resulting evidence:

```text
live_chatbot_output_report.json
live_blog_security_report.json
```

The live reports should be preserved with the submission because they demonstrate that the validator was executed against the actual XICTEK Blog and real chatbot-generated source URLs.

## Conclusion

The automated regression validator successfully verifies Blog-section URL security, path restrictions, link reachability, redirect behavior, and security-header configuration.

The live regression run successfully detected:

- out-of-scope source URLs returned by the chatbot;
- missing security headers on the live Blog page;
- valid HTTPS Blog URLs;
- reachable Blog pages;
- redirects that remain within the approved Blog section.

The detected failures are intentionally retained in the reports because a security and regression test should **identify existing problems rather than hide them**.

This submission therefore provides both repeatable offline regression coverage and live verification evidence for the Blog Section Security & Link Regression task.