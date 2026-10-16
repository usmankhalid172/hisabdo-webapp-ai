# Task 6 — Source Injection Automated Audit

**Member:** Muhammad Daniyal  
**Task:** `[Source Injection Automated Audit]` Write a Python validation script to automatically check if generated responses for Blog Section test queries properly contain active, valid source links at the end.

## Implementation

Added:

- `scripts/source_injection_audit.py`
- `tests/test_source_injection_audit.py`

The repository already separates application code, tests, data, and scripts, so the audit is implemented as a standalone script plus focused automated tests. The repository README explicitly lists testing/evaluation as an AI/ML workstream and instructs contributors to work from a feature branch rather than directly on `main`. 

## What the audit checks

For every generated Blog response, the validator checks:

1. The response is not empty.
2. A final `Sources`, `Source Links`, or `References` section exists.
3. At least one HTTP/HTTPS source URL is present in that section.
4. Source links are the final meaningful content of the response.
5. URLs have valid HTTP(S) syntax.
6. Every source URL is active/reachable using HTTP `HEAD`, with `GET` fallback for servers that do not support `HEAD`.
7. HTTP success and redirect responses (`200–399`) are accepted as active.
8. An optional `--source-prefix` can restrict sources to the official Blog URL space.

## Input

The script accepts JSON or CSV.

JSON list example:

```json
[
  {
    "test_id": "BLOG-01",
    "response": "Answer text.\n\n## Sources\n- [Article](https://xicteksystems.com/blog/example/)"
  }
]
```

CSV should contain a `test_id` column and one of these response columns:

`response`, `generated_response`, `actual_response`, or `answer`.

## Usage

From the repository root:

```bash
python scripts/source_injection_audit.py responses.json
```

For the XICTEK Blog source space:

```bash
python scripts/source_injection_audit.py responses.json   --source-prefix https://xicteksystems.com/blog/   --json-report source_audit_report.json
```

For offline syntax/presence validation:

```bash
python scripts/source_injection_audit.py responses.json --no-network
```

Run the automated tests:

```bash
pytest tests/test_source_injection_audit.py
```

## Expected audit behavior

A valid generated answer should end in a source section similar to:

```text
Answer to the user's Blog question.

## Sources
- [Relevant article](https://xicteksystems.com/blog/example/)
```

The audit fails responses where:

- the source section is missing;
- no source link is present;
- a source URL is malformed;
- a source URL is outside the configured Blog prefix;
- a source URL returns an error;
- additional generated prose appears after the final source link.

## Design notes

The implementation uses only Python standard-library modules, so no additional dependency is required. Network checks are intentionally performed at runtime because an URL can be syntactically correct while being unavailable.

The audit produces both human-readable console output and an optional JSON report suitable for CI/evaluation evidence.

## Repository alignment

The public repository contains `src/`, `tests/`, `data/`, `research/`, and `scripts/`, and its README describes testing/evaluation as part of the project workstreams. The audit therefore belongs naturally under `scripts/`, with its regression tests under `tests/`. 

## Submission

Recommended files for this task only:

- `scripts/source_injection_audit.py`
- `tests/test_source_injection_audit.py`
- `docs/source_injection_audit_report.md`

No application files are modified by this task.
