"""
Healthcare Document Cleaning & Vector Ingestion Preparation Script
Project: AI Healthcare Assistant & Smart Appointment Platform
Sprint: Sprint 1 (4 Sep - 8 Sep 2026)
Task: Rameesha Zafar - Healthcare Document Cleaning & Vector Ingestion
"""

import json
import os
import re

def clean_and_prepare_vector_chunks(input_path, output_path):
    print("--- Starting Healthcare Knowledge Base Cleaning & Ingestion ---")

    if not os.path.exists(input_path):
        print(f"[ERROR] Input file not found at '{input_path}'.")
        return False

    with open(input_path, 'r', encoding='utf-8') as f:
        documents = json.load(f)

    processed_chunks = []
    seen_ids = set()
    cleaned_count = 0

    for idx, doc in enumerate(documents):
        doc_id = doc.get("doc_id")

        if doc_id in seen_ids:
            print(f"[WARNING] Skipping duplicate document ID: {doc_id}")
            continue
        seen_ids.add(doc_id)

        title = doc.get("title", "").strip()
        specialty = doc.get("specialty", "").strip().title()
        raw_content = doc.get("content", "")

        sanitized_content = re.sub(r'\s+', ' ', raw_content).strip()
        chunk_text = f"Specialty: {specialty} | Title: {title} | Content: {sanitized_content}"

        processed_chunk = {
            "chunk_id": f"CHUNK_{doc_id}",
            "specialty": specialty,
            "metadata": {
                "doc_id": doc_id,
                "title": title,
                "approved_by": doc.get("approved_by", "Medical Board Admin"),
                "last_updated": doc.get("last_updated", "2026-09-04")
            },
            "vector_payload_text": chunk_text
        }

        processed_chunks.append(processed_chunk)
        cleaned_count += 1

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(processed_chunks, f, indent=2)

    print("\n--- Ingestion & Chunking Summary ---")
    print(f"Total Source Documents Processed: {len(documents)}")
    print(f"Vector-Ready Chunks Exported: {cleaned_count}")
    print(f"Sanitized Vector Chunk Asset Saved To: {output_path}")

    return True

if __name__ == "__main__":
    raw_file = os.path.join("healthcare-platform", "data", "healthcare_knowledge_base.json")
    ingest_file = os.path.join("healthcare-platform", "data", "vector_ready_chunks_sprint1.json")
    clean_and_prepare_vector_chunks(raw_file, ingest_file)