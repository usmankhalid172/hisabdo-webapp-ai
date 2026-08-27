\# Day 16 — RAG/ML Implementation Support



\## Current Implementation Direction



\### AI Financial Assistant / Chatbot



The current direction focuses on financial question handling, chatbot

prompting, knowledge-base retrieval, and RAG-based responses.



The implementation should remain modular so that retrieval, prompting,

and response generation can be evaluated and improved independently.



\### Smart Expense Categorization



The current direction focuses on expense preprocessing, feature

extraction, classification, prediction, and model evaluation.



A simple baseline should remain the reference point for evaluating

future improvements.



\---



\## RAG Improvement Support



\### Practical Improvements



\- Expand the retrieval test set with representative financial questions.

\- Tune the number of retrieved results (Top-K) based on evaluation.

\- Improve document chunking and metadata where retrieval quality is

&#x20; insufficient.

\- Use grounded prompts so generated answers rely on retrieved context.

\- Add a fallback response when relevant information cannot be retrieved.

\- Consider hybrid search or reranking only if the baseline retrieval

&#x20; does not provide sufficient results.



\### Evaluation



RAG improvements should be evaluated using:



\- Precision@K

\- Recall@K

\- F1-score

\- Groundedness

\- Hallucination rate

\- Retrieval latency

\- End-to-end response latency

\- API/model cost where applicable



Each improvement should be compared against the existing baseline using

the same test questions.



\---



\## RAG Technical Limitations and Solutions



| Limitation | Practical Solution |

|---|---|

| Irrelevant retrieved results | Tune Top-K and improve retrieval |

| Relevant information is missed | Measure Recall@K and improve retrieval coverage |

| Poor answer grounding | Require answers to use retrieved context |

| Hallucinated information | Add grounded-response validation and fallback handling |

| Slow responses | Measure retrieval and generation latency separately |

| Increased API cost | Track cost before adopting additional model calls |

| Insufficient test coverage | Expand the fixed financial-question test set |



Advanced retrieval techniques should only be introduced when baseline

evaluation identifies a specific retrieval problem.



\---



\## ML Improvement Support



\### Practical Improvements



\- Keep the current simple ML approach as the baseline.

\- Validate the preprocessing pipeline before model comparison.

\- Ensure representative examples exist for each expense category.

\- Evaluate per-category performance rather than relying only on accuracy.

\- Perform error analysis on incorrect predictions.

\- Consider a confidence threshold and `Needs Review` fallback for

&#x20; uncertain predictions.

\- Test alternative models only when baseline performance indicates a

&#x20; need for improvement.



\### Evaluation



The expense categorization baseline should be evaluated using:



\- Accuracy

\- Precision

\- Recall

\- Macro F1-score

\- Weighted F1-score

\- Confusion matrix

\- Per-category performance

\- Prediction latency where applicable



\---



\## ML Technical Limitations and Solutions



| Limitation | Practical Solution |

|---|---|

| Small dataset | Increase representative training/test examples |

| Class imbalance | Check category distribution and use suitable evaluation |

| Unknown merchants | Add fallback handling for low-confidence predictions |

| Ambiguous descriptions | Perform error analysis and improve training examples |

| Similar categories | Review confusion matrix and category definitions |

| Overly complex model | Compare against the simple baseline before adoption |



\---



\## Baseline-First Improvement Process



For both RAG and ML:



1\. Establish the current simple baseline.

2\. Prepare a fixed evaluation/test set.

3\. Measure baseline performance.

4\. Identify the main limitation.

5\. Introduce one practical improvement.

6\. Run the same tests again.

7\. Compare the new results with the baseline.

8\. Keep the improvement only if it provides a meaningful benefit.



Advanced techniques such as hybrid search, reranking, stronger

embeddings, or transformer-based models should only be considered when

the baseline does not meet the required performance.



\---



\## Implementation Support Recommendations



\### AI Financial Assistant / RAG



\- Keep retrieval and response generation modular.

\- Add retrieval-quality checks before relying on generated answers.

\- Provide a safe fallback when the knowledge base does not contain

&#x20; sufficient information.

\- Test financial questions covering normal, ambiguous, and unsupported

&#x20; queries.



\### Smart Expense Categorization



\- Keep preprocessing and prediction logic separate.

\- Maintain the simple baseline for comparison.

\- Record incorrect predictions for error analysis.

\- Avoid forcing predictions when model confidence is too low.



\---



\## Remaining Work



\- Apply the recommended evaluation approach to the current RAG and ML

&#x20; implementations.

\- Expand test data where required.

\- Record baseline metrics.

\- Perform error analysis.

\- Compare improvements against the baseline.

\- Coordinate any implementation changes with the relevant feature owners.

