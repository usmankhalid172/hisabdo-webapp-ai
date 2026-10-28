# Reranking Experiment

Diagnostic comparison of semantic ranking against simple query-term reranking.

Important: query-term overlap is a lightweight heuristic, not a trained cross-encoder.
Scores are diagnostic only. Ranking position does not prove answer correctness.
Only verified knowledge-base documents are retrieved.

## Overview

Query: What can I do with HisabDo?

- Original 1: `faq-001` — What is HisabDo? (similarity=0.5574)
- Original 2: `faq-khata-guidance` — What is Khata and how is it used? (similarity=0.4563)
- Original 3: `faq-005` — How do I export my expenses? (similarity=0.3157)
- Reranked 1: `faq-001` — What is HisabDo? (term overlap=4)
- Reranked 2: `faq-khata-guidance` — What is Khata and how is it used? (term overlap=4)
- Reranked 3: `faq-udhar-guidance` — How can I understand Udhar or customer balances? (term overlap=4)

## Categorize expense

Query: How do I categorize an expense?

- Original 1: `finance_003` — What is an expense? (similarity=0.7122)
- Original 2: `faq-005` — How do I export my expenses? (similarity=0.4316)
- Original 3: `finance_002` — What is revenue? (similarity=0.3975)
- Reranked 1: `faq-005` — How do I export my expenses? (term overlap=5)
- Reranked 2: `faq-khata-guidance` — What is Khata and how is it used? (term overlap=5)
- Reranked 3: `faq-udhar-guidance` — How can I understand Udhar or customer balances? (term overlap=4)

## Wrong prediction

Query: What if the predicted category is wrong?

- Original 1: `finance_001` — What is profit? (similarity=0.1035)
- Original 2: `finance_008` — Why can a profitable business have cash-flow problems? (similarity=0.0802)
- Original 3: `faq-006` — What's the difference between profit and cash flow? (similarity=0.0313)
- Reranked 1: `faq-006` — What's the difference between profit and cash flow? (term overlap=4)
- Reranked 2: `finance_007` — What is the difference between revenue and profit? (term overlap=4)
- Reranked 3: `finance_001` — What is profit? (term overlap=3)

## PDF report

Query: How do I generate a PDF report in HisabDo?

- Original 1: `faq-005` — How do I export my expenses? (similarity=0.6460)
- Original 2: `faq-001` — What is HisabDo? (similarity=0.5013)
- Original 3: `faq-khata-guidance` — What is Khata and how is it used? (similarity=0.3481)
- Reranked 1: `faq-005` — How do I export my expenses? (term overlap=8)
- Reranked 2: `faq-001` — What is HisabDo? (term overlap=7)
- Reranked 3: `faq-khata-guidance` — What is Khata and how is it used? (term overlap=6)

## Income and expenses

Query: How can I view my total income and expenses in HisabDo?

- Original 1: `faq-005` — How do I export my expenses? (similarity=0.6828)
- Original 2: `faq-001` — What is HisabDo? (similarity=0.4637)
- Original 3: `faq-khata-guidance` — What is Khata and how is it used? (similarity=0.4102)
- Reranked 1: `faq-005` — How do I export my expenses? (term overlap=8)
- Reranked 2: `faq-khata-guidance` — What is Khata and how is it used? (term overlap=6)
- Reranked 3: `faq-udhar-guidance` — How can I understand Udhar or customer balances? (term overlap=6)

## Add customer

Query: How do I add a new customer in HisabDo?

- Original 1: `faq-001` — What is HisabDo? (similarity=0.3901)
- Original 2: `faq-udhar-guidance` — How can I understand Udhar or customer balances? (similarity=0.3590)
- Original 3: `faq-khata-guidance` — What is Khata and how is it used? (similarity=0.3386)
- Reranked 1: `faq-udhar-guidance` — How can I understand Udhar or customer balances? (term overlap=7)
- Reranked 2: `faq-khata-guidance` — What is Khata and how is it used? (term overlap=7)
- Reranked 3: `faq-005` — How do I export my expenses? (term overlap=7)

## Record expense

Query: How do I record a new expense in HisabDo?

- Original 1: `faq-005` — How do I export my expenses? (similarity=0.7085)
- Original 2: `faq-001` — What is HisabDo? (similarity=0.4996)
- Original 3: `finance_003` — What is an expense? (similarity=0.4426)
- Reranked 1: `faq-005` — How do I export my expenses? (term overlap=8)
- Reranked 2: `faq-001` — What is HisabDo? (term overlap=7)
- Reranked 3: `faq-khata-guidance` — What is Khata and how is it used? (term overlap=7)

## Limitations

- This is a heuristic reranking diagnostic, not a trained neural reranker.
- Five workflow queries do not yet have confirmed relevance labels.
- A reranker cannot supply missing verified workflow instructions.
- Do not select a production winner without human relevance judgments and an irrelevant-context check.
