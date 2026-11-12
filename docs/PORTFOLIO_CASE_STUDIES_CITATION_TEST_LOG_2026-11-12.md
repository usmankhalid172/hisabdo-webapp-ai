# Portfolio & Case Studies Citation Test Log

**Date:** 12 November 2026  
**Scope:** Portfolio source isolation, grounded generation, and inline source attribution

## Automated checks added

`tests/xictek_website_assistant/test_portfolio_grounding.py` adds five focused cases:

| Check | Expected behavior | Execution status |
|---|---|---|
| Portfolio intent detection | Portfolio and HisabDo case-study questions use the Portfolio route; career questions do not | Blocked before collection |
| Source filtering | Only `xicteksystems.com/portfolio` chunks are eligible | Blocked before collection |
| Valid inline citation | Exact retrieved title and URL are accepted and returned in `sources` | Blocked before collection |
| Unsupported claim / wrong citation | An unverified metric and unrelated source link are replaced with a fallback | Blocked before collection |
| Empty retrieval | No LLM call; response points to the official Portfolio page | Blocked before collection |

Additional checks completed: Python syntax compilation passed for the changed service, query helper, prompt module, and new test module. A standalone intent smoke check passed for 3 cases (two Portfolio questions routed; one Careers question excluded). The checked-in vector index contains 10 Portfolio chunks, all titled `Our Work | XICTEK Systems` and attributed to `https://xicteksystems.com/portfolio`.

## Test execution

Command attempted:

```powershell
python -m pytest tests/xictek_website_assistant/test_portfolio_grounding.py -q
```

Result: **Not executed; environment dependency failure.** Pytest loading the repository's `tests/conftest.py` stopped because `slowapi` is missing. Retrying with the conftest excluded stopped during test-module import because `pydantic_settings` is missing. No test pass is claimed. The project `requirements.txt` lists both dependencies (`slowapi==0.1.9` and `pydantic-settings==2.5.2`).

## Manual source verification

The public [Our Work | XICTEK Systems](https://www.xicteksystems.com/portfolio) page was inspected on 12 November 2026. It explicitly states the HisabDo overview, challenge, approach, qualitative outcome, listed technology stack (Flutter, Supabase, PostgreSQL), and product screenshot descriptions. The page does not state client names beyond HisabDo, measurable business results, timelines, or before-and-after metrics. Those details are marked unsupported in the verified Q&A examples.

## Release status

The implementation and test cases are prepared. Runtime acceptance remains **pending** until the repository dependencies are installed in the project environment and the focused command above completes successfully. Do not treat this record as a passing test report or release sign-off.
