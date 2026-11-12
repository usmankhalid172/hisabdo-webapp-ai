# Citation Verification & Hallucination Guardrail Pipeline (Muhammad Daniyal)

Drop `src/financial_assistant/guardrails/` into `hisabdo-webapp-ai/src/financial_assistant/`, `config/guardrail_config.json` into the repo, and `tests/` + `docs/` + `reports/` alongside.

```
src/financial_assistant/guardrails/  citation_verifier.py, pipeline.py
config/guardrail_config.json         guardrail settings + system prompt
docs/guardrail_configuration_spec.md Guardrail Configuration Spec
tests/                               edge cases, unittest suite, report generator
reports/edge_case_report.md|json     Automated Edge-Case Test Report
examples/                            CLI demo inputs
```
Run (Python 3.9+, no dependencies):
```
export PYTHONPATH=src
python -m unittest discover -s tests -v          # tests
python tests/run_edge_case_report.py             # regenerate report
python -m financial_assistant.guardrails.citation_verifier --answer examples/answer_bad.txt --chunks examples/chunks.json
```
Note: test chunks are sample fixtures and the LLM is mocked; wire in the real retriever/LLM before production.
