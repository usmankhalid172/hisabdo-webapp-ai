# Day 15 — RAG & Knowledge Base Planning

## HisabDo AI Financial Assistant

### 1. Objective

The objective of this task is to define the requirements and architecture for a Retrieval-Augmented Generation (RAG) system for the HisabDo AI Financial Assistant.

The RAG system will allow the chatbot to retrieve relevant information from HisabDo's financial knowledge base and user-specific business data before generating a response. This will help the assistant provide more relevant, accurate, and context-aware financial assistance instead of relying only on the language model's general knowledge.

---

## 2. Knowledge Base Requirements

The knowledge base should contain reliable and structured information relevant to the HisabDo application.

### A. HisabDo Application Information

The knowledge base should contain information about:

* HisabDo features
* User account functionality
* Customer management
* Sales and transactions
* Income and expenses
* Financial summaries
* Business records
* Invoice/payment information
* Dashboard functionality
* Frequently asked questions
* Basic troubleshooting information

### B. Financial Knowledge

The knowledge base can also contain general financial information useful for small businesses, such as:

* Revenue
* Expenses
* Profit and loss
* Cash flow
* Outstanding payments
* Customer balances
* Basic budgeting concepts
* Expense categorization
* Financial record-keeping
* Small-business financial terminology

### C. User-Specific Data

For personalized responses, the assistant should retrieve relevant information from the user's HisabDo data.

Example:

```text
User:
"How much did I earn this month?"

Retrieved data:
- Monthly sales
- Total revenue
- Relevant transactions
- Date range

Generated response:
"Your total revenue for this month is Rs. XX."
```

User-specific financial information should be retrieved dynamically rather than permanently stored inside the general knowledge base.

---

## 3. Proposed Knowledge Base Structure

The initial knowledge base can use structured JSON documents.

Example:

```json
{
  "category": "financial_knowledge",
  "topic": "profit",
  "question": "What is profit?",
  "answer": "Profit is the amount remaining after subtracting expenses from revenue."
}
```

For HisabDo application information:

```json
{
  "category": "hisabdo",
  "topic": "customer_balance",
  "question": "How can I check a customer's balance?",
  "answer": "Customer balance information can be retrieved from the customer's financial records."
}
```

The existing HisabDo JSON data containing users, summaries, and customers can also be used as a source for personalized retrieval.

---

# 4. Retrieval Approach

The proposed approach is **semantic retrieval using embeddings and FAISS**.

The planned pipeline is:

```text
User Question
      ↓
Question Preprocessing
      ↓
Generate Query Embedding
      ↓
FAISS Similarity Search
      ↓
Retrieve Top-K Relevant Documents
      ↓
Build Context
      ↓
LLM / Response Generator
      ↓
Final Answer
```

The user's question will first be converted into an embedding using a sentence embedding model such as **SentenceTransformer**.

The embedding will then be compared with document embeddings stored in a **FAISS vector index**.

The most relevant documents will be retrieved and provided as context to the response-generation component.

---

# 5. Retrieval Flow

### Step 1 — Receive User Query

The chatbot receives a natural-language question.

Example:

> "Which customer owes me the most money?"

### Step 2 — Query Embedding

The question is converted into a numerical vector using SentenceTransformer.

### Step 3 — Similarity Search

FAISS searches the vector database for the most semantically similar records.

### Step 4 — Retrieve Relevant Context

The system retrieves the top relevant records.

For example:

```text
Customer A — Outstanding: Rs. 15,000
Customer B — Outstanding: Rs. 8,000
Customer C — Outstanding: Rs. 21,000
```

### Step 5 — Context Construction

The retrieved information is combined into a context that is passed to the response-generation model.

### Step 6 — Generate Response

The chatbot generates an answer based primarily on the retrieved information.

### Step 7 — Return Answer

The final response is returned to the user in a simple and understandable format.

---

# 6. Retrieval-Flow Diagram

```text
                  ┌─────────────────┐
                  │   User Query    │
                  └────────┬────────┘
                           ↓
                  ┌─────────────────┐
                  │ Query Processing│
                  └────────┬────────┘
                           ↓
                  ┌─────────────────┐
                  │   Embedding     │
                  │  SentenceTrans. │
                  └────────┬────────┘
                           ↓
                  ┌─────────────────┐
                  │ FAISS Vector DB │
                  │ Similarity Search│
                  └────────┬────────┘
                           ↓
                  ┌─────────────────┐
                  │ Relevant Top-K  │
                  │     Results     │
                  └────────┬────────┘
                           ↓
                  ┌─────────────────┐
                  │ Context Builder │
                  └────────┬────────┘
                           ↓
                  ┌─────────────────┐
                  │ Response / LLM  │
                  │    Generator    │
                  └────────┬────────┘
                           ↓
                  ┌─────────────────┐
                  │ Final Chatbot   │
                  │    Response     │
                  └─────────────────┘
```

---

# 7. Proposed RAG Architecture

The proposed architecture consists of four major components:

### 1. Knowledge Source

Contains:

* HisabDo application documentation
* Financial FAQs
* Financial terminology
* User/business records
* Customer and transaction information

### 2. Embedding Layer

SentenceTransformer will convert knowledge-base documents and user queries into vector representations.

### 3. Vector Database

FAISS will store and search document embeddings.

### 4. Response Generation

The retrieved context will be passed to the response-generation model/API, which will generate the final answer.

---

# 8. How Retrieval Supports Chatbot Responses

Retrieval will provide the chatbot with information directly related to the user's question.

For example:

**Question:**

> "Who owes me the most money?"

Instead of generating a generic response, the retrieval system will find the user's relevant customer records.

The chatbot can then answer:

> "Based on your current records, Customer X has the highest outstanding balance of Rs. XX."

This reduces the chance of the chatbot generating unsupported financial information.

---

# 9. Response-Quality Approach

The following basic criteria will be used to evaluate chatbot responses.

### Relevance

The response should directly answer the user's question.

### Accuracy

The response should match the retrieved HisabDo data.

### Groundedness

The chatbot should base financial answers on retrieved information instead of inventing values.

### Completeness

The answer should contain the important information needed by the user.

### Clarity

Responses should use simple language suitable for small-business users.

### Consistency

Similar questions should produce logically consistent responses.

### Handling Missing Information

If relevant information cannot be retrieved, the chatbot should not guess.

Example:

> "I couldn't find enough information in your records to answer that accurately."

---

# 10. Basic Evaluation Examples

| User Query                       | Expected Retrieval            | Quality Check       |
| -------------------------------- | ----------------------------- | ------------------- |
| How much did I earn this month?  | Monthly revenue records       | Correct amount      |
| Who owes me the most?            | Customer outstanding balances | Correct customer    |
| What are my expenses?            | Expense records               | Relevant expenses   |
| What is profit?                  | Financial knowledge base      | Correct definition  |
| How do I check customer balance? | HisabDo documentation         | Useful instructions |

---

# 11. Technical Limitations

The following limitations have been identified:

1. Retrieval quality depends on the quality and completeness of the knowledge base.
2. Incorrect or outdated financial records may result in incorrect answers.
3. Semantic search may retrieve partially relevant information.
4. FAISS requires embeddings to be generated consistently.
5. Large datasets may require better indexing and optimization.
6. The system may struggle with ambiguous questions.
7. User-specific financial information requires proper filtering and access control.
8. The response-generation model may still produce hallucinations if the retrieved context is insufficient.
9. The current prototype uses structured JSON data, which may need to be replaced or connected to the production database.
10. Model/API availability and API limits can affect response generation.

---

# 12. Dependencies

The planned implementation may depend on:

* Python
* SentenceTransformer
* FAISS
* NumPy
* JSON/structured data
* FastAPI or Flask
* HisabDo backend/API
* Response-generation LLM/API
* Existing HisabDo user/customer/financial data

---

# 13. Current Missing Information / Blockers

The following information needs to be confirmed before final implementation:

* Final production database structure
* Exact HisabDo API endpoints
* Which financial fields are available
* Authentication and authorization requirements
* Expected number of users and records
* Final LLM/API to be used
* Required retrieval Top-K value
* Whether user-specific data should be retrieved from the database/API or vectorized
* Final evaluation dataset/questions

### Current Blocker

The main blocker is that the final production data structure and API requirements need to be confirmed before implementing the complete retrieval pipeline.

---

# 14. Coordination With Financial Assistant Workstream

The RAG component should be integrated with the Financial Assistant rather than developed as an isolated chatbot feature.

The Financial Assistant will provide:

```text
User Question
     ↓
RAG Retrieval
     ↓
Relevant Financial Context
     ↓
Response Generation
     ↓
Financial Assistant Response
```

The RAG system will be responsible for retrieving relevant information, while the Financial Assistant will handle conversation flow and present the information to the user.

---

# 15. Current Day 15 Status

### Work Completed

* Defined knowledge-base requirements.
* Identified HisabDo application and financial information required.
* Defined user-specific data requirements.
* Selected semantic retrieval as the proposed retrieval approach.
* Selected SentenceTransformer + FAISS for initial retrieval.
* Designed the retrieval flow.
* Defined how retrieved context will support chatbot responses.
* Defined response-quality criteria.
* Documented technical limitations and dependencies.
* Identified missing information and blockers.
* Defined coordination requirements with the Financial Assistant workstream.

### Work Remaining

* Finalize the production data structure.
* Confirm API/database integration.
* Prepare and clean the actual knowledge-base data.
* Generate document embeddings.
* Build/update the FAISS index.
* Implement the complete retrieval pipeline.
* Connect retrieved context to the response-generation API.
* Test retrieval accuracy.
* Evaluate chatbot responses using real HisabDo queries.

### Blocker / Confusion

The main blocker is the lack of confirmed production data/API specifications. Final implementation decisions should be validated once the backend data structure and API requirements are confirmed.

### Proof / Evidence

* Day 15 RAG Planning Document
* Knowledge-base requirements
* Retrieval-flow diagram
* Proposed SentenceTransformer + FAISS architecture
* Response-quality criteria
* Technical limitation/dependency note
* GitHub documentation/commit for the Day 15 planning work


