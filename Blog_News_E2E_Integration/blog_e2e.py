"""Configurable Blog & News end-to-end test runner.
Requires a running chatbot API and real approved article URLs to produce live results.
"""
import csv, html, json, os, re, sys, uuid
from datetime import datetime, timezone
from urllib.parse import urlparse
import requests
from config import BASE_URL, CHAT_PATH, DOMAIN, PREFIXES, TEXT_FIELD, HISTORY_MODE, TIMEOUT

URL_RE=re.compile(r'https?://[^\s)\]>"\']+')
REFUSAL=re.compile(r"could not find|couldn't find|can't find|cannot find|don't have|do not have|no (article|post|information)|not available|not covered",re.I)
STOP=set('about their there which would should could these those through between because article articles please following without within during before after other others years where while being having doing really'.split())
SESSION=requests.Session(); SESSION.headers.update({'User-Agent':'XICTEK-Blog-News-E2E/1.0'})
CACHE={}

# Replace sample questions with questions grounded in your real blog/news corpus.
CONVERSATIONS=[
 {'id':'B01','kind':'normal','turns':['What topics are covered in the XICTEK blog?','Can you summarize one relevant article?','What is the source for that summary?']},
 {'id':'B02','kind':'normal','turns':['Do you have an article about cloud solutions?','Summarize the article in two sentences.','Are there other articles on this topic?']},
 {'id':'N01','kind':'normal','turns':['What recent news or updates are available from XICTEK Systems?','Are there earlier updates on the same subject?']},
 {'id':'OOS01','kind':'out-of-scope','turns':['Do you have an article about quantum computing?','What about an unrelated topic not covered in the corpus?']},
]
# Add only verified article URLs that actually disagree on the SAME claim.
# Example: {'id':'C01','question':'What date did the event take place?',
# 'follow_up':'These sources give different dates. Can you explain?',
# 'article_a':'https://www.xicteksystems.com/blog/real-article-a/',
# 'article_b':'https://www.xicteksystems.com/blog/real-article-b/'}
CONFLICTS=[]

def api_call(message, conversation_id, history):
    if not BASE_URL: return {'error':'QA_BASE_URL is not configured'}
    payload={'message':message,'conversation_id':conversation_id}
    if HISTORY_MODE=='payload': payload['history']=history
    try:
        r=SESSION.post(BASE_URL.rstrip('/')+'/'+CHAT_PATH.lstrip('/'),json=payload,timeout=TIMEOUT)
        if r.status_code!=200: return {'error':f'HTTP {r.status_code}: {r.text[:200]}'}
        data=r.json()
        if not isinstance(data,dict): return {'error':'API JSON response must be an object'}
        return data
    except Exception as e: return {'error':str(e)[:200]}

def unpack(data):
    text=data.get(TEXT_FIELD) or data.get('response') or data.get('answer') or data.get('reply') or ''
    sources=data.get('sources') or data.get('citations') or []
    urls=[]
    for s in sources:
        if isinstance(s,str): urls.append(s)
        elif isinstance(s,dict) and s.get('url'): urls.append(s['url'])
    urls += URL_RE.findall(text if isinstance(text,str) else '')
    return str(text),list(dict.fromkeys(u.rstrip('.,') for u in urls))

def valid_url(url):
    try: p=urlparse(url)
    except Exception: return False,'invalid URL'
    if p.scheme!='https': return False,'must use HTTPS'
    if p.hostname!=DOMAIN: return False,'hostname is not the exact approved domain'
    if not any(p.path.startswith(x) and len(p.path)>len(x) for x in PREFIXES): return False,'path is outside approved prefixes'
    if p.username or p.password: return False,'credentials in URL are not allowed'
    return True,''

def fetch_article(url):
    if url in CACHE: return CACHE[url]
    try:
        r=SESSION.get(url,timeout=20); r.raise_for_status()
        t=re.sub(r'<(script|style|noscript)[^>]*>.*?</\\1>',' ',r.text,flags=re.S|re.I)
        t=re.sub(r'<[^>]+>',' ',t)
        CACHE[url]=re.sub(r'\\s+',' ',html.unescape(t)).lower()
    except Exception: CACHE[url]=None
    return CACHE[url]

def check_live(url):
    try:
        r=SESSION.head(url,allow_redirects=True,timeout=15)
        if r.status_code in (403,405): r=SESSION.get(url,allow_redirects=True,timeout=15,stream=True)
        return r.status_code<400, str(r.status_code)
    except Exception as e: return False,str(e)[:80]

def citation_screening(reply, urls):
    """Heuristic screening only; never treat lexical overlap as proof of entailment."""
    texts=[fetch_article(u) for u in urls]
    texts=[x for x in texts if x]
    if not texts: return 'REVIEW','Could not retrieve cited article text; manually inspect.'
    corpus=' '.join(texts); body=URL_RE.sub('',reply).lower()
    words={w for w in re.findall(r'[a-z]{6,}',body) if w not in STOP}
    numbers=re.findall(r'\\b\\d[\\d,.]*\\b',body)
    missing=[n for n in numbers if n not in corpus]
    overlap=sum(w in corpus for w in words)/len(words) if words else 1.0
    if missing: return 'REVIEW','Numbers/dates not found verbatim: '+', '.join(missing[:5])
    if overlap>=.60: return 'REVIEW',f'Lexical overlap {overlap:.0%}; manual claim-level entailment check still required.'
    return 'REVIEW',f'Low lexical overlap {overlap:.0%}; manually verify paraphrases and claims.'

def evaluate(kind,turn_index,reply,urls):
    if kind=='out-of-scope' and turn_index==0:
        ok=bool(REFUSAL.search(reply)) and not urls
        return {'format':'PASS' if ok else 'FAIL','live':'N/A','citation':'N/A','detail':'Out-of-scope refusal check' if ok else 'Expected refusal without citations'}
    if not urls:
        refused=bool(REFUSAL.search(reply))
        return {'format':'N/A' if refused else 'FAIL','live':'N/A','citation':'N/A' if refused else 'FAIL','detail':'Refusal without links' if refused else 'Answer has no source link'}
    bad=[u for u in urls if not valid_url(u)[0]]
    lives=[check_live(u)[0] for u in urls if valid_url(u)[0]]
    eligible=[u for u in urls if valid_url(u)[0]]
    cit,detail=citation_screening(reply,eligible) if eligible else ('FAIL','No citation URL passed allowlist')
    return {'format':'FAIL' if bad else 'PASS','live':'FAIL' if lives and not all(lives) else ('N/A' if not lives else 'PASS'),'citation':cit,'detail':detail+ (('; invalid URLs: '+', '.join(bad)) if bad else '')}

def run():
    rows=[]; os.makedirs('logs',exist_ok=True)
    with open('logs/blog_multiturn_log.jsonl','w',encoding='utf-8') as log:
      for conv in CONVERSATIONS:
        cid='e2e-'+conv['id']+'-'+uuid.uuid4().hex[:6]; history=[]
        for i,q in enumerate(conv['turns']):
          data=api_call(q,cid,history); reply,urls=unpack(data) if 'error' not in data else (data['error'],[])
          log.write(json.dumps({'conversation':conv['id'],'turn':i+1,'request':q,'history':history,'response':data},ensure_ascii=False)+'\\n')
          ev=evaluate(conv['kind'],i,reply,urls) if 'error' not in data else {'format':'FAIL','live':'N/A','citation':'N/A','detail':'API error'}
          overall='FAIL' if 'FAIL' in (ev['format'],ev['live'],ev['citation']) else ('REVIEW' if ev['citation']=='REVIEW' else 'PASS')
          rows.append({'conversation':conv['id'],'turn':i+1,'question':q,'reply':reply.replace('\\n',' '),'urls':' | '.join(urls),'format':ev['format'],'live':ev['live'],'citation':ev['citation'],'overall':overall,'detail':ev['detail']})
          history += [{'role':'user','content':q},{'role':'assistant','content':reply}]
      for c in CONFLICTS:
        rows.append({'conversation':c['id'],'turn':'conflict','question':c['question'],'reply':'','urls':c['article_a']+' | '+c['article_b'],'format':'MANUAL','live':'MANUAL','citation':'MANUAL','overall':'REVIEW','detail':'Read both articles and response log; confirm both sources are cited and disagreement is explicitly attributed.'})
    if rows:
      with open('blog_pipeline_results.csv','w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    total=[r for r in rows if r['turn']!='conflict']
    lines=['# Blog & News E2E QA Report',f"Generated: {datetime.now(timezone.utc).isoformat()}",'','## Summary',f'- API turns: {len(total)}',f"- PASS: {sum(r['overall']=='PASS' for r in total)}",f"- REVIEW: {sum(r['overall']=='REVIEW' for r in total)}",f"- FAIL: {sum(r['overall']=='FAIL' for r in total)}",'','## Interpretation','- Citation screening is deliberately marked REVIEW: lexical overlap cannot prove that a cited source entails a claim.','- Conflict cases require real article pairs and manual claim-level review; an empty conflict list means conflict handling was not tested.','- Results are valid only for the configured live endpoint and current corpus.','']
    open('citation_report.md','w',encoding='utf-8').write('\\n'.join(lines))
    print(f"Completed {len(total)} API turns. See blog_pipeline_results.csv, logs/blog_multiturn_log.jsonl, citation_report.md")
    if not BASE_URL: print('NOTE: Configure QA_BASE_URL before running live tests.')
if __name__=='__main__': run()
