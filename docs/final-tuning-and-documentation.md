# Final Tuning and Documentation

## Fix Applied
Updated `src/xictek_website_assistant/vector_store.py` to read
`metadata.json` and `chunks.json` explicitly with UTF-8 encoding.
This fixes the Windows Unicode decoding issue encountered while loading
the persisted vector-store index.

## Verification
Full test suite:
- Command: `python -m pytest -q`
- Result: 329 passed, 4 skipped, 4 warnings
- Runtime: 7.78 seconds

Targeted endpoint test:
- Result: 1 passed, 2 warnings

## Warnings Observed
- Scikit-learn warned that saved TF-IDF objects were created with version
  1.5.2 while version 1.7.2 is installed.
- Starlette reported a deprecation warning for
  `HTTP_422_UNPROCESSABLE_ENTITY`.

## Submission Status
The tests passed after the UTF-8 fix. Code and documentation still need
a final review before commit and push.
