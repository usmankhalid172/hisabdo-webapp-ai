Absolutely. Below is the **complete, clean Markdown file**. You can copy everything inside the code block directly into:

`docs/day15-rag-planning.md`

````markdown
# Day 15 — RAG & Knowledge Base Planning

## HisabDo AI Financial Assistant

### 1. Objective

The objective of this task is to define the requirements and architecture for a Retrieval-Augmented Generation (RAG) system for the HisabDo AI Financial Assistant.

The RAG component will retrieve relevant information from HisabDo documentation, FAQs, and general financial knowledge to support chatbot responses.

Exact user-specific financial information will **not** be treated as RAG knowledge. Questions involving live financial values, customer balances, revenue, expenses, or other user-specific records will be handled through authenticated backend/API access and deterministic database queries or calculations.

This separation helps ensure that general knowledge is retrieved semantically while live financial information comes directly from the user's authorized financial records.

---

## 2. Knowledge Base Requirements

The knowledge base should contain reliable and structured information relevant to the HisabDo application.

### A. HisabDo Application Information

The RAG knowledge base should contain information about:

- HisabDo features
- User account functionality
- Customer management instructions
- Sales and transaction functionality
- Income and expense features
- Financial summary functionality
- Business record management
- Invoice and payment functionality
- Dashboard functionality
- Frequently asked questions
- Basic troubleshooting information
- General application usage instructions

This information is intended for documentation and instructional retrieval.

### B. General Financial Knowledge

The knowledge base can also contain general financial information useful for small businesses, such as:

- Revenue
- Expenses
- Profit and loss concepts
- Cash flow
- Outstanding payment concepts
- Customer balance concepts
- Basic budgeting concepts
- Expense categorization
- Financial record-keeping
- Small-business financial terminology

This information should explain financial concepts rather than provide live values for a specific user.

### C. User-Specific Financial Data

User-specific financial information should **not** be stored as permanent general RAG knowledge.

Examples include:

- Current revenue
- Monthly revenue
- Customer balances
- Outstanding invoices
- Current expenses
- Transaction totals
- Payments received
- Payments pending
- Customer-specific amounts

These values should be retrieved dynamically from the authenticated HisabDo backend/API.

For example:

```text
User:
"How much did I earn this month?"

        ↓

Intent recognized as user-specific financial query

        ↓

Authenticated Backend/API

        ↓

Retrieve user's transactions/revenue

        ↓

Deterministic calculation

        ↓

Return exact result to chatbot

        ↓

Response:
"Your total revenue for this month is Rs. XX."
````

The RAG knowledge base should not be used as the source of truth for these live financial values.

---

## 3. Proposed Knowledge Base Structure

The initial RAG knowledge base can use structured JSON documents.

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
  "answer": "Open the customer records section in HisabDo to view the financial information associated with a customer."
}
```

The knowledge base should contain documentation, FAQs, instructions, and general financial concepts.

Live user-specific financial records should remain in the application's backend/database and should be accessed through authenticated APIs when required.

---

# 4. Retrieval and Data-Access Approach

The proposed architecture separates **semantic knowledge retrieval** from **exact financial-data retrieval**.

### A. RAG / Semantic Retrieval

RAG is responsible for retrieving relevant information from:

* HisabDo documentation
* HisabDo FAQs
* General financial knowledge
* Financial terminology
* Application usage instructions
* General financial guidance

The proposed retrieval approach is semantic retrieval using **SentenceTransformer embeddings and FAISS**.

### B. Exact Financial Data Retrieval

Exact user-specific financial questions should not be answered using semantic vector retrieval.

Examples include:

* "How much did I earn this month?"
* "Who owes me the most?"
* "What are my expenses this month?"
* "What is my current balance?"
* "How much does Customer A owe me?"
* "What were my sales last month?"

These questions require access to the authenticated user's financial records.

The proposed flow is:

```text
User Question

      ↓

Query / Intent Classification

      ↓

Authenticated Backend/API

      ↓

Database Query

      ↓

Deterministic Calculation

      ↓

Exact Financial Result

      ↓

Chatbot Response
```

The backend/database remains the source of truth for live financial data.

---

# 5. RAG Retrieval Flow

### Step 1 — Receive User Query

The chatbot receives a natural-language question.

Example:

> "What is the difference between revenue and profit?"

### Step 2 — Query Classification

The system determines whether the question is:

1. A general knowledge/documentation question, or
2. An exact user-specific financial-data question.

### Step 3 — RAG Query Embedding

If the question is a general knowledge or documentation query, it is converted into a numerical vector using SentenceTransformer.

### Step 4 — Similarity Search

FAISS searches the vector index for semantically similar documents.

### Step 5 — Retrieve Relevant Context

The system retrieves the Top-K relevant documents.

For example:

```text
Document 1:
Revenue is the total income generated by a business.

Document 2:
Profit is the amount remaining after expenses are deducted from revenue.
```

### Step 6 — Context Construction

The retrieved documents are combined into context for the response-generation component.

### Step 7 — Generate Response

The chatbot generates an answer grounded in the retrieved documentation or financial knowledge.

### Step 8 — Return Answer

The final response is returned to the user in a clear and understandable format.

---

# 6. Exact User Financial Query Flow

Exact financial-data questions follow a separate path.

Example:

> "Who owes me the most money?"

The system should **not** perform semantic FAISS retrieval over customer records to determine the answer.

Instead:

```text
                  User Query
                      |
                      v
              Query Classification
                      |
                      v
            User Financial Query
                      |
                      v
          Authentication / Authorization
                      |
                      v
             HisabDo Backend/API
                      |
                      v
              User Financial Data
                      |
                      v
        Deterministic Database Query
                      |
                      v
        Calculate Highest Outstanding
                      |
                      v
              Exact Result
                      |
                      v
             Chatbot Response
```

For example, if the backend returns:

```text
Customer A — Rs. 15,000
Customer B — Rs. 8,000
Customer C — Rs. 21,000
```

the backend or deterministic application logic can identify:

```text
Customer C — Rs. 21,000
```

The chatbot can then respond:

> "Based on your current records, Customer C has the highest outstanding balance of Rs. 21,000."

The calculation is performed from authenticated financial records rather than semantic similarity.

---

# 7. Retrieval-Flow Diagram

The overall architecture is:

```text
                         ┌─────────────────┐
                         │    User Query   │
                         └────────┬────────┘
                                  │
                                  v
                     ┌────────────────────────┐
                     │ Query / Intent         │
                     │ Classification         │
                     └───────────┬────────────┘
                                 │
                  ┌──────────────┴──────────────┐
                  │                             │
                  v                             v
       ┌─────────────────────┐       ┌──────────────────────┐
       │ General Knowledge / │       │ Exact User Financial │
       │ Documentation Query │       │ Data Query            │
       └──────────┬──────────┘       └───────────┬───────────┘
                  │                              │
                  v                              v
       ┌─────────────────────┐       ┌──────────────────────┐
       │ SentenceTransformer │       │ Authentication /     │
       │ Query Embedding     │       │ Authorization         │
       └──────────┬──────────┘       └───────────┬───────────┘
                  │                              │
                  v                              v
       ┌─────────────────────┐       ┌──────────────────────┐
       │ FAISS Similarity    │       │ HisabDo Backend/API  │
       │ Search              │       └───────────┬───────────┘
       └──────────┬──────────┘                   │
                  │                              v
                  v                   ┌──────────────────────┐
       ┌─────────────────────┐        │ Database Query /     │
       │ Relevant Top-K      │        │ Deterministic        │
       │ Documents           │        │ Calculation          │
       └──────────┬──────────┘        └───────────┬───────────┘
                  │                              │
                  v                              v
       ┌─────────────────────┐        ┌──────────────────────┐
       │ Context Builder     │        │ Exact Financial      │
       │                     │        │ Result               │
       └──────────┬──────────┘        └───────────┬───────────┘
                  │                              │
                  └──────────────┬───────────────┘
                                 │
                                 v
                       ┌───────────────────┐
                       │ Response Generator│
                       └─────────┬─────────┘
                                 │
                                 v
                       ┌───────────────────┐
                       │ Final Chatbot     │
                       │ Response          │
                       └───────────────────┘
```

---

# 8. Proposed RAG Architecture

The proposed architecture consists of separate components for knowledge retrieval and financial-data access.

### 1. Knowledge Sources

The RAG knowledge base contains:

* HisabDo application documentation
* HisabDo FAQs
* Application usage instructions
* General financial knowledge
* Financial terminology
* General small-business guidance

The following are **not treated as permanent RAG knowledge**:

* Live customer balances
* Current revenue
* Current expenses
* Live transactions
* User account balances
* User-specific financial calculations

These remain in the backend/database.

### 2. Embedding Layer

SentenceTransformer will convert RAG knowledge-base documents and general knowledge queries into vector representations.

### 3. Vector Database

FAISS will store and search the embeddings of the RAG knowledge-base documents.

FAISS is used for semantic retrieval and should not be treated as the source of truth for live financial values.

### 4. Financial Data Layer

The authenticated HisabDo backend/API will provide access to user-specific financial information.

This layer is responsible for:

* Authentication
* Authorization
* User-specific data filtering
* Database queries
* Deterministic calculations

### 5. Response Generation

The response-generation component will receive either:

* Retrieved RAG context for general/documentation questions, or
* Exact backend/API results for user-specific financial questions.

The chatbot can then generate the final user-facing response.

---

# 9. How Retrieval Supports Chatbot Responses

RAG provides the chatbot with relevant documentation and general financial knowledge.

### General Knowledge Question

**Question:**

> "What is the difference between revenue and profit?"

The system retrieves relevant financial knowledge from the RAG knowledge base.

The chatbot can answer:

> "Revenue is the total income generated by a business, while profit is what remains after expenses are deducted from revenue."

### HisabDo Documentation Question

**Question:**

> "How can I check a customer's balance in HisabDo?"

The RAG system retrieves the relevant HisabDo documentation and provides it as context to the chatbot.

### Exact Financial Question

**Question:**

> "Who owes me the most money?"

This is **not a RAG retrieval task**.

The system should:

1. Authenticate the user.
2. Access the user's financial records through the backend/API.
3. Query outstanding customer balances.
4. Determine the highest balance using deterministic logic.
5. Return the exact result to the chatbot.

This separation reduces the risk of the chatbot using stale or semantically similar information when an exact financial value is required.

---

# 10. Response-Quality Approach

Response quality depends on selecting the correct information source.

### Relevance

The response should directly address the user's question.

### Accuracy

General knowledge responses should be supported by retrieved documentation or reliable financial knowledge.

Exact financial responses should match the authenticated backend/database result.

### Groundedness

The chatbot should not invent financial values.

RAG responses should be grounded in retrieved documents.

User-specific financial responses should be grounded in backend/API results.

### Completeness

The answer should contain the important information needed by the user.

### Clarity

Responses should use simple language suitable for small-business users.

### Consistency

Similar questions should produce logically consistent responses.

### Source Selection

The system should select the appropriate source based on the query:

```text
General / Documentation Question
        ↓
RAG / FAISS
        ↓
Retrieved Context
        ↓
Response
```

```text
Exact User Financial Question
        ↓
Authenticated Backend/API
        ↓
Database Query
        ↓
Deterministic Calculation
        ↓
Exact Result
        ↓
Response
```

### Handling Missing Information

If the RAG knowledge base does not contain sufficient information, the chatbot should not guess.

Example:

> "I couldn't find enough information in the available HisabDo documentation to answer that accurately."

If the backend cannot retrieve the required financial information, the chatbot should communicate the limitation rather than inventing a value.

---

# 11. Basic Evaluation Examples

| User Query                                         | Query Type          | Expected Source           | Quality Check                |
| -------------------------------------------------- | ------------------- | ------------------------- | ---------------------------- |
| What is profit?                                    | General knowledge   | RAG knowledge base        | Correct definition           |
| What is the difference between revenue and profit? | General knowledge   | RAG knowledge base        | Relevant explanation         |
| How do I record an expense in HisabDo?             | Documentation       | RAG knowledge base        | Useful instructions          |
| How do I check a customer balance in HisabDo?      | Documentation       | RAG knowledge base        | Correct instructions         |
| How much did I earn this month?                    | User financial data | Authenticated Backend/API | Exact calculated amount      |
| Who owes me the most?                              | User financial data | Authenticated Backend/API | Correct customer and balance |
| What were my expenses last month?                  | User financial data | Authenticated Backend/API | Correct date-filtered amount |
| What is my current balance?                        | User financial data | Authenticated Backend/API | Exact current value          |

The evaluation should verify both retrieval quality and correct source selection.

---

# 12. Technical Limitations

The following limitations have been identified:

1. RAG retrieval quality depends on the quality and completeness of the knowledge base.

2. Semantic search may retrieve partially relevant information.

3. FAISS requires embeddings to be generated consistently.

4. Large knowledge bases may require indexing and performance optimization.

5. The system may struggle with ambiguous questions.

6. User-specific financial information requires proper authentication, authorization, and user-level filtering.

7. RAG must not be used as the source of truth for live financial values.

8. Exact financial calculations depend on the accuracy and availability of backend financial records.

9. The response-generation model may still produce hallucinations if the retrieved context or backend result is insufficient.

10. The current prototype uses structured JSON data for knowledge retrieval and may need to be connected to production documentation/data sources later.

11. Production database/API integration depends on the final backend architecture.

12. Model/API availability and API limits can affect response generation.

13. Query classification between general knowledge and user-specific financial questions must be reliable to prevent incorrect source selection.

---

# 13. Dependencies

The planned implementation may depend on:

* Python
* SentenceTransformer
* FAISS
* NumPy
* JSON/structured knowledge-base data
* FastAPI or Flask
* HisabDo backend/API
* Production database
* Authentication and authorization mechanisms
* Response-generation LLM/API
* HisabDo application documentation
* Financial knowledge sources

---

# 14. Current Missing Information / Blockers

The following information needs to be confirmed before final implementation:

* Final production database structure
* Exact HisabDo API endpoints
* Available financial fields
* Authentication requirements
* Authorization and user-data isolation requirements
* Expected number of users and records
* Final LLM/API to be used
* Required RAG retrieval Top-K value
* Final knowledge-base dataset
* Query classification/routing approach
* Backend endpoints for revenue, expenses, customers, balances, and transactions
* Final evaluation dataset/questions

### Current Blocker

The main blocker is that the final production backend/database structure and API requirements have not yet been confirmed.

The RAG component can proceed independently for documentation, FAQs, and general financial knowledge, while integration with live user financial data should wait for the confirmed backend/API structure.

---

# 15. Coordination With Financial Assistant Workstream

The RAG component should support the Financial Assistant without duplicating the chatbot implementation.

The responsibilities should be separated as follows:

### RAG / Knowledge Retrieval Workstream

Responsible for:

* Knowledge-base structure
* Documentation and FAQ retrieval
* General financial knowledge retrieval
* Embedding generation
* FAISS/vector search
* Top-K relevant document retrieval
* Retrieval evaluation

### Backend / Financial Data Workstream

Responsible for:

* User authentication
* Authorization
* Access to user financial records
* Database queries
* Revenue calculations
* Expense calculations
* Customer balance calculations
* Transaction queries

### Chatbot / Financial Assistant Workstream

Responsible for:

* Conversation flow
* Query classification/routing
* Sending general questions to RAG
* Sending exact financial questions to backend/API
* Passing retrieved context/results to the response-generation model
* Generating the final user-facing response

The intended flow is:

```text
                         User Question
                              |
                              v
                    Query Classification
                              |
              ┌───────────────┴────────────────┐
              |                                |
              v                                v
       General Knowledge              Exact Financial Data
       / Documentation                      Query
              |                                |
              v                                v
          RAG / FAISS                  Authenticated API
              |                                |
              v                                v
      Relevant Documents             Exact Data / Calculation
              |                                |
              └───────────────┬────────────────┘
                              |
                              v
                    Response Generation
                              |
                              v
                    Financial Assistant
                              |
                              v
                         User Response
```

The RAG workstream will provide retrieval results to the chatbot workstream and will not implement or duplicate the chatbot's conversation-generation logic.

---

# 16. Current Day 15 Status

### Work Completed

* Defined RAG knowledge-base requirements.
* Identified HisabDo application documentation and FAQ information required.
* Identified general financial knowledge required.
* Separated general knowledge retrieval from exact user-specific financial data.
* Defined that live financial values must come from authenticated backend/API access.
* Selected semantic retrieval as the proposed RAG approach.
* Selected SentenceTransformer + FAISS for initial semantic retrieval.
* Designed the RAG retrieval flow.
* Designed the exact financial-data query flow.
* Defined the separation between RAG, backend/API, and chatbot responsibilities.
* Defined how retrieved RAG context will support chatbot responses.
* Defined response-quality criteria.
* Added evaluation examples for both RAG and exact financial queries.
* Documented technical limitations and dependencies.
* Identified missing information and blockers.
* Defined coordination requirements with the Financial Assistant workstream.

## Remaining Work

* Finalize the RAG knowledge-base dataset.
* Implement semantic retrieval using SentenceTransformer + FAISS if approved.
* Define and implement query classification/routing between RAG and financial-data APIs.
* Confirm backend financial-data API endpoints.
* Confirm authentication and authorization requirements.
* Confirm production database structure.
* Define evaluation questions and retrieval metrics.
* Coordinate RAG integration with the chatbot workstream.

### Blocker / Confusion

The main blocker is the lack of confirmed production backend/database specifications and financial-data API requirements.

The RAG component can proceed with documentation, FAQs, and general financial knowledge.

Integration with live user-specific financial data depends on confirmed authenticated backend/API endpoints and database structure.

### Proof / Evidence

* Day 15 RAG Planning Document
* Knowledge-base requirements
* RAG retrieval-flow diagram
* Exact financial-data query flow
* Proposed SentenceTransformer + FAISS architecture
* Response-quality criteria
* RAG vs backend/API source-selection approach
* Technical limitation/dependency note
* GitHub documentation and commit for Day 15 planning work
* Existing Day 15 feature branch and Pull Request

```
```
