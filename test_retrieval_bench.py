import json, os, tempfile
import pytest
from retrieval_metrics import query_metrics,aggregate_metrics
from retrieval_methods import RetrievalEngine
from retrieval_test_bench import load_jsonl,run

def tiny_docs():
    return [
      {"document_id":"a","title":"Apple care","text":"Apple fruit storage and orchard","source_url":"https://x/a"},
      {"document_id":"b","title":"Banana bread","text":"Banana baking recipe","source_url":"https://x/b"},
      {"document_id":"c","title":"Apple devices","text":"Apple phone and computer support","source_url":"https://x/c"},
    ]

def test_dataset_loading_and_malformed():
    with tempfile.TemporaryDirectory() as d:
        p=os.path.join(d,"x.jsonl")
        open(p,"w").write('{"record_type":"query"}\n')
        assert len(load_jsonl(p))==1
        open(p,"w").write("{bad json}\n")
        with pytest.raises(ValueError): load_jsonl(p)

def test_dense_vector_proxy_returns_ranked_results():
    e=RetrievalEngine(tiny_docs())
    r,_=e.retrieve("apple orchard", "vector_proxy", 2)
    assert len(r)==2 and r[0]["document_id"] in {"a","c"}

def test_bm25_retrieval():
    e=RetrievalEngine(tiny_docs())
    r,_=e.retrieve("banana baking", "bm25", 2)
    assert r[0]["document_id"]=="b"

def test_hybrid_fusion_and_deduplication():
    e=RetrievalEngine(tiny_docs())
    fused=e._rrf([["a","b","a"],["a","c"]])
    assert list(fused).count("a")==1
    r,_=e.retrieve("apple", "hybrid_rrf", 3)
    assert len({x["document_id"] for x in r})==len(r)

def test_reranking_order_and_provenance():
    e=RetrievalEngine(tiny_docs())
    r,_=e.retrieve("apple orchard", "hybrid_rerank", 3)
    assert r[0]["document_id"]=="a"
    assert r[0]["source_url"]=="https://x/a"
    assert r[0]["reranker"]=="heuristic_fallback"

def test_metrics_recall_precision_mrr_hit():
    m=query_metrics(["x","b","c"],["b","c"],(1,3))
    assert m["Recall@3"]==1
    assert m["Precision@3"]==pytest.approx(2/3)
    assert m["MRR"]==0.5
    assert m["HitRate@1"]==0

def test_empty_retrieval_and_missing_labels():
    m=query_metrics([],[],(1,3,5))
    assert m["MRR"] is None
    assert m["Precision@5"]==0
    assert m["Recall@5"] is None
    a=aggregate_metrics([{"metrics":m}],(1,3,5))
    assert a["labeled_query_count"]==0

def test_cross_domain_skip_and_report_generation():
    with tempfile.TemporaryDirectory() as d:
        p=os.path.join(d,"dataset.jsonl")
        rows=[
          {"record_type":"document","domain":"D1","document_id":"a","title":"alpha","text":"alpha","source_url":"u"},
          {"record_type":"query","domain":"D1","query_id":"q1","query":"alpha","relevant_document_ids":["a"]},
          {"record_type":"query","domain":"D2","query_id":"q2","query":"missing","relevant_document_ids":["z"]},
        ]
        with open(p,"w") as f:
            for x in rows:f.write(json.dumps(x)+"\n")
        s,n=run(p,d)
        assert n==5
        assert s["domain_status"]["D1"]["status"]=="executed"
        assert s["domain_status"]["D2"]["status"]=="not_executed_missing_corpus"
        assert os.path.exists(os.path.join(d,"per_query_results.csv"))
        assert os.path.exists(os.path.join(d,"cross_domain_metrics.csv"))
        assert os.path.exists(os.path.join(d,"cross_configuration_metrics.json"))

def test_reranked_topk_pipeline():
    e=RetrievalEngine(tiny_docs())
    r,_=e.retrieve("banana", "reranked_topk", 2, candidate_k=3)
    assert r and r[0]["document_id"]=="b"
