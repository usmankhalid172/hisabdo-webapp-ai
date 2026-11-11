"""Blog & News retrieval benchmark: vector vs lexical vs hybrid, filters, threshold sweep.
Usage: python blog_retrieval_benchmark.py [path/to/blog-kb-cleaned-consolidated.md]
Optional: pip install sentence-transformers  -> adds real MiniLM (all-MiniLM-L6-v2) rows.
Always available (sklearn only): TF-IDF, BM25, LSA (SVD semantic proxy), hybrids.
"""
import re, sys, json, math, csv
from collections import defaultdict
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import normalize

KB = sys.argv[1] if len(sys.argv) > 1 else "blog-kb-cleaned-consolidated.md"

# ---------- corpus ----------
raw = open(KB, encoding="utf-8").read()
arts = []
for blk in re.split(r"(?m)^---\s*$\n\s*^---\s*$\n", raw):
    m = re.match(r"article_id:.*?\n---\s*\n(.*)", blk, re.S)
    if not m: continue
    head = blk[:blk.index("\n---")]
    meta = dict(l.split(": ", 1) for l in head.split("\n") if ": " in l)
    meta["title"] = meta["title"].strip('"')
    meta["text"] = re.sub(r"\n---\s*$", "", m.group(1)).strip()
    arts.append(meta)
ids = [a["article_id"] for a in arts]
CAT = {"ARTIFICIAL INTELLIGENCE": "AI", "AI AND AUTOMATION": "AI", "MOBILE APPS": "MOBILE",
       "MOBILE DEVELOPMENT": "MOBILE", "Uncategorized": "SOFTWARE DEVELOPMENT", "CLOUD": "CLOUD",
       "ERP": "ERP", "SAAS": "SAAS"}
for a in arts:
    a["cat_norm"] = CAT.get(a["category"], a["category"])
docs = [a["title"] + ". " + a["text"] for a in arts]
print(f"Loaded {len(arts)} articles")

# ---------- queries (24 from blog-retrieval-evaluation.md + held-out P-set + negatives) ----------
POS = {
"F1":("how much does custom software cost in Pakistan",["software-development-cost-pakistan","custom-software-development-guide"]),
"F2":("what is the cost to build a mobile app",["mobile-app-cost-guide","startup-mobile-apps"]),
"F3":("best AI chatbot for customer support",["ai-chatbot-development","ai-customer-support"]),
"F4":("azure vs aws which is better",["azure-development-services"]),
"F5":("how to choose software development company",["software-development-company-pakistan","web-development-company-pakistan"]),
"S1":("custom software development guide",["custom-software-development-guide","custom-software-development"]),
"S2":("saas product development from MVP",["saas-product-development","saas-development-services","mvp-development-guide"]),
"S3":("next.js development services",["nextjs-development-services","react-development-services"]),
"S4":("flutter cross platform mobile app",["flutter-app-development","cross-platform-development"]),
"S5":("agile software development process",["agile-software-development","software-development-process"]),
"N1":("How Do I Build A ChatBot??",["ai-chatbot-development"]),
"N2":("ios iphone app development",["ios-app-development"]),
"N3":("progressive web apps pwa",["progressive-web-apps"]),
"N4":("ERP system automation",["erp-software-development","business-process-automation","ai-in-erp-systems"]),
"A1":("ai for small business",["ai-for-smes"]),
"A2":("startup mvp",["mvp-development-guide","startup-software-development","startup-mobile-apps"]),
"H1":("we need to put our internal tools online so employees can use them from anywhere",["portal-development","enterprise-web-applications"]),
"H2":("our checkout flow is slow on mobile and people abandon carts",["ecommerce-development","website-performance-optimization"]),
"H3":("we want to add a smart assistant that answers questions from our documentation",["ai-chatbot-development","ai-customer-support","generative-ai-applications"]),
"H4":("how do we make sure our app doesn't get hacked",["mobile-app-security"]),
"H5":("we have an old system that nobody understands and we want to modernize it",["digital-transformation-services","software-maintenance-services"]),
"H6":("subscribe users monthly and charge them recurring fees",["saas-development-services","saas-product-development"]),
"H7":("continuous deployment pipeline with automated tests",["software-development-process","agile-software-development"]),
"H8":("what does it take to launch a startup product quickly",["mvp-development-guide","startup-software-development","startup-mobile-apps"]),
# held-out probes from the weak-question analysis (not used to tune anything)
"P2":("how do i make my website load faster",["website-performance-optimization"]),
"P6":("how to build a chatobt for my website",["ai-chatbot-development"]),
"P7":("erp",["erp-software-development","ai-in-erp-systems"]),
"P8":("what are common mistakes in software development",["custom-software-development-guide","software-development-process"]),
"P9":("AI For SMEs",["ai-for-smes"]),
"P10":("how much does erp implementation cost",["erp-software-development","software-development-cost-pakistan"]),
}
NEG = {  # no answer exists in the corpus -> system should abstain
"P1":"what is xictek's refund policy for software development projects",
"P4":"should i use postgresql or mongodb for my project",
"X1":"do you have an article about quantum computing",
"X2":"what is the weather in Lahore today",
"X3":"who won the cricket world cup",
"X4":"how do i bake sourdough bread",
"X5":"what is xictek's office phone number",
"X6":"tell me about blockchain smart contracts",
"X7":"best laptop for gaming under 1000 dollars",
"X8":"how do i file my income tax return",
}
qids = list(POS); pos_q = [POS[q][0] for q in qids]; neg_ids = list(NEG); neg_q = [NEG[q] for q in neg_ids]
gold = {q: set(POS[q][1]) for q in qids}
missing = {g for s in gold.values() for g in s} - set(ids)
assert not missing, missing

# ---------- retrievers: each returns score vector over docs ----------
tf = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, stop_words="english", min_df=1)
X_tf = tf.fit_transform(docs)
def s_tfidf(q): return (X_tf @ tf.transform([q]).T).toarray().ravel()

cv = CountVectorizer(stop_words="english"); C = cv.fit_transform(docs).tocsc()
N = C.shape[0]; dl = np.asarray(C.sum(1)).ravel(); avg = dl.mean()
df = np.asarray((C > 0).sum(0)).ravel(); idf = np.log(1 + (N - df + .5) / (df + .5))
def s_bm25(q, k1=1.5, b=.75):
    sc = np.zeros(N)
    for t in cv.build_analyzer()(q):
        j = cv.vocabulary_.get(t)
        if j is None: continue
        col = C[:, j].toarray().ravel()
        sc += idf[j] * col * (k1 + 1) / (col + k1 * (1 - b + b * dl / avg))
    return sc

svd = TruncatedSVD(n_components=40, random_state=0)
Z = normalize(svd.fit_transform(X_tf))
def s_lsa(q): return Z @ normalize(svd.transform(tf.transform([q]))).ravel()

SEM = {"lsa": s_lsa}; sem_name = "lsa"
try:
    from sentence_transformers import SentenceTransformer
    st = SentenceTransformer("all-MiniLM-L6-v2")
    E = st.encode(docs, normalize_embeddings=True)
    SEM["minilm"] = lambda q: E @ st.encode(q, normalize_embeddings=True); sem_name = "minilm"
    print("MiniLM available: using it as the vector method")
except Exception:
    print("MiniLM NOT available: using LSA as the vector proxy. Re-run with sentence-transformers for real numbers.")
s_vec = SEM[sem_name]

def mm(x):
    lo, hi = x.min(), x.max()
    return (x - lo) / (hi - lo) if hi > lo else np.zeros_like(x)
def rrf(*vs, k=60):
    f = np.zeros(N)
    for v in vs:
        for r, i in enumerate(np.argsort(-v), 1): f[i] += 1 / (k + r)
    return f
METHODS = {
 "tfidf": s_tfidf, "bm25": s_bm25, "vector": s_vec,
 "hybrid_a0.5": lambda q: .5 * mm(s_vec(q)) + .5 * mm(s_bm25(q)),
 "hybrid_a0.7": lambda q: .7 * mm(s_vec(q)) + .3 * mm(s_bm25(q)),
 "hybrid_rrf": lambda q: rrf(s_vec(q), s_bm25(q)),
}

def ranked(score, mask=None):
    order = [i for i in np.argsort(-score) if mask is None or mask[i]]
    return order
def metrics(fn, ks=(1, 3, 5, 10), mask_fn=None):
    out = {}
    for k in ks:
        hit = []; rec = []; rr = []; prec = []
        for q, qid in zip(pos_q, qids):
            sc = fn(q); order = ranked(sc, mask_fn(qid) if mask_fn else None)[:k]
            top = [ids[i] for i in order]; g = gold[qid]; inter = g & set(top)
            hit.append(bool(inter)); rec.append(len(inter) / len(g)); prec.append(len(inter) / k)
            rr.append(next((1 / (r + 1) for r, d in enumerate(top) if d in g), 0))
        out[k] = dict(hit=np.mean(hit), recall=np.mean(rec), prec=np.mean(prec), mrr=np.mean(rr))
    return out

rows = []
print("\n== Method comparison (30 positive queries) ==")
print(f"{'method':14}{'k':>3}{'Hit':>7}{'Recall':>8}{'MRR':>7}")
for name, fn in METHODS.items():
    m = metrics(fn)
    for k, v in m.items():
        rows.append([name, "none", k, round(v["hit"], 3), round(v["recall"], 3), round(v["prec"], 3), round(v["mrr"], 3)])
        if k in (1, 3, 5): print(f"{name:14}{k:>3}{v['hit']:7.3f}{v['recall']:8.3f}{v['mrr']:7.3f}")

# ---------- metadata filtering ----------
KW = {"AI": "ai chatbot assistant generative machine learning intelligence",
      "MOBILE": "mobile app ios android flutter iphone",
      "WEB DEVELOPMENT": "web website react next.js pwa ecommerce portal checkout",
      "SOFTWARE DEVELOPMENT": "software agile mvp startup custom process cost",
      "ERP": "erp"}
def predict_cat(q):
    ql = q.lower(); best, bs = None, 0
    for c, kws in KW.items():
        s = sum(w in ql for w in kws.split())
        if s > bs: best, bs = c, s
    return best
cat_of = {i: a["cat_norm"] for i, a in enumerate(arts)}
def oracle_mask(qid):  # best case: category of the first gold article
    c = cat_of[ids.index(sorted(gold[qid])[0])]
    return [cat_of[i] == c for i in range(N)]
def pred_mask(qid):
    c = predict_cat(POS[qid][0])
    return [True] * N if c is None else [cat_of[i] == c for i in range(N)]
print("\n== Metadata category filter (hybrid_a0.5, k=3) ==")
fn = METHODS["hybrid_a0.5"]
filt_res = {}
for lab, mf in [("no filter", None), ("predicted category", pred_mask), ("oracle category (upper bound)", oracle_mask)]:
    v = metrics(fn, ks=(3,), mask_fn=mf)[3]; filt_res[lab] = v
    rows.append(["hybrid_a0.5", lab, 3, round(v["hit"], 3), round(v["recall"], 3), round(v["prec"], 3), round(v["mrr"], 3)])
    print(f"{lab:32} Hit@3={v['hit']:.3f} Recall@3={v['recall']:.3f} MRR={v['mrr']:.3f}")
dates = {a["published_date"] for a in arts}
print(f"\nDate filter: not testable - {len(dates)} distinct published_date value(s): {dates}")

with open("hybrid_comparison_log.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["method", "filter", "k", "hit", "recall", "precision", "mrr"]); w.writerows(rows)

# ---------- per-query log for hybrid vs vector ----------
pq = []
for q, qid in zip(pos_q, qids):
    r = {"qid": qid, "query": q, "gold": "|".join(sorted(gold[qid]))}
    for name in ("vector", "bm25", "hybrid_a0.5"):
        sc = METHODS[name](q); top = [ids[i] for i in ranked(sc)[:3]]
        r[name + "_top3"] = "|".join(top)
        r[name + "_hit3"] = int(bool(gold[qid] & set(top)))
        r[name + "_top1_score"] = round(float(mm(sc)[np.argmax(sc)]), 3) if name != "x" else 0
    pq.append(r)
with open("per_query_log.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(pq[0])); w.writeheader(); w.writerows(pq)

# ---------- threshold sweep: abstain when top-1 score < t ----------
# Score used: raw TF-IDF cosine and raw vector cosine (absolute, comparable across queries).
def top1(fn, q): sc = fn(q); i = int(np.argmax(sc)); return float(sc[i]), ids[i]
def sweep(fn, grid):
    P = [(top1(fn, q), qid) for q, qid in zip(pos_q, qids)]
    Ng = [top1(fn, q) for q in neg_q]
    res = []
    for t in grid:
        ans = [(s >= t, gold[qid] and top1id in gold[qid]) for ((s, top1id), qid) in P]
        tp = sum(a and c for a, c in ans)              # answered correctly (top-1)
        fp_pos = sum(a and not c for a, c in ans)      # answered wrongly
        fp_neg = sum(s >= t for s, _ in Ng)            # answered an unanswerable question
        abst_pos = sum(not a for a, _ in ans)          # wrongly refused
        answered = tp + fp_pos + fp_neg
        prec = tp / answered if answered else 1.0
        rec = tp / len(P)
        f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0
        res.append(dict(threshold=round(t, 3), answered_correct=tp, answered_wrong=fp_pos,
                        false_accept_neg=f"{fp_neg}/{len(Ng)}", wrongly_refused=abst_pos,
                        precision=round(prec, 3), recall=round(rec, 3), f1=round(f1, 3)))
    return res
sweeps = {"tfidf_cosine": (s_tfidf, np.arange(0.0, 0.41, 0.025)), "vector_cosine": (s_vec, np.arange(0.0, 0.91, 0.05))}
best_cfg = {}
for name, (fn, grid) in sweeps.items():
    r = sweep(fn, grid)
    with open(f"threshold_sweep_{name}.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(r[0])); w.writeheader(); w.writerows(r)
    best = max(r, key=lambda x: (x["f1"], x["threshold"]))
    best_cfg[name] = best
    print(f"\n== Threshold sweep: {name} ==")
    for x in r[::2]: print(x)
    print("BEST (max F1):", best)
    # score distributions
    ps = [top1(fn, q)[0] for q in pos_q]; ns = [top1(fn, q)[0] for q in neg_q]
    print(f"  top-1 score positives: median={np.median(ps):.3f} min={min(ps):.3f} | negatives: median={np.median(ns):.3f} max={max(ns):.3f}")

# ---------- duplicate audit ----------
print("\n== 'Duplicate' audit: cosine(article, claimed primary) vs typical article pair ==")
idx = {d: i for i, d in enumerate(ids)}
Xn = normalize(X_tf)
sims = []; bad = 0
for a in arts:
    p = a.get("duplicate_of")
    if p and p != "null":
        s = float(Xn[idx[a["article_id"]]].multiply(Xn[idx[p]]).sum()); sims.append(s)
allp = (Xn @ Xn.T).toarray(); allm = allp[np.triu_indices(N, 1)].mean()
print(f"  marked duplicates: {len(sims)} | mean TF-IDF cosine to claimed primary = {np.mean(sims):.3f} (max {max(sims):.3f}) | mean over ALL pairs = {allm:.3f}")
print(f"  pairs with cosine >= 0.9 (true near-dup): {sum(s >= .9 for s in sims)}")
json.dump({"sem_method": sem_name, "best": best_cfg, "filters": {k: {kk: float(vv) for kk, vv in v.items()} for k, v in filt_res.items()}},
          open("benchmark_summary.json", "w"), indent=1, default=float)