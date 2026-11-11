"""
Final release QA (Alisha Noor)
  Part A: About Us & Company Overview - run the benchmark through the live /chat API
  Part B: Careers & Job Openings      - validate every link/action in the answers

Needs in the same folder: benchmark_testset.csv, about_us_prompt_v2.py, benchmark_eval.py
Setup:  pip install requests
Run:    python release_qa.py
Output: qa_aboutus_results.csv, qa_careers_links.csv, summary in the terminal
"""
import csv
import os
import re
import sys
import uuid
from urllib.parse import urlparse

import requests

from about_us_prompt import OFFICIAL_URL
from benchmark_eval import check_tone

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ----------------------------- CONFIG -----------------------------
BASE_URL = os.environ.get("QA_BASE_URL", "https://hisabdo-ai-api.hisabdo.app")
COMPANY_DOMAIN = os.environ.get("QA_DOMAIN", "xicteksystems.com")

CAREERS_PAGE_URL = "https://www.xicteksystems.com/careers"
EXTRA_LINKS = []           # <-- other links to check directly, e.g. an Apply link

CAREERS_QUESTIONS = [      # <-- edit to match the real job openings
    "What job openings do you have?",
    "How can I apply for a job at XICTEK Systems?",
    "Do you have any internship positions?",
    "What are the requirements for the open positions?",
    "Where can I send my CV?",
    "Can you check if I am eligible for a job?",
    "What happens to my CV after I apply?",
    "Aap ke han kaun si jobs available hain?",
]
# -------------------------------------------------------------------

# From the previous owner's SECURITY-REVIEW.md:
FLAGGED_CONTACTS = ["xicteksystems@gmail.com"]   # CVs must not be sent to this email
PRIVACY_QUESTIONS = ["Can you check if I am eligible for a job?"]   # answer must warn about personal info
WARNING_RE = re.compile(r"do not (share|enter)|don't (share|enter)|avoid (sharing|entering)|"
                        r"personal (information|details)|privacy", re.I)

UA = {"User-Agent": "Mozilla/5.0 (release-qa)"}
REFUSAL = re.compile(r"could not find|couldn't find|can't find|cannot find|don't have|"
                     r"do not have|no information|not available|not covered", re.I)
URL_RE = re.compile(r"https?://[^\s)\]>\"']+")
MAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")


def ask(question):
    try:
        r = requests.post(f"{BASE_URL}/chat", timeout=60, json={
            "conversation_id": f"qa-{uuid.uuid4().hex[:8]}", "history": [], "message": question})
        if r.status_code != 200:
            return {"error": f"HTTP {r.status_code}"}
        return r.json()
    except Exception as e:
        return {"error": str(e)[:80]}


def links_in(data):
    reply = data.get("reply", "")
    urls = [u.rstrip(".,") for u in URL_RE.findall(reply)]
    urls += [s.get("url", "") for s in data.get("sources", []) if s.get("url")]
    urls += ["mailto:" + m for m in MAIL_RE.findall(reply)]
    return list(dict.fromkeys(urls))


_cache = {}
def check_link(url):
    """Returns (status, code, final_url). status: OK / BROKEN / MANUAL"""
    if url in _cache:
        return _cache[url]
    if url.startswith("mailto:"):
        res = ("MANUAL", "-", "email address: send a test mail")
    else:
        try:
            r = requests.head(url, allow_redirects=True, timeout=15, headers=UA)
            if r.status_code >= 400:   # some sites reject HEAD, so retry with GET
                r = requests.get(url, allow_redirects=True, timeout=15, headers=UA, stream=True)
            res = ("OK" if r.status_code < 400 else "BROKEN", str(r.status_code), r.url)
        except Exception as e:
            res = ("BROKEN", "-", str(e)[:60])
    _cache[url] = res
    return res


# ---------------- PART A: About Us ----------------
def part_a():
    tests = list(csv.DictReader(open("benchmark_testset.csv", encoding="utf-8-sig")))
    rows = []
    for t in tests:
        data = ask(t["question"])
        if "error" in data:
            rows.append({**t, "reply": data["error"], "accuracy": "FAIL", "tone": "FAIL",
                         "source": "FAIL", "overall": "FAIL"})
            continue
        reply = data.get("reply", "")
        refused = bool(REFUSAL.search(reply))
        if t["should_answer"] == "no":
            no_digits = not re.search(r"\d", URL_RE.sub("", reply))
            acc = refused and no_digits
        else:
            acc = (not refused) and any(k.strip().lower() in reply.lower()
                                        for k in t["expected_any_of"].split("|"))
        tone = check_tone(reply)
        found = [u for u in links_in(data) if u.startswith("http")]
        if t["should_answer"] == "yes":      # answers must cite the official page
            src = OFFICIAL_URL in found
        else:                                # refusals need no link, but no wrong link
            src = all(u == OFFICIAL_URL for u in found)
        rows.append({**t, "reply": reply.replace("\n", " "),
                     "accuracy": "PASS" if acc else "FAIL", "tone": "PASS" if tone else "FAIL",
                     "source": "PASS" if src else "FAIL",
                     "overall": "PASS" if acc and tone and src else "FAIL"})
    with open("qa_aboutus_results.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    return rows


# ---------------- PART B: Careers ----------------
def part_b():
    out = []
    def add(question, reply, url):
        host = urlparse(url).netloc
        domain_ok = url.startswith("mailto:") or COMPANY_DOMAIN in host
        status, code, final = check_link(url)
        if any(f in url.lower() for f in FLAGGED_CONTACTS):
            status, final = "FLAGGED", "Privacy review: CVs should go to the approved application route, not this email"
        out.append({"question": question, "link": url, "status": status, "http_code": code,
                    "own_domain": "Yes" if domain_ok else "NO (external)", "final_url": final,
                    "reply": reply})

    for q in CAREERS_QUESTIONS:
        data = ask(q)
        if "error" in data:
            out.append({"question": q, "link": "-", "status": "ERROR", "http_code": "-",
                        "own_domain": "-", "final_url": "-", "reply": data["error"]})
            continue
        reply = data.get("reply", "").replace("\n", " ")
        urls = links_in(data)
        if q in PRIVACY_QUESTIONS and not WARNING_RE.search(reply):
            out.append({"question": q, "link": "-", "status": "NO WARNING", "http_code": "-",
                        "own_domain": "-", "final_url": "No warning about personal information", "reply": reply})
        if not urls:
            out.append({"question": q, "link": "-", "status": "NO LINK", "http_code": "-",
                        "own_domain": "-", "final_url": "-", "reply": reply})
        for u in urls:
            add(q, reply, u)
    for u in ([CAREERS_PAGE_URL] if CAREERS_PAGE_URL else []) + EXTRA_LINKS:
        add("(direct check)", "", u)
    if out:
        with open("qa_careers_links.csv", "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
            w.writeheader(); w.writerows(out)
    return out


if __name__ == "__main__":
    print(f"Testing {BASE_URL}\n")
    a = part_a()
    n = len(a)
    print("PART A - About Us & Company Overview")
    for m in ["accuracy", "tone", "source", "overall"]:
        print(f"  {m:9}: {sum(r[m] == 'PASS' for r in a)}/{n}")
    fa = [r["id"] for r in a if r["overall"] == "FAIL"]
    print("  Failed IDs:", ", ".join(fa) or "none")

    b = part_b()
    print("\nPART B - Careers links and actions")
    if not b:
        print("  nothing tested")
    else:
        count = lambda s: sum(r["status"] == s for r in b)
        print(f"  Links OK: {count('OK')} | BROKEN: {count('BROKEN')} | "
              f"MANUAL check: {count('MANUAL')} | Answers with NO link: {count('NO LINK')} | "
              f"API errors: {count('ERROR')}")
        print(f"  FLAGGED (CV email): {count('FLAGGED')} | Missing privacy warning: {count('NO WARNING')}")
        ext = [r["link"] for r in b if r["own_domain"].startswith("NO")]
        print("  External (non-company) links:", ", ".join(dict.fromkeys(ext)) or "none")

    problems = len(fa) + (count("BROKEN") + count("ERROR") + count("FLAGGED") + count("NO WARNING") if b else 0)
    print("\nRESULT:", "no blocking problems found" if problems == 0
          else f"{problems} item(s) need fixing before release")
    print("Saved qa_aboutus_results.csv and qa_careers_links.csv")