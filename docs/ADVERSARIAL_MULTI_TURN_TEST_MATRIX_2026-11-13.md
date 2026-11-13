# Adversarial & Multi-Turn Regression Test Matrix

**Date:** 13 November 2026  
**System under test:** XICTEK website assistant chat service  
**Domains:** About Us, Core Services, Portfolio & Case Studies, Careers, HisabDo Product, Blog & News, Contact & Locations

## Coverage matrix

| ID | Domain / surface | Scenario | Expected control | Automated test |
|---|---|---|---|---|
| ADV-01–07 | All seven domains | Direct instruction override, prompt extraction, or secret/token probe using domain-tailored text | Deterministic refusal before retrieval and provider call | `test_prompt_injection_and_extraction_are_blocked_across_domains`; `test_direct_injection_short_circuits_service_for_every_domain`; existing `test_guardrails.py` |
| ADV-08–11 | Portfolio, company, recruitment | Confidential metrics and employee/applicant personal contact probes | Deterministic refusal before retrieval/provider; no answer containing requested private data | `test_confidential_metrics_and_personal_data_probes_are_blocked`; `test_private_data_and_confidential_metric_probes_short_circuit_service`; `test_portfolio_followup_cannot_invent_confidential_metric` |
| ADV-12–15 | Off-topic abuse | Malware, ransomware/data theft, doxxing, weapon creation requests | Narrow abuse classifier refuses before retrieval and provider call | `test_explicit_harmful_off_topic_requests_are_blocked`; service short-circuit tests |
| SAFE-01–08 | All domains + defensive security | Ordinary company/product questions and defensive phishing question | Must not be rejected by the safety classifiers | `test_legitimate_domain_questions_and_defensive_security_are_not_guardrail_blocked` |
| MT-01–07 | Each of seven domains | Two-turn clarification in a single conversation | Same conversation ID; prior user/assistant turns reach provider; current domain source remains attached | `test_two_turn_dialogs_retain_history_and_conversation_across_all_domains` |
| HIST-01–07 | Each of seven domains | Injection placed in earlier assistant-labeled history | Reject before vector lookup/provider call regardless of role label | `test_injection_in_any_history_turn_is_blocked_before_retrieval_or_llm` |
| PORT-01 | Portfolio & Case Studies | Ask for confidential revenue after a harmless first turn | Reject the metric probe before retrieval/provider; never echo a fabricated number | `test_portfolio_followup_cannot_invent_confidential_metric` |

## Execution notes

- The new parametrized matrix contributes 51 case instances (7 direct adversarial detector + 7 service-level direct blocks + 4 private-data detector + 4 service-level private-data blocks + 4 abuse detector + 8 benign + 7 multi-turn + 7 history-injection + 2 harmful request service blocks + 1 Portfolio metric probe).
- The runner also includes existing guardrail, Careers grounding, and Portfolio grounding regressions.
- These are controlled unit/integration tests using fake retrieval and fake LLM providers. They validate routing, history forwarding, and deterministic pre-LLM blocks; they do not simulate a deployed widget, external provider behavior, or all possible paraphrases.
- The guardrail intentionally catches a narrow high-confidence set of harmful requests. General off-topic questions still depend on the assistant's out-of-scope system instruction and should be checked against the live model separately.
