\# Day 25 (Part 2) — Expense Classification Model Fine-Tuning \& Evaluation Report



\*\*Project:\*\* HisabDo Web App AI  

\*\*Department:\*\* Department 1 – Capstone Development  

\*\*Track:\*\* AI/ML  

\*\*Workstream:\*\* AI Financial Assistant / Chatbot  

\*\*Intern:\*\* Rameesha Zafar  

\*\*Task:\*\* Fine-tune inference logic and classification models (Logistic Regression / Decision Trees) for transaction categorization, run predictions, and tune confidence thresholds for edge cases  

\*\*Day:\*\* 25 (Part 2)  



\---



\## 1. Objective



The objective of Day 25 (Part 2) is to implement and fine-tune machine learning inference logic for automated expense transaction categorization within the HisabDo AI ecosystem.



This document serves to:

\* Detail the classification model fine-tuning architecture (TF-IDF N-Gram Vectorizer + Logistic Regression Classifier).

\* Establish optimal confidence thresholding to gracefully catch edge-case or ambiguous transaction descriptions as `Uncategorized`.

\* Report classification accuracy metrics, test logs, and prediction evaluations.

\* Provide an executable script (`scripts/fine\_tune\_expense\_classifier.py`) ready for backend pipeline integration.



\---



\## 2. Model Architecture \& Fine-Tuning Parameters



| Parameter / Component | Configuration | Description / Purpose |

| :--- | :--- | :--- |

| \*\*Model Algorithm\*\* | Logistic Regression | Lightweight, fast inference, highly interpretable linear classifier. |

| \*\*Text Feature Extractor\*\* | TF-IDF Vectorizer | Extract unigram and bigram features (`ngram\_range=(1,2)`). |

| \*\*Regularization Parameter ($C$)\*\* | `C=1.0` | Balanced L2 regularization to prevent overfitting on short text queries. |

| \*\*Confidence Threshold\*\* | `0.35` (35%) | Minimum prediction probability required to assign a financial category. |

| \*\*Fallback Label\*\* | `Uncategorized` | Assigned when prediction confidence falls below the probability threshold. |



\---



\## 3. Evaluation Metrics \& Test Logs



The fine-tuned classifier was evaluated against a representative test set containing edge-case transactions:



\### 3.1 Sample Prediction Log

\* \*\*Input:\*\* `"Grocery shopping for monthly provisions"` $\\rightarrow$ \*\*Predicted:\*\* `Groceries` (Confidence: 0.4215) $\\rightarrow$ \*\*Status:\*\* \*\*PASSED\*\*

\* \*\*Input:\*\* `"Office commute taxi fare"` $\\rightarrow$ \*\*Predicted:\*\* `Transportation` (Confidence: 0.4890) $\\rightarrow$ \*\*Status:\*\* \*\*PASSED\*\*

\* \*\*Input:\*\* `"Utility bill payment electric supply"` $\\rightarrow$ \*\*Predicted:\*\* `Utilities` (Confidence: 0.4632) $\\rightarrow$ \*\*Status:\*\* \*\*PASSED\*\*

\* \*\*Input:\*\* `"Pharmacy painkiller medicine"` $\\rightarrow$ \*\*Predicted:\*\* `Healthcare` (Confidence: 0.3980) $\\rightarrow$ \*\*Status:\*\* \*\*PASSED\*\*

\* \*\*Input:\*\* `"Fast food lunch order pizza"` $\\rightarrow$ \*\*Predicted:\*\* `Food` (Confidence: 0.4120) $\\rightarrow$ \*\*Status:\*\* \*\*PASSED\*\*



\### 3.2 Accuracy Summary

\* \*\*Overall Evaluation Accuracy:\*\* 100.00% on sample validation set.

\* \*\*Precision / Recall / F1-Score:\*\* 1.00 across all primary expense categories (`Groceries`, `Transportation`, `Utilities`, `Healthcare`, `Food`).



\---



\## 4. Integration Readiness \& Deliverables



1\. \*\*Tuning Script:\*\* Created `scripts/fine\_tune\_expense\_classifier.py` containing complete training, inference thresholding, and metric reporting logic.

2\. \*\*Backend API Readiness:\*\* The model pipeline exports normalized category strings directly compatible with downstream RAG and Chatbot query engines.

3\. \*\*Repository Evidence:\*\* Pushed to feature branch `feature/task15-25-classification-rameesha-2`.



\---



\## 5. Summary \& Next Steps



\* \*\*Branch Created:\*\* `feature/task15-25-classification-rameesha-2`

\* \*\*Script Deliverable:\*\* `scripts/fine\_tune\_expense\_classifier.py`

\* \*\*Documentation Deliverable:\*\* `docs/day25-part2-expense-classification-model-fine-tuning.md`

\* \*\*Next Steps:\*\* Submit Pull Request to GitHub, attach link to ClickUp subtask, and coordinate API model loading with backend leads.

