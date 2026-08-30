# Day 20 – RAG/ML Final Improvement Review and Implementation Readiness

**Prepared by:** Farheen Fatima  
**Workstream:** AI/ML – RAG and Smart Expense Categorization  
**Day:** 20  
**Repository:** `usmankhalid172/hisabdo-webapp-ai`

---

## 1. Objective

This document provides the Day 20 technical review of the current RAG/chatbot and Smart Expense Categorization approaches.

The purpose of this review is to:

- Continue the RAG/ML improvement work from Days 15–19.
- Review the current implementation and technical direction.
- Identify practical risks and limitations.
- Separate immediate improvements from future improvements.
- Identify dependencies on other feature owners.
- Recommend realistic next steps for Capstone integration.
- Avoid unnecessary complexity or duplicate implementation work.

The recommendations in this document are based on the existing repository structure, previous research, current ML prototype results, chatbot/RAG implementation work, integration notes, and roadmap documentation.

---

## 2. Continuity With Previous Work

Day 20 continues the work completed during Days 15–19.

The previous work established the following:

- Day 15: Initial RAG/ML research and technical planning.
- Day 16: RAG/ML implementation support and Smart Expense Categorization baseline work.
- Day 17: AI use-case improvement review.
- Day 18: RAG/ML integration risks and integration-readiness review.
- Day 19: Consolidated RAG/ML improvement roadmap and remaining technical considerations.

Day 20 does not restart these activities.

Instead, this review uses the existing research and implementation evidence to identify the most practical improvements that can be carried forward toward the final Capstone integration.

---

## 3. Current AI/ML Workstreams

The current Department 1 AI/ML work contains two primary AI/ML use cases:

1. AI Financial Assistant / Chatbot
2. Smart Expense Categorization

Both use cases have different technical requirements and should therefore be improved using appropriate approaches rather than forcing a single architecture onto both.

---

## 4. AI Financial Assistant / Chatbot

The Financial Assistant is intended to answer financial questions using application data, a knowledge base, retrieval, deterministic financial calculations, and optionally an LLM.

The current chatbot/RAG implementation includes separate components for:

- Intent detection
- Transaction data handling
- Knowledge-base loading
- Chunking
- Retrieval
- Prompt construction
- Response generation
- Response validation
- LLM integration
- End-to-end orchestration

The repository structure indicates that the chatbot implementation is already moving beyond a simple unrestricted LLM chatbot.

The intended flow is:

```text
User
  |
  v
HisabDo Application
  |
  v
Backend/API
  |
  v
Financial Assistant
  |
  +----> Intent Detection
  |
  +----> Transaction / Backend Data
  |
  +----> Knowledge Base
  |          |
  |          v
  |       Retrieval
  |
  v
Response Generation
  |
  v
Response Validation
  |
  v
Validated Response
  |
  v
HisabDo Application
  |
  v
User

## 5. Current RAG Approach

The current RAG direction is based on a relatively simple retrieval architecture.

The existing approach includes:

- Knowledge-base loading.
- Text chunking.
- Metadata/tag support.
- Retrieval based on relevant content.
- Grounded prompt construction.
- Response validation.
- Fallback handling.
- Optional LLM generation.

The current research recommendation remains to start with simple retrieval before introducing more complex retrieval systems.

The preferred initial architecture is:

```text
Knowledge Base
      |
      v
Document Loading
      |
      v
Chunking + Metadata
      |
      v
Retrieval
      |
      v
Relevant Context
      |
      v
Grounded Prompt
      |
      v
LLM / Deterministic Response
      |
      v
Validation
      |
      v
Final Response


## 6. RAG Improvement Recommendations

The current RAG approach should remain simple and practical for the Capstone.

Recommended improvements:

- Improve chunking so related information stays together.
- Use small chunk overlap where necessary.
- Add useful metadata such as topic, source, category, and document section.
- Test retrieval using realistic financial questions.
- Use grounded prompts to reduce hallucinations.
- Keep retrieval lightweight to avoid unnecessary latency and cost.
- Consider hybrid keyword + semantic search only if testing shows retrieval failures.
- Add reranking only if basic retrieval is not sufficiently accurate.
- Maintain fallback responses when relevant information cannot be retrieved.

The priority should be improving retrieval quality and reliability before adding complex RAG infrastructure.


## 7. Grounded Response Generation

The chatbot should not rely on the LLM to independently invent financial facts.

The preferred flow is:

```text
User Question
      |
      v
Retrieve Relevant Information
      |
      v
Provide Context to Model
      |
      v
Generate Grounded Response
      |
      v
Validate Response

The system should ensure that:

- The model uses the supplied context.
- The model does not invent unavailable facts.
- Unsupported information is not presented as confirmed.
- Financial calculations are handled by backend logic where possible.
- The assistant clearly states when information is unavailable.
- Responses remain within the supported financial scope.

Grounded generation should be combined with retrieval, validation, and fallback handling to reduce hallucinations and improve reliability.


## 8. Financial Calculations Should Remain Backend-Controlled

Financial calculations should be handled by deterministic backend code wherever possible.

Examples include:

- Total spending
- Monthly expenses
- Highest spending category
- Spending summaries
- Budget calculations
- Transaction totals

The preferred flow is:

```text
User Question
      |
      v
Intent Detection
      |
      v
Backend Financial Calculation
      |
      v
Validated Result
      |
      v
Response Generation
      |
      v
User

The LLM may explain the calculated result, but it should not be treated as the source of truth for numerical calculations.

This reduces arithmetic errors, improves consistency, and makes financial results easier to validate.


## 9. Response Validation

Response validation is an important protection against unreliable AI output.

The chatbot should validate responses before returning them to the user.

Validation should check for:

- Empty responses
- Unsupported financial numbers
- Unrelated responses
- Unavailable information presented as fact
- Responses outside the supported financial scope

A simplified validation flow is:

```text
Generated Response
       |
       v
Validation
       |
   +---+---+
   |       |
 Valid   Invalid
   |       |
   v       v
 Return   Fallback
 Response Response

Response validation should remain part of the final integration architecture to improve reliability and reduce unsafe or unsupported answers.


## 10. RAG Risks and Limitations

The main risks and limitations of the current RAG/chatbot approach are:

- **Hallucination:** The LLM may generate information that is not present in the retrieved context.
- **Incorrect Retrieval:** Relevant information may exist in the knowledge base but fail to be retrieved.
- **Out-of-Scope Questions:** Users may ask questions outside the supported financial functionality.
- **Incorrect Calculations:** LLM-generated arithmetic may be inaccurate.
- **Latency:** Retrieval, model calls, and validation can increase response time.
- **API Cost:** External LLM/API calls may introduce additional costs.
- **Privacy:** Financial information requires careful handling and should not be unnecessarily exposed to external services.

Recommended mitigations include:

- Grounded prompts and response validation.
- Better chunking, metadata, and retrieval testing.
- Intent and scope validation with clear fallback responses.
- Backend-controlled financial calculations.
- Lightweight retrieval and avoiding unnecessary model calls.
- Monitoring API usage and controlling context size.
- Never committing secrets or private user data.

These risks should be monitored during integration and end-to-end testing.


## 11. Smart Expense Categorization

The second major AI/ML workstream is Smart Expense Categorization.

The current baseline approach uses expense descriptions with TF-IDF text features and Logistic Regression.

The basic flow is:

```text
Expense Description
        |
        v
      TF-IDF
        |
        v
Logistic Regression
        |
        v
Predicted Category

The current repository contains a baseline training implementation in:

src/expense_categorization/train_model.py

The training script loads the expense dataset, separates unique descriptions into training and testing sets, trains the model, evaluates its performance, and saves the trained pipeline.

The current approach is suitable as a simple Capstone baseline. More complex models should only be considered after evaluating the baseline and identifying specific performance limitations.


## 12. Current Dataset Status

The current synthetic expense dataset contains:

- 500 rows
- 3 columns
- `description`
- `amount`
- `category`

There are 10 expense categories, with 50 examples per category:

- Education
- Groceries
- Utilities
- Transport
- Other
- Food
- Bills
- Entertainment
- Shopping
- Healthcare

The balanced category distribution is useful for the initial baseline experiment.

However, the dataset is still synthetic and relatively small. It should not be considered representative of real production user behaviour.

A larger and approved dataset should be used for meaningful model evaluation before production deployment.


## 13. Current Baseline Evaluation

The current training script produced the following evaluation results:

```text
Training rows: 397
Testing rows: 103
Unique descriptions: 200
Description overlap: 0

Accuracy: 0.7864077669902912
Precision: 0.8592233009708737
Recall: 0.7864077669902912
F1-score: 0.7903350990103262

### Rounded Results

| Metric | Result |
|---|---:|
| Accuracy | 78.64% |
| Weighted Precision | 85.92% |
| Weighted Recall | 78.64% |
| Weighted F1-score | 79.03% |

The model achieved approximately 78.64% accuracy on the test set.

The Description overlap: 0 result confirms that no identical description was present in both the training and testing sets.

These results should be treated as a baseline proof of concept, not as production-level performance. The dataset is synthetic and relatively small, so broader evaluation on representative approved data is required.


## 14. Baseline Classification Findings

The classification report shows different performance levels across the expense categories.

| Category | Precision | Recall | F1-score |
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

The weaker results include:

- Groceries precision: **0.33**
- Bills precision/recall: **0.62**
- Utilities precision: **0.50**
- Entertainment recall: **0.55**
- Transport recall: **0.69**

These results suggest that better training data and targeted error analysis should be prioritized before replacing the baseline with a more complex model.


## 15. ML Improvement Recommendations

The current ML baseline is useful for the Capstone, but several practical improvements can be made.

- Increase the size and quality of the training dataset.
- Add realistic expense descriptions and common merchant names.
- Include spelling variations, short descriptions, and ambiguous expenses.
- Perform systematic error analysis on incorrect predictions.
- Compare additional features such as merchant, amount, payment method, date/time, and currency.
- Evaluate each new feature before including it in the final model.
- Use confidence scores to identify uncertain predictions.
- Add a **"Needs Review"** fallback for low-confidence predictions.
- Continue using Accuracy, Precision, Recall, F1-score, and confusion matrix for evaluation.

The main priority should be improving the dataset and understanding model errors before introducing more complex ML or transformer-based approaches.


## 16. Evaluate Additional Features Carefully

The current baseline mainly uses expense description text.

Potential additional features include:

- Merchant
- Amount
- Payment method
- Date/time
- Currency

These features should not be added automatically. Each feature should be tested to determine whether it provides a measurable improvement.

A practical comparison is:

```text
Text Only
    |
    v
Baseline Score

Text + Merchant
    |
    v
Compare Score

Text + Merchant + Amount
    |
    v
Compare Score

Only features that improve model performance or reliability should be retained.

This keeps the implementation simple and avoids adding unnecessary complexity to the Capstone.


## 17. Confidence and "Needs Review" Fallback

A practical improvement is to avoid forcing the model to make a confident-looking prediction for every expense.

The future prediction service can use the model's confidence score to identify uncertain predictions.

Recommended flow:

```text
Prediction Confidence >= Threshold
            |
            v
   Return Predicted Category

Prediction Confidence < Threshold
            |
            v
      Return "Needs Review"

The exact confidence threshold should be selected using validation data rather than chosen arbitrarily.

A low-confidence fallback can reduce the risk of silently assigning an incorrect category and allows uncertain expenses to be reviewed by the user or application.

This feature should be added after the baseline prediction service is integrated and confidence behaviour has been evaluated.


## 18. ML Risks and Limitations

The current Smart Expense Categorization model has several risks and limitations:

- **Small Dataset:** The current dataset is suitable for a baseline experiment but may not represent real user behaviour.
- **Synthetic Data:** Synthetic descriptions may differ from real-world expense descriptions.
- **Ambiguous Expenses:** Some expenses can reasonably belong to more than one category.
- **Unknown Merchants:** New or unseen merchants may reduce prediction accuracy.
- **Category Quality:** Incorrect or inconsistent labels can negatively affect model performance.
- **Data Leakage:** Repeated descriptions can make evaluation misleading if they appear in both training and testing data.

The current training script reduces the data-leakage risk by splitting unique descriptions before creating the training and testing sets.

The evaluation confirmed:

```text
Description overlap: 0

Recommended mitigations include:

- Obtain a larger approved dataset.
- Validate category labels.
- Add realistic and varied training examples.
- Perform detailed error analysis.
- Evaluate merchant and other additional features.
- Use confidence thresholds and a "Needs Review" fallback for uncertain predictions.

The current model should remain classified as a Capstone prototype until it is evaluated on larger and representative approved data.


## 19. Immediate Improvements vs Future Improvements

### Immediate Improvements

The following improvements should be prioritized for the current Capstone:

- Connect the baseline ML model to the appropriate prediction service.
- Finalize the API request and response schema.
- Validate API inputs and handle invalid requests safely.
- Run broader model evaluation.
- Perform systematic error analysis.
- Add realistic and representative test cases.
- Test chatbot retrieval using realistic financial questions.
- Keep financial calculations deterministic and backend-controlled.
- Maintain response validation and fallback behaviour.
- Record integration and testing evidence.

### Future / Optional Improvements

The following improvements should only be considered if testing shows that the current approach is insufficient:

- Hybrid retrieval
- Retrieval reranking
- Transformer-based expense classification
- Embedding-based expense classification
- Advanced semantic search
- More sophisticated model ensembles
- Large-scale vector infrastructure
- Advanced model monitoring

The Capstone should avoid introducing these technologies without evidence that the existing approach cannot meet the required functionality or reliability.


## 20. Final Recommendations, Dependencies and Next Steps

### Final Technical Recommendations

The recommended architecture for the current Capstone is:

```text
                    HISABDO APPLICATION
                           |
                           v
                     BACKEND / API
                           |
              +------------+------------+
              |                         |
              v                         v
       FINANCIAL ASSISTANT       EXPENSE SERVICE
              |                         |
              v                         v
       Intent Detection          Input Validation
              |                         |
        +-----+-----+                   v
        |           |             ML Pipeline
        v           v                   |
   Backend Data   RAG Retrieval         v
        |           |              Category
        |           v              Prediction
        |      Grounded Prompt          |
        |           |                   |
        +-----+-----+                   |
              |                         |
              v                         v
        Response Validation       Confidence Check
              |                         |
              v                         v
        Validated Response       Validated Prediction
              |                         |
              +------------+------------+
                           |
                           v
                          USER

The current approach should prioritize simple, reliable, testable, and maintainable components rather than unnecessary complexity.

### Dependencies on Feature Owners

The following work should be coordinated with the relevant feature owners:

- Financial Assistant / chatbot implementation
- RAG knowledge-base implementation
- Smart Expense Categorization model implementation
- Prediction API integration
- Application/backend integration
- Integration testing
- Final model evaluation

This review should not duplicate the primary implementation responsibilities of those feature owners.

### Current Open Technical Considerations

The following items remain open:

- Final chatbot API contract
- Final expense prediction API contract
- Larger approved dataset
- Model evaluation on representative data
- Retrieval-quality testing
- End-to-end integration testing
- Confidence threshold selection
- Final validation rules
- Performance and latency measurements
- Security and privacy requirements
- Production-readiness criteria

### Blockers / Dependencies

No new implementation blocker was identified during this review.

The main dependencies are:

- Availability of an approved representative dataset.
- Completion of the relevant API and integration work.
- Coordination with chatbot and expense-categorization feature owners.
- Completion of broader testing.
- Team Lead confirmation of the integration and merge workflow.

Until these dependencies are resolved, the current ML and RAG components should be treated as Capstone prototypes rather than production-ready services.

### Day 20 Completion Summary

### Work Completed
- Reviewed the current Financial Assistant/RAG architecture.
- Reviewed the current Smart Expense Categorization baseline.
- Reviewed the latest baseline evaluation results.
- Identified RAG risks and mitigation strategies.
- Identified ML risks and mitigation strategies.
- Defined practical RAG improvements.
- Defined practical ML improvements.
- Separated immediate improvements from optional future improvements.
- Documented feature-owner dependencies.
- Documented current open technical considerations.
- Defined practical next steps toward Capstone integration.
- Preserved continuity with the Day 15–19 research and roadmap work.

### Work Still Remaining
- Finalize API integration.
- Complete broader testing.
- Obtain and validate a larger approved dataset.
- Perform additional ML error analysis.
- Evaluate retrieval quality using realistic chatbot queries.
- Perform end-to-end integration testing.
- Confirm production-readiness requirements.

### Current Blocker / Confusion

No new blocker was identified.

Remaining work depends primarily on API/integration owners, approved dataset availability, testing, and Team Lead coordination.

### Proof / Evidence
- research/rag-ml-improvement-research.md
- docs/day19-rag-ml-roadmap.md
- docs/smart_expense_categorization_roadmap.md
- docs/smart_expense_integration_notes.md
- src/expense_categorization/train_model.py
- Current baseline evaluation output
- Financial Assistant/RAG implementation branch evidence
- Day 15–19 GitHub contributions and documentation

### Day 20 Status

The Day 20 review consolidates the current RAG/ML technical direction, risks, limitations, improvement recommendations, dependencies, and remaining implementation work.

The recommended approach is to continue with the existing simple RAG and ML baselines while prioritizing integration, testing, data quality, validation, and measurable evaluation before introducing advanced techniques.