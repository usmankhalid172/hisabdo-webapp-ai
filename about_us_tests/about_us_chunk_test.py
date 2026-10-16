"""
Task 1 - About Us chunking + retrieval testing (Alisha Noor)

SETUP (once):
    pip install chromadb langchain-text-splitters




Uses a LOCAL database folder (./local_chroma), so it never touches the shared DB.
"""
import csv
import shutil
from pathlib import Path

import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter

# ----------------------------- CONFIG -----------------------------
ABOUT_FILE = "about_us.txt"
SOURCE_URL = "https://YOUR-WEBSITE.com/about-us"   # <-- change this
K = 3                                              # top-k results to check

CONFIGS = {
    "A": {"size": 300, "overlap": 30},
    "B": {"size": 500, "overlap": 75},
    "C": {"size": 800, "overlap": 100},
    "D": {"size": 500, "overlap": 0},   # baseline: no overlap
}

# (category, query, keyword that must appear in the correct chunk)
# EDIT these to match your real About Us text.
TESTS = [
    ("direct",       "What is your company mission?",                "mission"),
    ("direct",       "What is your company vision?",                 "vision"),
    ("paraphrase",   "What does your company stand for?",            "mission"),
    ("paraphrase",   "What are your core values?",                   "values"),
    ("keyword",      "mission",                                      "mission"),
    ("keyword",      "about company",                                "about"),
    ("short",        "who are you",                                  "about"),
    ("short",        "team",                                         "team"),
    ("long",         "Can you tell me a bit about how your company started and what you do?", "founded"),
    ("long",         "I want to know who runs the company and what experience they have",    "team"),
    ("typo_case",    "abuot us",                                     "about"),
    ("typo_case",    "COMPANY VISION",                               "vision"),
    ("related",      "founders",                                     "found"),
    ("related",      "company history",                              "history"),
    ("related",      "years of experience",                          "experience"),
]
# -------------------------------------------------------------------


def build_chunks(text, size, overlap):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=size,
        chunk_overlap=overlap,
        separators=["\n## ", "\n\n", "\n", ". ", " "],
    )
    docs = splitter.create_documents(
        [text],
        metadatas=[{"section": "about_us", "source_url": SOURCE_URL}],
    )
    for i, d in enumerate(docs):
        d.metadata["chunk_id"] = f"about_us_{i}"
    return docs


def build_collection(client, name, docs):
    if name in [c.name for c in client.list_collections()]:
        client.delete_collection(name)
    col = client.create_collection(name, metadata={"hnsw:space": "cosine"})
    col.add(
        ids=[d.metadata["chunk_id"] for d in docs],
        documents=[d.page_content for d in docs],
        metadatas=[d.metadata for d in docs],
    )
    return col


def run_tests(col, cfg):
    rows = []
    for category, query, keyword in TESTS:
        res = col.query(query_texts=[query], n_results=K)
        docs = res["documents"][0]
        dists = res["distances"][0]
        metas = res["metadatas"][0]
        rank = next((i + 1 for i, d in enumerate(docs) if keyword.lower() in d.lower()), None)
        score = round(1 - dists[0], 3) if dists else 0  # cosine similarity of top result
        source_ok = bool(metas) and metas[0].get("source_url") == SOURCE_URL
        status = "PASS" if rank == 1 else ("PARTIAL" if rank else "FAIL")
        rows.append({
            "config": cfg, "category": category, "query": query,
            "expected_keyword": keyword, "rank": rank or "-",
            "top_similarity": score, "source_ok": "Yes" if source_ok else "No",
            "status": status,
            "top_chunk_preview": (docs[0][:80].replace("\n", " ") if docs else ""),
        })
    return rows


def summarize(rows, docs):
    n = len(rows)
    ranks = [r["rank"] for r in rows]
    hit = sum(1 for x in ranks if x != "-")
    top1 = sum(1 for x in ranks if x == 1)
    mrr = sum((1 / x) for x in ranks if x != "-") / n
    avg_sim = sum(r["top_similarity"] for r in rows) / n
    cut = sum(1 for d in docs if not d.page_content.strip().endswith((".", "!", "?", ":")))
    return {
        "chunks": len(docs), "hit@k": f"{hit}/{n}", "top1": f"{top1}/{n}",
        "mrr": round(mrr, 3), "avg_sim": round(avg_sim, 3), "cut_chunks": cut,
        "_score": (top1, hit, mrr),
    }


def main():
    path = Path(ABOUT_FILE)
    if not path.exists():
        raise SystemExit(f"Put the About Us text in {ABOUT_FILE} first.")
    text = path.read_text(encoding="utf-8")

    shutil.rmtree("local_chroma", ignore_errors=True)
    client = chromadb.PersistentClient(path="local_chroma")

    all_rows, summaries = [], {}
    for cfg, p in CONFIGS.items():
        docs = build_chunks(text, p["size"], p["overlap"])
        col = build_collection(client, f"about_us_cfg_{cfg}", docs)
        rows = run_tests(col, cfg)
        all_rows += rows
        summaries[cfg] = summarize(rows, docs)
        print(f"Config {cfg} ({p['size']}/{p['overlap']}): {summaries[cfg]}")

    # CSV log
    with open("results_log.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(all_rows[0].keys()))
        w.writeheader()
        w.writerows(all_rows)

    best = max(summaries, key=lambda c: summaries[c]["_score"])
    bp = CONFIGS[best]

    # Report
    lines = [
        "# Day 4 - About Us Chunking & Retrieval Report",
        "**Owner:** Alisha Noor",
        f"**Source:** {SOURCE_URL}",
        f"**Queries tested:** {len(TESTS)} per config, top-{K} checked",
        "",
        "## Config comparison",
        "| Config | Size | Overlap | Chunks | Hit@3 | Top-1 | MRR | Avg similarity | Chunks cut mid-sentence |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for cfg, s in summaries.items():
        p = CONFIGS[cfg]
        lines.append(f"| {cfg} | {p['size']} | {p['overlap']} | {s['chunks']} | {s['hit@k']} | "
                     f"{s['top1']} | {s['mrr']} | {s['avg_sim']} | {s['cut_chunks']} |")
    lines += [
        "",
        f"## Final choice: Config {best} (chunk size {bp['size']}, overlap {bp['overlap']})",
        "Reason: highest top-1 accuracy / hit rate / MRR in the table above. "
        "(Add your own note here about chunk completeness after reading a few chunks.)",
        "",
        f"## Failed queries (Config {best})",
        "| Query | Category | Expected keyword | Status | Suspected cause |",
        "|---|---|---|---|---|",
    ]
    for r in all_rows:
        if r["config"] == best and r["status"] != "PASS":
            cause = "Typo/casing -> pass to Marsha (preprocessing)" if r["category"] == "typo_case" \
                else "Check chunk boundaries / keyword wording"
            lines.append(f"| {r['query']} | {r['category']} | {r['expected_keyword']} | {r['status']} | {cause} |")
    Path("report.md").write_text("\n".join(lines), encoding="utf-8")

    print(f"\nBest config: {best}. Wrote results_log.csv and report.md")


if __name__ == "__main__":
    main()
