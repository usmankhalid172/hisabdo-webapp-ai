"""Retrieval implementations for the Department 4 offline benchmark.

BM25 is implemented directly (Okapi BM25) to avoid a mandatory rank_bm25 dependency.
LSA is a clearly labelled lexical latent-semantic proxy, NOT a neural dense embedding.
A cross-encoder is only used if explicitly configured and available; the benchmark
uses a transparent lexical heuristic fallback otherwise.
"""
from __future__ import annotations
import re, math, time
from collections import Counter, defaultdict
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import normalize

TOKEN_RE = re.compile(r"(?u)\b\w+\b")

def tokenize(text):
    return TOKEN_RE.findall((text or "").lower())

class RetrievalEngine:
    def __init__(self, documents, random_state=17):
        self.documents = documents
        self.ids = [d["document_id"] for d in documents]
        self.texts = [(d.get("title","") + ". " + d.get("text","")).strip() for d in documents]
        if not documents: raise ValueError("Corpus contains no documents")
        self.tfidf = TfidfVectorizer(ngram_range=(1,2), sublinear_tf=True, stop_words="english")
        self.X = self.tfidf.fit_transform(self.texts)
        n_features=self.X.shape[1]
        self.svd=None; self.Z=None
        if len(documents)>=3 and n_features>=3:
            n_components=max(2,min(40,len(documents)-1,n_features-1))
            self.svd=TruncatedSVD(n_components=n_components,random_state=random_state)
            self.Z=normalize(self.svd.fit_transform(self.X))
        self.cv=CountVectorizer(stop_words="english")
        self.C=self.cv.fit_transform(self.texts).tocsr()
        self.df=np.asarray((self.C>0).sum(axis=0)).ravel()
        self.N=self.C.shape[0]
        self.dl=np.asarray(self.C.sum(axis=1)).ravel()
        self.avgdl=float(self.dl.mean()) if self.N else 0.0
        self.idf=np.log(1+(self.N-self.df+0.5)/(self.df+0.5))

    def vector_proxy_scores(self, query):
        if self.svd is None: return np.zeros(self.N)
        q=self.tfidf.transform([query])
        return self.Z @ normalize(self.svd.transform(q)).ravel()

    def bm25_scores(self, query, k1=1.5, b=0.75):
        scores=np.zeros(self.N,dtype=float)
        analyzer=self.cv.build_analyzer()
        for term in analyzer(query):
            j=self.cv.vocabulary_.get(term)
            if j is None: continue
            col=self.C[:,j].toarray().ravel()
            denom=col+k1*(1-b+b*self.dl/(self.avgdl or 1))
            scores += self.idf[j]*col*(k1+1)/(denom+1e-12)
        return scores

    @staticmethod
    def _rank(scores):
        return np.argsort(-np.asarray(scores),kind="stable").tolist()

    @staticmethod
    def _rrf(rankings, rrf_k=60):
        fused=defaultdict(float)
        for ranking in rankings:
            seen=set()
            for rank,doc_id in enumerate(ranking,1):
                if doc_id in seen: continue
                seen.add(doc_id)
                fused[doc_id]+=1.0/(rrf_k+rank)
        return fused

    def retrieve(self, query, method, top_k=5, candidate_k=20, reranker="heuristic"):
        started=time.perf_counter()
        vec=self.vector_proxy_scores(query)
        bm=self.bm25_scores(query)
        if method=="vector_proxy":
            scores=vec; ranked=self._rank(scores)
            result=[(self.ids[i],float(scores[i]),"lsa_vector_proxy") for i in ranked[:top_k]]
        elif method=="bm25":
            scores=bm; ranked=self._rank(scores)
            result=[(self.ids[i],float(scores[i]),"bm25") for i in ranked[:top_k]]
        elif method in ("hybrid_rrf","hybrid_rerank","reranked_topk"):
            rv=[self.ids[i] for i in self._rank(vec)]
            rb=[self.ids[i] for i in self._rank(bm)]
            fused=self._rrf([rv,rb])
            effective_candidate_k=max(top_k, candidate_k//2) if method=="reranked_topk" else candidate_k
            candidates=sorted(fused,key=lambda x:(-fused[x],x))[:effective_candidate_k]
            # Deduplicate IDs and preserve all source URLs/provenance.
            by_id={d["document_id"]:d for d in self.documents}
            candidates=list(dict.fromkeys(candidates))
            if method=="hybrid_rrf":
                chosen=candidates[:top_k]
                result=[(d,float(fused[d]),"rrf") for d in chosen]
            else:
                if reranker=="cross_encoder":
                    try:
                        from sentence_transformers import CrossEncoder
                        # Explicitly instantiate only when caller requested it.
                        ce=CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
                        pairs=[(query,(by_id[d].get("title","")+" "+by_id[d].get("text",""))) for d in candidates]
                        rs=ce.predict(pairs)
                        ranked=sorted(zip(candidates,rs),key=lambda x:-float(x[1]))
                        tag="cross_encoder"
                    except Exception:
                        ranked=self._heuristic_rerank(query,candidates,by_id,fused)
                        tag="heuristic_fallback"
                else:
                    ranked=self._heuristic_rerank(query,candidates,by_id,fused)
                    tag="heuristic_fallback"
                result=[(d,float(score),tag) for d,score in ranked[:top_k]]
        else:
            raise ValueError(f"Unknown retrieval method: {method}")
        elapsed=(time.perf_counter()-started)*1000
        return [{"document_id":d,"score":s,"reranker":tag,
                 "source_url":next((x.get("source_url") for x in self.documents if x["document_id"]==d),None),
                 "rank":i+1} for i,(d,s,tag) in enumerate(result)],elapsed

    def _heuristic_rerank(self, query, candidates, by_id, fused):
        q=set(tokenize(query))
        rows=[]
        for doc_id in candidates:
            doc=by_id[doc_id]
            title=set(tokenize(doc.get("title","")))
            body=set(tokenize(doc.get("text","")))
            overlap=len(q & (title|body))/(len(q) or 1)
            title_overlap=len(q & title)/(len(q) or 1)
            score=0.55*overlap+0.25*title_overlap+0.20*fused[doc_id]
            rows.append((doc_id,score))
        return sorted(rows,key=lambda x:(-x[1],x[0]))
