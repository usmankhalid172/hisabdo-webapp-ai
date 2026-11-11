"""Cross-domain retrieval evaluation runner.
Run: python retrieval_test_bench.py --dataset domain_evaluation_dataset.jsonl
Only domains with both query labels and matching corpus documents are executed.
"""
from __future__ import annotations
import argparse,csv,json,logging,os,sys,time
from collections import defaultdict
from retrieval_methods import RetrievalEngine
from retrieval_metrics import query_metrics,aggregate_metrics

CONFIGS=[
 ("vector_proxy","LSA vector proxy (not neural dense)"),
 ("bm25","Okapi BM25"),
 ("hybrid_rrf","RRF fusion of LSA proxy + BM25"),
 ("hybrid_rerank","RRF candidates + lexical heuristic reranker"),
 ("reranked_topk","RRF candidate pool + heuristic reranker top-k"),
]

def load_jsonl(path):
    records=[]
    with open(path,encoding="utf-8") as f:
        for line_no,line in enumerate(f,1):
            if not line.strip(): continue
            try: records.append(json.loads(line))
            except json.JSONDecodeError as e: raise ValueError(f"Malformed JSONL line {line_no}: {e}")
    return records

def run(dataset_path,out_dir):
    os.makedirs(out_dir,exist_ok=True)
    records=load_jsonl(dataset_path)
    docs=defaultdict(list); queries=defaultdict(list)
    for r in records:
        if r.get("record_type")=="document": docs[r["domain"]].append(r)
        elif r.get("record_type")=="query": queries[r["domain"]].append(r)
    detail=[]; aggregates={}; domain_status={}
    for domain, qs in queries.items():
        corpus=docs.get(domain,[])
        executable=[q for q in qs if q.get("relevant_document_ids")]
        if not corpus:
            domain_status[domain]={"status":"not_executed_missing_corpus","query_records":len(qs),
                "labeled_query_records":len(executable),"corpus_documents":0}
            continue
        # Restrict execution to labels that match the supplied corpus IDs.
        doc_ids={d["document_id"] for d in corpus}
        runnable=[q for q in executable if set(q["relevant_document_ids"]) & doc_ids]
        if not runnable:
            domain_status[domain]={"status":"not_executed_no_matching_labels","query_records":len(qs),
                "labeled_query_records":len(executable),"corpus_documents":len(corpus)}
            continue
        engine=RetrievalEngine(corpus)
        domain_status[domain]={"status":"executed","query_records":len(qs),"labeled_query_records":len(executable),
            "runnable_queries":len(runnable),"corpus_documents":len(corpus)}
        for method,_ in CONFIGS:
            qrows=[]
            for q in runnable:
                try:
                    results,latency=engine.retrieve(q["query"],method,top_k=5,candidate_k=25)
                    ids=[x["document_id"] for x in results]
                    relevant=list(set(q["relevant_document_ids"]) & doc_ids)
                    met=query_metrics(ids,relevant)
                    row={"domain":domain,"query_id":q["query_id"],"query":q["query"],"method":method,
                         "retrieved_ids":"|".join(ids),"source_urls":"|".join(x["source_url"] or "" for x in results),
                         "ranked_results_json":json.dumps(results,ensure_ascii=False),
                         "latency_ms":round(latency,4),"relevant_document_ids":"|".join(relevant),
                         "label_basis":q.get("label_basis",""),"label_type":q.get("label_type",""),
                         "reranker":results[0]["reranker"] if results else "none","error":"","metrics":met}
                    detail.append(row); qrows.append(row)
                except Exception as e:
                    row={"domain":domain,"query_id":q.get("query_id"),"query":q.get("query"),"method":method,
                         "retrieved_ids":"","source_urls":"","ranked_results_json":"[]","latency_ms":None,
                         "relevant_document_ids":"|".join(q.get("relevant_document_ids",[])),
                         "label_basis":q.get("label_basis",""),"label_type":q.get("label_type",""),
                         "reranker":"none","error":repr(e),"metrics":query_metrics([],q.get("relevant_document_ids",[]))}
                    detail.append(row); qrows.append(row)
            aggregates[(domain,method)]=aggregate_metrics(qrows)
    # per-query CSV with flattened metrics
    fields=["domain","query_id","query","method","retrieved_ids","source_urls","ranked_results_json","latency_ms",
            "relevant_document_ids","label_basis","label_type","reranker","error",
            "Recall@1","Recall@3","Recall@5","Precision@1","Precision@3","Precision@5",
            "HitRate@1","HitRate@3","HitRate@5","MRR"]
    with open(os.path.join(out_dir,"per_query_results.csv"),"w",newline="",encoding="utf-8-sig") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
        for r in detail:
            flat={k:r.get(k) for k in fields}
            flat.update(r["metrics"]); w.writerow(flat)
    metric_rows=[]
    for (domain,method),m in aggregates.items(): metric_rows.append({"domain":domain,"method":method,**m})
    # overall aggregate is macro across all runnable blog queries (single corpus domain currently)
    for method,_ in CONFIGS:
        subset=[r for r in detail if r["method"]==method]
        if subset: metric_rows.append({"domain":"OVERALL_EXECUTED","method":method,**aggregate_metrics(subset)})
    with open(os.path.join(out_dir,"cross_domain_metrics.csv"),"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(metric_rows[0]) if metric_rows else ["domain","method"])
        w.writeheader(); w.writerows(metric_rows)
    summary={"domain_status":domain_status,"configurations":[{"id":a,"description":b} for a,b in CONFIGS],
             "aggregate_metrics":{f"{d}::{m}":v for (d,m),v in aggregates.items()},
             "execution_notes":{"dense_neural":"NOT RUN: sentence-transformers package/model unavailable in this environment; LSA proxy is separately labelled",
               "reranker":"heuristic lexical reranker fallback; NOT a cross-encoder",
               "corpus_scope":"only Blog & News corpus was supplied as actual document text; other domains retained in dataset but skipped",
               "historical_results":"not merged into newly executed metrics"}}
    with open(os.path.join(out_dir,"cross_configuration_metrics.json"),"w",encoding="utf8") as f: json.dump(summary,f,indent=2,ensure_ascii=False)
    return summary,len(detail)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--dataset",default="domain_evaluation_dataset.jsonl")
    ap.add_argument("--out-dir",default=".")
    args=ap.parse_args()
    logging.basicConfig(level=logging.INFO,format="%(asctime)s %(levelname)s %(message)s")
    summary,n=run(args.dataset,args.out_dir)
    print(f"records loaded; newly executed per-query configuration rows={n}")
    for d,s in summary["domain_status"].items(): print(f"{d}: {s['status']} (queries={s['query_records']}, corpus={s['corpus_documents']})")
    print("dense_neural=NOT_RUN; vector_proxy=LSA; reranker=heuristic_fallback")
if __name__=="__main__": main()
