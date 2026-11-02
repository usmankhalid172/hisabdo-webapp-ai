# Portfolio Security & Boundary Test Log

**Owner:** Muhammad Mohsin
**Task:** Safety & Domain Boundaries — Portfolio & Case Studies
**Execution date:** 2026-11-02

## Findings

- The reviewed public portfolio material describes HisabDo and contains no client-named private case-study records. No confirmed disclosure of private client material was found in the reviewed source content.
- Portfolio source filtering previously used raw string-prefix matching. That could accept a lookalike path such as `/portfolio-archive` or `/portfolio.evil`. Matching now validates the parsed scheme, host, port, and normalized path boundary; foreign hosts, malformed URLs, credential-bearing URLs, non-HTTPS URLs, and path traversal are excluded.
- Conversation history is supplied by the website client and can contain fabricated assistant turns or old instruction overrides. Portfolio/case-study generations now omit that untrusted history and rely on the current question plus retrieved portfolio context.
- Retrieved passages are now explicitly treated as untrusted data rather than instructions. Case-study answers are limited to details explicitly presented as public in portfolio context; confidential or uncertain details must be omitted.
- Instruction-override attempts in the current message are refused before retrieval/provider invocation. The existing deterministic guardrail remains heuristic; this test run does not establish resistance to every paraphrase or measure a live model's behavior.

## Boundary coverage

| Boundary | Test evidence |
|---|---|
| Portfolio queries retrieve portfolio facts and cite the retrieved portfolio source | `test_portfolio_answer_uses_only_portfolio_retrieval_and_cites_it` |
| Missing evidence does not call the model or create citations for unsupported client outcomes | `test_missing_retrieval_returns_no_answer_without_calling_llm` |
| Portfolio source matching allows the exact route and child paths while excluding unrelated sources | `test_query_can_restrict_candidates_to_a_source_prefix` |
| Spoofed/out-of-scope sources are excluded: foreign host, foreign subdomain, prefix lookalikes, traversal, credentials, HTTP, malformed URL | `test_query_rejects_spoofed_or_out_of_scope_portfolio_sources` |
| Client-supplied prior turns, including fabricated private metrics and override text, are not passed into portfolio generation | `test_portfolio_answer_uses_only_portfolio_retrieval_and_cites_it` |
| Current-message instruction override is refused before retrieval or LLM use | `test_instruction_override_is_refused_before_retrieval_or_llm` |
| System prompt marks retrieved text as untrusted and limits case-study claims to public portfolio facts | `test_system_prompt_treats_retrieved_text_as_untrusted_and_limits_case_studies` |
| Common override/extraction patterns are covered by the deterministic guardrail suite | `test_guardrails.py` |

## Execution log

From `hisabdo-webapp-ai`, on 2026-11-02:

```text
python -m pytest tests\xictek_website_assistant\test_vector_store.py tests\xictek_website_assistant\test_grounded_portfolio.py tests\xictek_website_assistant\test_guardrails.py -q
49 passed, 1 warning in 0.23s

python -m pytest tests\xictek_website_assistant -q
122 passed, 2 warnings in 0.98s
```

The test environment initially lacked declared dependencies (`joblib`, `numpy`, `scikit-learn`, `pandas`, and `beautifulsoup4`). The missing packages were installed at their versions specified in `requirements.txt`; no dependency manifest was changed. The warnings are Starlette deprecations, not test failures.

## Evidence limits

- These are automated tests with a mocked provider, not a live LLM or production-index evaluation.
- The prior retrieval evaluation reports an empty checked-in `data/index/chunks.json`; the test fixtures validate source filtering but do not prove that a deployed/rebuilt index contains only authorized public material.
- Before release, rebuild the index from approved public sources and audit the resulting portfolio chunks for private client details. Confirm the production source allowlist and deployed index contents separately.
