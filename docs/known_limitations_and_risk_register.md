# Known Limitations and Risk Register

## Known Technical Limitations
1. FAQ retrieval uses TF-IDF and cosine similarity. It may miss questions expressed with different vocabulary.
2. The FAQ retriever uses a fixed relevance threshold of 0.12. Its suitability requires evaluation against real test questions.
3. The current FAQ JSON file contains 12 documents. Coverage depends on the content maintained in that file.
4. The recorded result of 21 passed and 1 warning covers the targeted automated test run only. It is not proof that all application behaviour has passed QA.
5. Individual chatbot evaluation results have not yet been recorded in the evaluation report.

## Risk Register

| Risk | Impact | Status | Recommended action |
|---|---|---|---|
| Relevant question not retrieved | Incorrect or incomplete answer | Requires evaluation | Test paraphrased and out-of-scope questions |
| FAQ content becomes invalid | Retrieval may fail | Requires validation | Validate JSON and document fields |
| Incomplete evaluation evidence | Release defects may be missed | Open | Record actual results for the evaluation set |
| Configuration or secrets are incorrect | Startup or security problems | Requires deployment check | Validate environment configuration without exposing secrets |
| Cross-account data exposure | Sensitive financial data may be exposed | Requires security test evidence | Run cross-user authorization tests |

## Release Note
Do not treat a risk as fixed until the corresponding code change and verification result are recorded.
