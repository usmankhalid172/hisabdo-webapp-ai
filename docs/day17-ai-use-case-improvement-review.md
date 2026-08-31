\# Day 17 — AI Use Case Improvement Review



\*\*Project:\*\* HisabDo Web App AI  

\*\*Department:\*\* Department 1 – Capstone Development  

\*\*Track:\*\* AI/ML  

\*\*Workstream:\*\* AI Use Case / RAG / ML Improvement Review  

\*\*Intern:\*\* Farheen Fatima  

\*\*Day:\*\* 17  



\---



\## 1. Objective



The objective of this review is to evaluate the currently selected AI use cases in the HisabDo Web App AI repository and identify practical improvements, implementation gaps, risks, and priorities for the Capstone.



The review covers:



1\. AI Financial Assistant / Chatbot

2\. RAG-based financial question answering

3\. Smart Expense Categorization

4\. AI/ML evaluation and integration considerations



The recommendations are based on the current repository state and available implementation evidence rather than assuming that planned components are already implemented.



\---



\# 2. Current AI Use Case Status



\## 2.1 AI Financial Assistant / Chatbot



The repository currently contains:



```text

src/financial\_assistant/README.md

```



The directory currently contains documentation only and does not yet contain a working chatbot implementation.



Therefore, the Financial Assistant should currently be treated as a planned AI use case rather than a completed production feature.



\### Current intended functionality



The planned assistant is expected to support:



\- Expense questions

\- Spending summaries

\- Category-based questions

\- Budget-related questions

\- Transaction queries

\- Spending comparisons

\- Financial summaries

\- Clarification of ambiguous questions

\- Safe handling of unsupported requests



\### Review finding



The use case is appropriate for the application, but implementation should begin with deterministic financial data operations before introducing more complex LLM/RAG behavior.



\---



\# 3. Current RAG Approach



Existing project research proposes:



\- Vector retrieval

\- Metadata filtering

\- Grounded prompts

\- Backend financial calculations

\- Fallback responses

\- Hybrid search or reranking only if baseline testing shows a need



This is a reasonable direction for the Capstone.



However, there is currently no implemented Financial Assistant retrieval pipeline in `src/financial\_assistant/`.



\## Improvement Recommendation



The initial architecture should avoid making the LLM responsible for financial arithmetic.



A recommended flow is:



```text

User Question

&#x20;     |

&#x20;     v

Intent / Query Understanding

&#x20;     |

&#x20;     +-----------------------------+

&#x20;     |                             |

&#x20;     v                             v

Structured Financial Data      Knowledge Retrieval

&#x20;     |                             |

&#x20;     v                             v

Deterministic Calculation      Relevant Context

&#x20;     |                             |

&#x20;     +-------------+---------------+

&#x20;                   |

&#x20;                   v

&#x20;            Grounded Response

&#x20;                   |

&#x20;                   v

&#x20;            Validation/Fallback

```



Financial totals, comparisons, budget calculations, and transaction filtering should be performed by application code.



The LLM should primarily interpret natural language and explain already-grounded results.



\---



\# 4. Smart Expense Categorization — Current Evidence



The current implementation uses:



\- TF-IDF text features

\- Unigrams and bigrams

\- Logistic Regression

\- A train/test split based on unique descriptions

\- Classification metrics



The current dataset contains:



\- 500 records

\- 3 columns: `description`, `amount`, `category`

\- 10 categories

\- 50 records per category



The equal category distribution is useful for establishing a baseline because there is no obvious class-count imbalance in the current dataset.



\---



\# 5. Current Model Evaluation



The current model was executed using:



```text

python src\\expense\_categorization\\train\_model.py

```



Observed results:



| Metric | Result |

|---|---:|

| Accuracy | 78.64% |

| Weighted Precision | 85.92% |

| Weighted Recall | 78.64% |

| Weighted F1 | 79.03% |



The test set contained 103 records.



The implementation also verifies that identical descriptions do not appear in both training and testing sets.



Observed result:



```text

Description overlap: 0

```



This is a useful safeguard against a direct description-level leakage between the two splits.



\---



\# 6. Category-Level Findings



The classification report shows that overall accuracy alone does not fully describe model reliability.



Examples:



| Category | Precision | Recall | F1 |

|---|---:|---:|---:|

| Bills | 0.62 | 0.62 | 0.62 |

| Education | 0.67 | 1.00 | 0.80 |

| Entertainment | 1.00 | 0.55 | 0.71 |

| Food | 1.00 | 0.64 | 0.78 |

| Groceries | 0.33 | 1.00 | 0.50 |

| Healthcare | 1.00 | 1.00 | 1.00 |

| Other | 0.75 | 1.00 | 0.86 |

| Shopping | 1.00 | 1.00 | 1.00 |

| Transport | 1.00 | 0.69 | 0.82 |

| Utilities | 0.50 | 1.00 | 0.67 |



These results indicate that some categories require further investigation even though the overall accuracy is approximately 79%.



The Groceries result should be interpreted cautiously because only two Groceries examples were present in the test set.



\---



\# 7. Improvement Area 1 — Expense Categorization Confidence



\## Current limitation



The current training script returns a category prediction but does not implement a production-level confidence or uncertainty policy.



For a financial application, an uncertain prediction should not necessarily be presented to the user as a definitive classification.



\## Recommendation



Use model probability information to establish a simple confidence policy.



Example:



```text

High confidence

&#x20;   -> Automatically accept category



Low confidence

&#x20;   -> Mark as "Needs Review"



Borderline prediction

&#x20;   -> Request user confirmation when appropriate

```



The threshold should be determined experimentally rather than arbitrarily.



This is more realistic than immediately replacing the baseline model with a complex transformer.



\---



\# 8. Improvement Area 2 — Error Analysis



The current evaluation provides aggregate metrics and a classification report, but a production improvement cycle should also inspect actual misclassified transactions.



Recommended error-analysis record:



| Input | Expected | Predicted | Possible Cause | Improvement |

|---|---|---|---|---|

| Expense description | Category | Category | Ambiguous wording / insufficient examples | Add representative training examples |



The team should prioritize recurring confusion patterns rather than changing the model after isolated errors.



\---



\# 9. Improvement Area 3 — Dataset Quality



The current dataset contains 500 synthetic/sample records.



This is sufficient for a baseline proof of concept, but it is not sufficient evidence for production-level financial categorization.



Potential limitations include:



\- Limited vocabulary

\- Repeated description patterns

\- Limited merchant variation

\- Limited real-world ambiguity

\- Limited user-specific language

\- Lack of multilingual/Roman Urdu examples

\- No demonstrated handling of noisy descriptions



\## Recommendation



Before adopting a more complex model, expand and validate the dataset.



Useful additions include:



\- More merchant variations

\- Short descriptions

\- Informal descriptions

\- Misspellings

\- Ambiguous expenses

\- Different transaction wording

\- Realistic category boundaries

\- English and Roman Urdu examples if supported by the product



\---



\# 10. Improvement Area 4 — Financial Assistant Data Grounding



A financial chatbot should not allow the LLM to invent financial values.



The application should provide structured facts such as:



```text

total\_expense

date\_range

category

transaction\_count

largest\_transaction

budget

remaining\_budget

```



The LLM can then convert these verified values into a natural-language response.



For example:



```text

Application:

total\_expense = 42500

period = August 2026



LLM:

"You spent PKR 42,500 in August 2026."

```



The model should not independently calculate or invent the underlying financial value.



\---



\# 11. Improvement Area 5 — Query and Date Handling



Financial questions commonly contain natural-language periods:



\- today

\- yesterday

\- this week

\- last week

\- this month

\- last month

\- this weekend

\- August 1 to August 10



These expressions should be normalized by application logic before financial calculations are performed.



Recommended approach:



```text

Natural-language date

&#x20;       |

&#x20;       v

Date normalization

&#x20;       |

&#x20;       v

Start date + End date

&#x20;       |

&#x20;       v

Transaction filtering

&#x20;       |

&#x20;       v

Deterministic calculation

```



This reduces ambiguity and makes results reproducible.



\---



\# 12. Improvement Area 6 — Retrieval Strategy



Vector RAG should be introduced only where it provides value.



For structured financial questions such as:



```text

How much did I spend this month?

```



direct database/dataframe aggregation is more appropriate than semantic document retrieval.



RAG is more useful for questions involving financial knowledge or explanatory content, for example:



```text

What does the 50/30/20 budgeting rule mean?

```



Therefore, the recommended architecture is a hybrid approach:



```text

Structured financial query

&#x20;   -> Financial data tools / backend calculations



Knowledge-based question

&#x20;   -> Retrieval / RAG



Mixed question

&#x20;   -> Financial data + relevant retrieved knowledge

```



This avoids unnecessary RAG complexity.



\---



\# 13. Improvement Area 7 — Retrieval Evaluation



If vector RAG is implemented, retrieval quality should be measured separately from LLM response quality.



A small evaluation set should include:



\- User query

\- Expected relevant context

\- Retrieved context

\- Retrieval score

\- Correct/incorrect retrieval



Potential metrics include:



\- Precision@K

\- Recall@K

\- Hit Rate@K



The team should establish a baseline before adding reranking or hybrid retrieval.



\---



\# 14. Improvement Area 8 — Multi-Turn Context



Financial questions may depend on previous turns.



Example:



```text

User:

How much did I spend on food this month?



Assistant:

\[answer]



User:

What about last month?

```



The second question depends on the previous category.



The chatbot should maintain structured conversation state such as:



```text

intent = spending\_total

category = food

previous\_period = current\_month

```



The system can then resolve:



```text

"last month"

```



without requiring the user to repeat:



```text

"How much did I spend on food last month?"

```



Conversation state should be controlled by the application rather than relying entirely on the LLM's memory.



\---



\# 15. Improvement Area 9 — User Data Isolation



Financial information is sensitive.



A production implementation must ensure that retrieval and calculations are scoped to the authenticated user.



Recommended rule:



```text

Authenticated User

&#x20;     |

&#x20;     v

User-scoped financial data

&#x20;     |

&#x20;     v

Query processing

&#x20;     |

&#x20;     v

User-scoped response

```



The system must not retrieve or combine another user's transactions.



This should be treated as a core architecture requirement rather than an optional improvement.



\---



\# 16. Improvement Area 10 — Evaluation Strategy



The AI Financial Assistant should be evaluated at multiple levels.



\## Level 1 — Financial correctness



Does the calculated value match the underlying transaction data?



\## Level 2 — Retrieval correctness



If RAG is used, did the system retrieve the appropriate context?



\## Level 3 — Response correctness



Does the generated response accurately represent the calculated/retrieved information?



\## Level 4 — Safety



Does the assistant avoid:



\- Fabricating financial information

\- Revealing system prompts

\- Revealing credentials

\- Mixing user data

\- Making unsupported financial claims



\## Level 5 — Usability



Is the response:



\- Clear

\- Concise

\- Relevant

\- Understandable



\---



\# 17. Prioritized Recommendations



The improvements should be implemented in the following order.



| Priority | Improvement | Reason |

|---|---|---|

| P0 | Deterministic financial calculations | Prevent incorrect financial arithmetic |

| P0 | User-scoped data access | Protect sensitive financial information |

| P0 | Grounded response + fallback | Reduce hallucination risk |

| P1 | Financial query/date normalization | Improve question handling |

| P1 | Expense-model confidence threshold | Handle uncertain predictions safely |

| P1 | Error analysis | Identify actual model weaknesses |

| P1 | Financial Assistant evaluation set | Establish measurable quality |

| P2 | Vector retrieval | Improve semantic knowledge retrieval |

| P2 | Retrieval evaluation | Measure RAG quality |

| P2 | Conversation state | Improve follow-up questions |

| P3 | Hybrid search/reranking | Add only if baseline retrieval is insufficient |

| P3 | Advanced transformer models | Consider only after baseline evidence |



\---



\# 18. Improvements That Should NOT Be Prioritized Yet



The current Capstone does not need unnecessary architectural complexity.



The team should not immediately introduce:



\- Multi-agent architecture

\- Complex autonomous agents

\- Large-scale vector infrastructure

\- Fine-tuning a large language model

\- Transformer-based expense classification without baseline evidence

\- Reranking before retrieval quality is measured

\- Multiple LLM providers without a clear requirement



The current baseline should be measured first.



\---



\# 19. Key Risks and Limitations



| Risk | Impact | Mitigation |

|---|---|---|

| LLM hallucination | Incorrect financial information | Ground responses in structured data |

| Incorrect retrieval | Wrong contextual answer | Retrieval evaluation + thresholds |

| User data mixing | Privacy/security issue | Strict user-scoped access |

| Ambiguous questions | Incorrect interpretation | Clarification and structured intent handling |

| Limited dataset | Poor categorization generalization | Expand and validate dataset |

| Category confusion | Incorrect expense classification | Error analysis + additional examples |

| Low confidence predictions | Incorrect automatic categorization | Confidence threshold + review fallback |

| API latency/cost | Poor user experience | Keep calculations local and minimize unnecessary LLM calls |

| Synthetic data | Limited production validity | Validate with realistic data |

| Natural-language dates | Incorrect transaction filtering | Deterministic date normalization |



\---



\# 20. Overall Assessment



The selected AI use cases are technically appropriate for the HisabDo Capstone.



The Smart Expense Categorization feature already has a working baseline using TF-IDF and Logistic Regression, with approximately 78.6% test accuracy and 79.0% weighted F1-score.



The Financial Assistant is currently at the planning/research stage rather than being a completed chatbot implementation.



The recommended strategy is therefore incremental:



```text

Existing ML baseline

&#x20;       |

&#x20;       v

Error analysis + confidence handling

&#x20;       |

&#x20;       v

Financial data/query layer

&#x20;       |

&#x20;       v

Grounded Financial Assistant

&#x20;       |

&#x20;       v

Targeted RAG

&#x20;       |

&#x20;       v

Retrieval evaluation

&#x20;       |

&#x20;       v

Advanced retrieval only if justified

```



This approach keeps the implementation realistic for the Capstone while providing a clear path toward a more capable AI Financial Assistant.



\---



\# 21. Day 17 Deliverable Evidence



This review provides:



\- Current AI use-case assessment

\- Current implementation status

\- ML performance evidence

\- RAG improvement analysis

\- Practical technical recommendations

\- Prioritized improvement roadmap

\- Evaluation recommendations

\- Risk and limitation analysis

\- Guidance on avoiding unnecessary complexity



The review is based on the repository state available during Day 17 development.



\---



\# 22. Recommended Next Steps



1\. Establish the Financial Assistant's structured financial query/data layer.

2\. Add deterministic date and transaction filtering.

3\. Define an evaluation dataset for financial questions.

4\. Add confidence handling to expense categorization.

5\. Perform systematic model error analysis.

6\. Implement grounded response generation.

7\. Add retrieval only for knowledge-oriented financial questions.

8\. Measure retrieval quality before introducing reranking or hybrid search.

9\. Validate user-data isolation during integration.

10\. Re-evaluate the AI use cases after implementation evidence is available.

