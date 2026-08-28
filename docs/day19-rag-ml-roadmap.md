\# Day 19 – RAG/ML Improvement Roadmap



\*\*Prepared by:\*\* Farheen Fatima  

\*\*Workstream:\*\* RAG / ML Improvement Review  

\*\*Day:\*\* 19  

\*\*Repository:\*\* hisabdo-webapp-ai



\---



\## 1. Purpose



This document consolidates the RAG and ML improvement recommendations, risks, limitations, dependencies, and practical next steps identified during the Day 15–18 AI/ML work.



The goal is to keep the Capstone implementation realistic and avoid unnecessary complexity while identifying the improvements required for reliable integration.



Previously completed research and implementation work is referenced rather than repeated.



\---



\# 2. Current AI/ML Use Cases



The current Department 1 AI/ML work includes two main use cases:



\### 2.1 AI Financial Assistant / Chatbot



Planned capabilities include:



\- Financial question answering

\- Chatbot interaction

\- RAG-based retrieval where applicable

\- Grounded responses

\- Response validation

\- Backend-supported financial calculations



\### 2.2 Smart Expense Categorization



The current ML implementation uses:



\- Expense descriptions as input

\- TF-IDF text features

\- Logistic Regression classification

\- Ten expense categories

\- Train/test evaluation

\- Accuracy, Precision, Recall and F1-score evaluation



\---



\# 3. Existing Research Reference



The Day 15 research identified practical improvements for both AI use cases.



Existing research:



`research/rag-ml-improvement-research.md`



The research recommended starting with simple approaches and only introducing advanced techniques when evaluation demonstrates a need.



This principle is retained for Day 19.



\---



\# 4. RAG Improvement Recommendations



\## 4.1 Immediate Improvements



\### A. Grounded responses



The chatbot should generate answers using retrieved context where RAG is required.



The prompt should clearly instruct the model to avoid presenting unsupported information as fact.



\*\*Priority:\*\* High



\### B. Retrieval validation



Retrieved documents/chunks should be checked for relevance before being passed to the LLM.



If useful information cannot be retrieved, the system should avoid generating an unsupported answer.



\*\*Priority:\*\* High



\### C. Fallback handling



The system should provide a safe fallback when:



\- No relevant context is found.

\- Retrieval confidence is low.

\- The AI service fails.

\- The request cannot be answered reliably.



\*\*Priority:\*\* High



\### D. Metadata filtering



Where applicable, retrieved information should use metadata such as document type or relevant user context to reduce irrelevant results.



\*\*Priority:\*\* Medium



\### E. Top-K retrieval



The initial implementation should use a small Top-K retrieval strategy rather than retrieving excessive context.



This helps reduce:



\- Irrelevant context

\- Token usage

\- Latency

\- Potential confusion for the LLM



\*\*Priority:\*\* Medium



\---



\# 5. RAG Improvements for Later Evaluation



The following techniques should not be added automatically.



They should only be considered if testing demonstrates that the basic RAG pipeline is insufficient.



\### Hybrid Search



Combine vector search with keyword-based search when semantic retrieval alone misses important terms.



\### Reranking



Use a reranking step to improve ordering of retrieved results when Top-K retrieval produces irrelevant results.



\### Advanced Embeddings



Consider stronger embedding models only if the baseline retrieval quality is inadequate.



\### Query Rewriting



Consider query rewriting if users frequently ask questions that cannot be retrieved effectively using their original wording.



\*\*Recommendation:\*\*



Do not introduce these techniques before baseline retrieval quality has been tested.



\---



\# 6. Smart Expense Categorization – Current Baseline



The existing implementation uses:



\- TF-IDF vectorization

\- Unigrams and bigrams

\- Logistic Regression

\- Train/test split based on unique descriptions

\- Classification metrics



The dataset currently contains:



\- 500 rows

\- 3 columns: description, amount, category

\- 200 unique descriptions

\- 10 categories

\- 50 samples per category



The categories are:



\- Education

\- Groceries

\- Utilities

\- Transport

\- Other

\- Food

\- Bills

\- Entertainment

\- Shopping

\- Healthcare



\---



\# 7. Current ML Evaluation



The current baseline produced:



| Metric | Result |

|---|---:|

| Accuracy | 78.64% |

| Weighted Precision | 85.92% |

| Weighted Recall | 78.64% |

| Weighted F1-score | 79.03% |



The baseline is useful as an initial reference point.



It should not be treated as a final production-quality performance target until additional realistic testing is completed.



\---



\# 8. ML Improvement Recommendations



\## 8.1 Immediate Improvements



\### A. Data quality validation



Review:



\- Duplicate descriptions

\- Incorrect labels

\- Ambiguous descriptions

\- Missing values

\- Inconsistent wording



\*\*Priority:\*\* High



\### B. Error analysis



Review incorrect predictions using the classification report and confusion matrix.



Identify categories that are frequently confused.



\*\*Priority:\*\* High



\### C. Realistic test cases



Test the model using descriptions that differ from the training examples.



Examples should include:



\- Short descriptions

\- Detailed descriptions

\- Similar expenses

\- Ambiguous expenses

\- Unknown merchants

\- Unusual wording



\*\*Priority:\*\* High



\### D. Confidence / review fallback



The application should avoid blindly accepting uncertain predictions.



A future implementation can introduce a confidence threshold and return:



`Needs Review`



when the model is not sufficiently confident.



\*\*Priority:\*\* Medium



\---



\# 9. Optional ML Improvements



These should be considered only after evaluating the baseline.



\### Alternative Classifiers



Compare Logistic Regression with:



\- Decision Tree

\- Random Forest

\- Other suitable lightweight classifiers



\### Additional Features



Potential features include:



\- Merchant information

\- Expense amount

\- Transaction metadata

\- Normalized merchant names



\### Class Imbalance Handling



The current dataset is balanced across categories, but future production data may not be.



Class distribution should therefore be monitored after real application data becomes available.



\### Embedding-Based Classification



Embeddings or transformer-based models could be evaluated if traditional TF-IDF features perform poorly on realistic user inputs.



\*\*Recommendation:\*\*



Do not replace the current lightweight baseline without evaluation evidence.



\---



\# 10. Technical Risks



\## 10.1 RAG Risks



\### Hallucination



The LLM may generate information that is not supported by retrieved context.



\*\*Mitigation:\*\*



Use grounded prompts, retrieval validation and fallback responses.



\### Incorrect Retrieval



The correct information may not be retrieved.



\*\*Mitigation:\*\*



Evaluate chunking, Top-K retrieval and metadata filtering before introducing advanced retrieval methods.



\### User Data Mixing



Incorrect retrieval or poor isolation could expose information from an unrelated context.



\*\*Mitigation:\*\*



Apply appropriate metadata/user-context filtering and validate access boundaries during integration.



\### Latency



Multiple retrieval and model calls may increase response time.



\*\*Mitigation:\*\*



Keep the initial pipeline simple and avoid unnecessary model calls.



\### API Cost / Rate Limits



External AI APIs may introduce cost and rate-limit constraints.



\*\*Mitigation:\*\*



Minimize unnecessary calls and monitor API usage during testing.



\---



\# 11. ML Risks



\## Limited Dataset



The current dataset contains only 500 records and 200 unique descriptions.



This may not represent the variety of real user expense descriptions.



\*\*Mitigation:\*\*



Expand the dataset with realistic examples before relying on the model for production decisions.



\### Ambiguous Expenses



Some descriptions can reasonably belong to multiple categories.



\*\*Mitigation:\*\*



Use clearer training examples and consider a review/fallback mechanism.



\### Unknown Merchants



A merchant may not appear in the training data.



\*\*Mitigation:\*\*



Normalize merchant information and collect additional examples.



\### Incorrect Labels



Incorrect training labels can directly affect model predictions.



\*\*Mitigation:\*\*



Perform dataset validation and error analysis.



\### Distribution Changes



Real application data may differ from the current dataset.



\*\*Mitigation:\*\*



Monitor model performance after integration and periodically review errors.



\---



\# 12. Immediate vs Future Improvements



| Area | Immediate | Future / Optional |

|---|---|---|

| RAG | Grounded prompts | Query rewriting |

| RAG | Retrieval validation | Reranking |

| RAG | Fallback responses | Hybrid search |

| RAG | Top-K retrieval | Advanced embeddings |

| RAG | Metadata filtering | More advanced retrieval pipelines |

| ML | Data validation | Larger production dataset |

| ML | Error analysis | Embedding-based classification |

| ML | Realistic test cases | Transformer models |

| ML | Baseline evaluation | Advanced model tuning |

| ML | Review fallback design | More sophisticated confidence calibration |



The immediate improvements should be completed before adding optional complexity.



\---



\# 13. Integration Dependencies



The AI/ML work depends on coordination with other feature owners.



\### Financial Assistant / Chatbot



Coordination is required for:



\- API request/response schema

\- RAG service integration

\- Prompt handling

\- Response validation

\- Error/fallback behavior

\- Application-facing endpoints



\### Smart Expense Categorization



Coordination is required for:



\- Model inference interface

\- Input/output schema

\- Prediction confidence handling

\- Category mapping

\- Application integration

\- Error handling



The AI/ML implementation should support these owners without duplicating their primary feature work.



\---



\# 14. Current Open Technical Considerations



The following items remain to be validated:



1\. Final API request and response schemas.

2\. Actual integration between the application backend and AI/ML services.

3\. RAG retrieval quality using realistic financial questions.

4\. Chatbot response validation.

5\. Expense categorization performance on unseen realistic inputs.

6\. Model confidence threshold for uncertain predictions.

7\. Fallback behavior for failed or uncertain AI/ML responses.

8\. API latency and rate-limit behavior.

9\. Production data requirements.

10\. Final integration testing across the application flow.



\---



\# 15. Practical Next Steps



\## Priority 1 – Integration



Connect the AI/ML components to the application-facing service layer.



Expected flow:



User  

→ HisabDo Application  

→ Backend/API  

→ AI Service  

→ Model/LLM  

→ Validation  

→ Response  

→ User



\## Priority 2 – Testing



Create realistic test cases for:



\- Financial questions

\- RAG retrieval

\- Unsupported questions

\- Ambiguous expenses

\- Unknown merchants

\- Invalid inputs

\- AI service failures



\## Priority 3 – Error Analysis



Review:



\- Incorrect RAG retrievals

\- Unsupported chatbot answers

\- Incorrect expense classifications

\- Low-confidence predictions



\## Priority 4 – Improvement



Apply only the improvements supported by testing evidence.



Avoid adding complex retrieval or ML techniques without demonstrating that they solve an observed problem.



\## Priority 5 – Final Evidence



Maintain:



\- GitHub commits

\- Pull Requests

\- Test results

\- Evaluation metrics

\- Research notes

\- Integration/API evidence

\- Screenshots where useful

\- Blocker/dependency notes



\---



\# 16. Progress / Evidence Update



\## Work Completed



\- Reviewed and consolidated Day 15 RAG/ML research.

\- Reviewed Day 16 RAG/ML implementation support work.

\- Reviewed Day 17 AI use-case improvement recommendations.

\- Documented Day 18 RAG/ML integration risks and limitations.

\- Consolidated RAG improvement recommendations.

\- Consolidated ML improvement recommendations.

\- Identified immediate and future improvements.

\- Documented technical risks and known limitations.

\- Identified dependencies on feature owners.

\- Defined practical next steps toward integration.



\## Work Remaining



\- Complete application-facing AI/ML integration.

\- Validate RAG retrieval using realistic application scenarios.

\- Complete chatbot response validation.

\- Perform further ML error analysis using realistic unseen inputs.

\- Define and test fallback behavior.

\- Validate model confidence handling.

\- Perform end-to-end integration testing.

\- Collect final implementation and testing evidence.



\## Blockers / Dependencies



\- Final application/API integration depends on coordination with the relevant feature owners.

\- Final request/response contracts need to be confirmed.

\- RAG and ML behavior cannot be fully validated until the application integration path is available.

\- Production-level performance cannot be concluded from the current limited dataset alone.



\## Evidence



\- `research/rag-ml-improvement-research.md`

\- `docs/day15-financial-assistant-prompts-and-test-cases.md`

\- `docs/model-evaluation-test-plan.md`

\- `docs/day17-ai-use-case-improvement-review.md`

\- `docs/day18-rag-ml-integration-risks.md`

\- `src/expense\_categorization/train\_model.py`

\- Day 16 ML baseline evaluation results

\- Day 17 and Day 18 GitHub branches/PRs



\---



\# 17. Conclusion



The current RAG/ML approach is intentionally kept lightweight for the Capstone.



The recommended strategy is:



1\. Establish a working baseline.

2\. Integrate it with the application.

3\. Test using realistic inputs.

4\. Analyze failures.

5\. Apply targeted improvements.

6\. Introduce advanced techniques only when testing demonstrates a clear need.



This reduces unnecessary complexity while keeping a clear path toward a more reliable AI/ML system before final submission.

