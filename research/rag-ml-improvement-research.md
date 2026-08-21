\# RAG/ML Improvement Research



\## 1. AI Financial Assistant / Chatbot



\### RAG Improvements



\- Improve document chunking and metadata.

\- Use vector search with Top-K relevant results.

\- Consider hybrid search if vector retrieval is insufficient.

\- Use grounded prompts to reduce hallucinations.

\- Perform financial calculations through the backend instead of the LLM.

\- Add fallback responses when relevant information is unavailable.



\### Risks / Limitations



\- Hallucinations

\- Incorrect retrieval

\- User data mixing

\- High latency or API cost



\### Recommendation



Start with simple vector RAG + metadata filtering + grounded responses.

Add reranking or hybrid search only if testing shows a need.



\---



\## 2. Smart Expense Categorization



\### ML Improvements



\- Clean and validate expense data.

\- Use TF-IDF + Logistic Regression as the baseline.

\- Compare with Random Forest or Decision Tree.

\- Use merchant, description, amount, and other reliable features.

\- Handle class imbalance.

\- Add prediction confidence and a "Needs Review" fallback.



\### Evaluation



\- Accuracy

\- Precision

\- Recall

\- F1-score

\- Confusion Matrix



\### Risks / Limitations



\- Limited or imbalanced data

\- Unknown merchants

\- Incorrect labels

\- Ambiguous expenses



\### Recommendation



Start with a simple ML baseline and consider embeddings or transformer

models only if the baseline performs poorly.



\---



\## 3. Implementation Considerations



\- Keep the initial implementation simple.

\- Evaluate the baseline before adding advanced techniques.

\- Avoid unnecessary complexity.

\- Keep financial calculations in the backend.

\- Validate AI/ML outputs before returning them to users.

\- Test using realistic financial questions and expense examples.

