# Knowledge Base Management

## Current Structure
The FAQ knowledge base is stored in `data/faq_docs.json`.
The current file contains 12 documents. Each document uses `id`, `title`, and `text`.

## Maintenance Procedure
1. Back up `data/faq_docs.json` before editing.
2. Add or update entries using the existing JSON structure.
3. Keep each ID unique and each title and text meaningful.
4. Validate the JSON format before running tests.
5. Run the retrieval and RAG pipeline tests after changes.
6. Review retrieval results for relevant and irrelevant questions.

## Retrieval Behaviour
The FAQ retriever uses TF-IDF vectors and cosine similarity.
Its current relevance threshold is 0.12.
Changes to FAQ content or the threshold may affect search results.

## Ownership and Change Control
Record the date, reason, and documents changed for each update.
Do not add real customer financial information or secrets to FAQ documents.
