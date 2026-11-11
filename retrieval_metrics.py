"""Standard ranked retrieval metrics; precision denominator is fixed at K."""
def query_metrics(ranked_ids, relevant_ids, ks=(1,3,5)):
    ranked_ids=list(ranked_ids or [])
    relevant=set(relevant_ids or [])
    out={}
    for k in ks:
        top=ranked_ids[:k]
        hits=sum(1 for d in top if d in relevant)
        out[f"Recall@{k}"]=hits/len(relevant) if relevant else None
        out[f"Precision@{k}"]=hits/k
        out[f"HitRate@{k}"]=int(hits>0)
    rr=0.0
    if relevant:
        for i,d in enumerate(ranked_ids,1):
            if d in relevant:
                rr=1.0/i; break
    out["MRR"]=rr if relevant else None
    return out

def aggregate_metrics(rows, ks=(1,3,5)):
    """Macro-average per-query metrics; queries without labels are excluded."""
    labeled=[r for r in rows if r.get("relevant_document_ids")]
    result={"query_count":len(rows),"labeled_query_count":len(labeled)}
    for metric in [f"{m}@{k}" for k in ks for m in ("Recall","Precision","HitRate")]+["MRR"]:
        vals=[r["metrics"].get(metric) for r in labeled if r["metrics"].get(metric) is not None]
        result[metric]=sum(vals)/len(vals) if vals else None
    return result
