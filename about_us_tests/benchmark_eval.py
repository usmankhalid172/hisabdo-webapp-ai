"""
Benchmark evaluation - About Us & Company Overview (Alisha Noor)

Needs in the same folder: about_us.txt, about_us_prompt.py, benchmark_testset.csv
Run:  python benchmark_eval.py
Output: results_eval.csv + summary in the terminal

Checks per question:  ACCURACY, TONE, SOURCE LINK  (PASS/FAIL each)
"""
import csv
import re
import sys

from about_us_prompt import FALLBACK, OFFICIAL_URL, check_answer

sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # Urdu-safe on Windows

SIM_MIN = 0.30   # baseline only: below this similarity -> fallback (tune if needed)


# ---------------- 1. THE SYSTEM BEING TESTED ----------------
_col = None

def baseline_answer(question):
    """Retrieval-only baseline (no LLM): returns the best chunk + source link."""
    global _col
    if _col is None:
        import chromadb
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        text = open("about_us.txt", encoding="utf-8").read()
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500, chunk_overlap=75,
            separators=["\n## ", "\n\n", "\n", ". ", " "])
        chunks = splitter.split_text(text)
        _col = chromadb.Client().create_collection("eval", metadata={"hnsw:space": "cosine"})
        _col.add(ids=[str(i) for i in range(len(chunks))], documents=chunks)
    res = _col.query(query_texts=[question], n_results=1)
    if 1 - res["distances"][0][0] < SIM_MIN:
        return FALLBACK
    chunk = res["documents"][0][0].replace("##", "").strip()
    return check_answer(f"{chunk}\nSource: {OFFICIAL_URL}")


def get_answer(question):
    # TODO: to test your team's real chatbot, call it here instead, e.g.
    #   return answer_question(question, chunks, your_llm_function)
    return baseline_answer(question)


# ---------------- 2. THE THREE CHECKS ----------------
BAD_WORDS = ["bro", "yaar", "lol", "dude", "stupid", "idiot", "guaranteed",
             "best company", "number one", "#1", "100%", "world-class"]

def check_accuracy(answer, expected, should_answer):
    a = answer.lower()
    if should_answer == "no":   # must refuse, and must not invent numbers/years
        refused = "could not find" in a
        invented = bool(re.search(r"\d", answer.replace(OFFICIAL_URL, "")))
        return refused and not invented
    if "could not find" in a:   # refused something it should know
        return False
    return any(k.strip().lower() in a for k in expected.split("|"))

def check_tone(answer):
    a = answer.lower()
    if any(w in a for w in BAD_WORDS):          return False   # slang / boasting
    if re.search(r"[\U00010000-\U0010ffff]", answer): return False   # emoji
    if len(answer.split()) > 120:               return False   # too long
    letters = [c for c in answer if c.isalpha()]
    if letters and sum(c.isupper() for c in letters) / len(letters) > 0.5: return False
    return True

def check_source(answer):
    urls = [u.rstrip(".,") for u in re.findall(r"https?://[^\s)]+", answer)]
    return OFFICIAL_URL in urls and all(u == OFFICIAL_URL for u in urls)


# ---------------- 3. RUN ----------------
def run(answer_fn=get_answer):
    tests = list(csv.DictReader(open("benchmark_testset.csv", encoding="utf-8-sig")))
    out = []
    for t in tests:
        ans = answer_fn(t["question"])
        acc = check_accuracy(ans, t["expected_any_of"], t["should_answer"])
        tone = check_tone(ans)
        src = check_source(ans)
        out.append({**t, "answer": ans.replace("\n", " "),
                    "accuracy": "PASS" if acc else "FAIL",
                    "tone": "PASS" if tone else "FAIL",
                    "source": "PASS" if src else "FAIL",
                    "overall": "PASS" if acc and tone and src else "FAIL"})
    with open("results_eval.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
        w.writeheader(); w.writerows(out)

    n = len(out)
    print(f"\nQuestions: {n}")
    for m in ["accuracy", "tone", "source", "overall"]:
        print(f"  {m:9}: {sum(r[m]=='PASS' for r in out)}/{n}")
    print("\nBy question type (overall):")
    for ty in dict.fromkeys(r["type"] for r in out):
        rs = [r for r in out if r["type"] == ty]
        print(f"  {ty:13}: {sum(r['overall']=='PASS' for r in rs)}/{len(rs)}")
    fails = [r["id"] for r in out if r["overall"] == "FAIL"]
    print("\nFailed IDs:", ", ".join(fails) or "none")
    print("Saved results_eval.csv")

if __name__ == "__main__":
    run()