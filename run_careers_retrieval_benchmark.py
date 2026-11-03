import json, numpy as np
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
ROOT=Path(__file__).resolve().parent
chunks=json.loads((ROOT/"benchmark_source/chunks.json").read_text(encoding="utf-8"))
queries=['What jobs is XICTEK hiring for?', 'Is there a senior developer position?', 'What technologies are used for the mobile app role?', 'Does XICTEK need someone for cloud architecture?', 'Is there a UI/UX design position?', 'What internship opportunities are available?', 'What is the XICTEK work culture like?', 'What are the requirements for the internship?', 'Is the old 2026 HisabDo internship still open?', 'What skills should a cloud architect have?']
relevant=[{'faq-75', 'faq-76', 'faq-74', 'faq-78', 'faq-77'}, {'faq-75'}, {'faq-76'}, {'faq-77'}, {'faq-78'}, {'faq-89', 'faq-80'}, {'faq-82', 'faq-83'}, {'faq-93'}, {'faq-185', 'faq-184', 'faq-195'}, {'faq-77'}]
texts=[c.get("title","")+" "+c.get("text","") for c in chunks]
v=TfidfVectorizer(ngram_range=(1,2),stop_words="english",sublinear_tf=True); X=v.fit_transform(texts)
for name,filtered in [("Global TF-IDF baseline",False),("Careers metadata-filtered TF-IDF",True)]:
 h=[];p=[];rr=[]
 for i,q in enumerate(queries):
  scores=cosine_similarity(v.transform([q]),X).ravel(); allowed=[]
  for j,c in enumerate(chunks):
   u=c.get("url","")
   if not filtered or (i==8 and u=="https://hisabdo.app/careers") or (i!=8 and u in ("https://xicteksystems.com/careers","https://xicteksystems.com/careers/internship")): allowed.append(j)
  top=sorted(allowed,key=lambda j:scores[j],reverse=True)[:5]; ranks=[r for r,j in enumerate(top,1) if chunks[j]["id"] in relevant[i]]
  h.append(bool(ranks));p.append(sum(chunks[j]["id"] in relevant[i] for j in top)/5);rr.append(1/min(ranks) if ranks else 0)
 print(name,"Hit Rate@5",round(float(np.mean(h)),3),"Precision@5",round(float(np.mean(p)),3),"MRR@5",round(float(np.mean(rr)),3))
