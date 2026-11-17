"""Department 3 production configuration freeze (docs/dept3-production-config-freeze-spec.md).

    python scripts/freeze_config.py            # write config/production_freeze_v1.json from the code as it is now
    python scripts/freeze_config.py --verify   # exit 1 when the code, prompts, rules, KB or index differ from the freeze

The freeze records every value that changes what a user is told: retrieval constants, vector index parameters, the
embedding model file hash, prompt and rule hashes, the approved KB hash, and the release gates. Source files are hashed
with line endings normalised, so a Windows and a Linux checkout give the same hash.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
FREEZE = ROOT / "config" / "production_freeze_v1.json"

RULE_FILES = {   # what is hashed, and the part of the package it belongs to
    "src/financial_assistant/prompts.py": "system prompt and grounding rules",
    "src/financial_assistant/guardrails.py": "safety guardrail rules (injection, extraction, secrets, domain, output)",
    "src/financial_assistant/conversation.py": "conversation rules U4-U7 (escalation, repeats, honest limits)",
    "src/financial_assistant/grounding/answer.py": "grounded answer rules R1-R13 and reply templates",
    "src/financial_assistant/grounding/retrieval.py": "retrieval pipeline and glossary",
    "src/financial_assistant/service.py": "routing, third-party guard, fallbacks",
    "src/financial_assistant/dialogue/recognizer.py": "intent router",
    "data/knowledge_source_audit.csv": "approved source register",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def text_sha(s: str) -> str:
    return hashlib.sha256(s.replace("\r\n", "\n").encode("utf-8")).hexdigest()


def current() -> dict:
    from src.config import Settings
    from src.financial_assistant import prompts
    from src.financial_assistant.grounding import answer as A
    from src.financial_assistant.grounding import retrieval as R
    import clean_knowledge_sources as C
    import ingest_dept3 as I

    kb_path = ROOT / "data" / "kb" / "approved" / "kb_chunks.jsonl"
    chunks = [json.loads(l) for l in kb_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    manifest = json.loads((ROOT / "data" / "kb" / "dept3" / "index_manifest.json").read_text(encoding="utf-8"))
    templates = json.dumps(A.TEMPLATES, sort_keys=True, ensure_ascii=False)
    s = Settings.model_fields
    return {
        "freeze_version": "1.0",
        "retrieval": {
            "embedding_model": R.BGE, "query_prefix": R.BGE_QUERY_PREFIX, "max_query_chars": R.MAX_QUERY_CHARS,
            "hybrid_alpha_dense": R.HYBRID_ALPHA, "hybrid_alpha_lexical": round(1 - R.HYBRID_ALPHA, 10),
            "relevance_threshold": R.HYBRID_THRESHOLD, "top_k": R.HYBRID_TOP_K, "margin": R.HYBRID_MARGIN,
            "candidates": R.CANDIDATES,
            "lexical_fallback": {"threshold": R.LEXICAL_THRESHOLD, "top_k": R.LEXICAL_TOP_K, "margin": R.LEXICAL_MARGIN},
            "bm25": {"k1": 1.5, "b": 0.75, "score_saturation_k": 5.0},
            "metadata_filter": "off", "reranker": "off",
            "router_gate": "intent faq only reaches the knowledge base",
        },
        "vector_index": {
            "type": "in-memory exact search (NumPy matrix, no ANN index: no HNSW or IVF parameters)",
            "dimensions": manifest["embedding"]["dimensions"], "normalisation": manifest["embedding"]["normalisation"],
            "similarity": manifest["embedding"]["similarity"], "passage_text": manifest["embedding"]["passage_text"],
            "model_repo": manifest["embedding"]["resolved_repo"], "model_file": manifest["embedding"]["onnx_file"],
            "model_file_sha256": manifest["embedding"]["onnx_sha256"],
            "vector_checksum": manifest["embedding"]["checksum"], "records": manifest["records"],
            "kb_version_index_manifest": manifest["kb_version"],
        },
        "chunking": {"faq": "one question and answer per chunk, never split", "section_max_chars": C.MAX_CHARS,
                     "overlap": "none", "short_intro_merge_below_chars": 150},
        "grounding": {"support_min": A.SUPPORT_MIN, "switch_margin": A.SWITCH_MARGIN,
                      "max_sentences_per_passage": A.MAX_SENTENCES_PER_PASSAGE, "max_excerpt_chars": A.MAX_EXCERPT_CHARS,
                      "related_sentences": A.RELATED_SENTENCES, "rare_word_max_df": A.RARE_DF,
                      "source_authority": A.AUTHORITY},
        "settings_required_in_production": {
            "GROUNDED_ANSWERS_ENABLED": "true", "GUARDRAILS_ENABLED": "true", "KB_RETRIEVER_MODE": "hybrid",
            "DIALOGUE_ENABLED": "true", "LLM_PROVIDER": "mock until a provider passes the same gates",
            "INTERNAL_SERVICE_TOKEN": "32+ characters, from the secret store, never in the repository",
            "FASTEMBED_CACHE_PATH": "a fixed folder, so the verified model file is reused",
        },
        "settings_defaults_in_code": {"grounded_answers_enabled": s["grounded_answers_enabled"].default,
                                      "guardrails_enabled": s["guardrails_enabled"].default,
                                      "kb_retriever_mode": s["kb_retriever_mode"].default},
        "prompts": {"system_prompt_sha256": text_sha(prompts.SYSTEM_PROMPT),
                    "grounding_rules_sha256": text_sha(prompts.GROUNDING_RULES),
                    "reply_templates_sha256": text_sha(templates)},
        "rule_files_sha256": {p: sha(ROOT / p) for p in RULE_FILES},
        "knowledge_base": {"approved_chunks_file": "data/kb/approved/kb_chunks.jsonl", "sha256": sha(kb_path),
                           "chunks": len(chunks), "sources": len({c["source_id"] for c in chunks}),
                           "kb_version": R.kb_version(chunks),
                           "knowledge_set_sha256": sha(ROOT / "data" / "kb" / "dept3" / "knowledge_set.jsonl"),
                           "snapshot": manifest["snapshot"]},
        "release_gates": {"acceptance_critical": "25/25", "acceptance_major": "6/6", "safety_suite_v1.1": "CLEARED x4",
                          "conversation_journeys": "8/8", "adversarial_cases": "18/18", "grounded_transcripts": "19/19",
                          "retrieval_correct_139": ">= 120", "knowledge_p95_ms": "< 250", "account_p95_ms": "< 150"},
        "environment_informational": {**manifest["environment"], "platform": platform.platform()},
    }


def diff(frozen, now, path="") -> list[str]:
    out = []
    if isinstance(frozen, dict) and isinstance(now, dict):
        for k in sorted(set(frozen) | set(now)):
            if k == "environment_informational":
                continue
            if k not in frozen or k not in now:
                out.append(f"{path}{k}: {'added' if k not in frozen else 'removed'}")
            else:
                out += diff(frozen[k], now[k], f"{path}{k}.")
    elif frozen != now:
        out.append(f"{path[:-1]}: frozen {str(frozen)[:60]} != now {str(now)[:60]}")
    return out


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    now = current()
    if not a.verify:
        FREEZE.parent.mkdir(exist_ok=True)
        FREEZE.write_text(json.dumps(now, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        print("written", FREEZE.relative_to(ROOT))
        return 0
    frozen = json.loads(FREEZE.read_text(encoding="utf-8"))
    d = diff(frozen, now)
    for line in d:
        print("DIFF", line)
    print("FREEZE OK" if not d else f"FREEZE BROKEN: {len(d)} differences")
    return 1 if d else 0


if __name__ == "__main__":
    raise SystemExit(main())
