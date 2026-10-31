# Intent Router

## Overview
The intent router identifies the purpose of a user's message and assigns it to an intent category. It uses keyword-based rules written in Python.

## Supported Intents
- `customer_balance` — Questions about money customers owe.
- `payable` — Questions about money owed to suppliers.
- `cash_flow` — Questions about business cash flow.
- `report` — General financial report requests.
- `income` — Money received by the business.
- `expense` — Money spent by the business.
- `correction` — Requests to correct or update information.
- `categorization` — Questions about transaction categories.
- `general_faq` — General help and information questions.
- `unknown` — Questions that do not match the defined rules.

## Files
- `intent_router.py` — Contains the intent recognition logic.
- `test_intent_router.py` — Contains automated unit tests.

## Run the Intent Router
```bash
python intent_router.py
```

## Run Automated Tests
```bash
python -m unittest test_intent_router.py -v
```

## Test Results
Eight automated tests passed during testing.

## Limitation
This router uses keyword matching rather than a machine-learning model. Some differently worded questions may be classified incorrectly, so additional rules and tests may be needed.
