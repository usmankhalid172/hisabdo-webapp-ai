# Department 3 Phase 2, Day 1
## Current Financial Assistant Flow

Date: 5 November 2026

### 1. Purpose
This document describes the current Department 3 chatbot architecture based on source code inspection and available test evidence.

### 2. Current Request Flow

flowchart TD
    A[Client Request] --> B[POST /api/v1/chatbot]
    B --> C[Internal Token Validation]
    C --> D[Authenticated User Identity]
    D --> E[handle_chat]
    E --> F[Safety Guards]
    F -->|Blocked| G[Policy Refusal]
    F -->|Allowed| H{Own Financial Data?}
    H -->|Yes| I[Backend Financial Summary]
    I --> J{Backend Available?}
    J -->|No| K[Backend Unavailable Fallback]
    J -->|Yes| L[LLM Provider]
    H -->|No| M[FAQ Retriever]
    M --> N[TF IDF Similarity]
    N --> O{Score >= 0.30?}
    O -->|No| P[Empty Retrieval Fallback]
    O -->|Yes| Q[LLM with FAQ Context]

### 3. Implemented Components

| Component | Current observation |
|---|---|
| API route | POST /api/v1/chatbot |
| Authentication | Internal token and authenticated user identity |
| Safety | Prompt injection, third party, out of scope, unsafe language and sensitive information guards |
| Financial data | Backend summary lookup |
| FAQ source | data/faq_docs.json |
| Retrieval | TF IDF and cosine similarity |
| Threshold | 0.30 |
| Top K | 1 in active service |
| Default provider | Mock provider in development |

### 4. Source Ingestion and Retrieval
The FAQ retriever loads JSON documents and combines document title and text for retrieval. The inspected implementation does not show document chunking, an external embedding model or a vector database.

The active service requests one retrieval result. The configured relevance threshold is 0.30.

The retriever refresh method returns false on exceptions. Monitoring visibility for refresh failures needs improvement.

### 5. LLM Architecture
The active service uses llm_providers.py.

Development configuration defaults to MockLLMProvider. This provider produces deterministic template responses and does not apply the production system prompt or understand conversation history.

Separate rag_pipeline.py, llm_service.py and vector_store.py components also exist. Their connection to the active service request path has not been established.

The separate vector store uses synthetic in memory transaction data. It is not a production transaction retrieval integration.

### 6. Backend Integration
The backend client interface exposes get_user_financial_summary(user_id).

Development mode uses fixed synthetic PKR values through MockBackendClient.

Production mode reports the backend as unavailable because the real backend integration is not configured.

The approved backend data contract and production session isolation remain open blockers.

### 7. PDF Flow
The chatbot router includes a financial summary PDF endpoint with customer access verification. The PDF request path needs separate testing for backend failures and response formatting.

### 8. Monitoring and Evidence Limitations
Existing execution logs are automated test logs, not real customer query logs or production traces.

Retrieval evaluation measures source ranking only. It does not measure final answer correctness, citation accuracy, language quality or safety.

### 9. Immediate Priorities
1. Finalize the real backend data contract and production integration.
2. Select one canonical retrieval and LLM execution path.
3. Fix verified retrieval ranking misses.
4. Obtain approved Khata and Udhar product sources.
5. Add generated answer evaluation.
6. Improve monitoring of backend, provider and retrieval failures.

### 10. Evidence Status
This document reflects inspected source code and available automated test evidence as of 6 November 2026.

Production behavior and live customer query behavior have not been independently verified.
