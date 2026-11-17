# Content Update Runbook — Blog & News

**Task:** Defect Closure & Production Config Freeze — Blog & News
**Date:** 17 November 2026
**Owner:** QA Automation
**Audience:** Content editors, on-call engineers, QA
**Companion artifacts:** `frozen-domain-configuration-spec.md` (the config this runbook maintains), `defect-closure-log.md` (rationale for the content validator, Defect D10), `scripts/validate_new_article.py` (the ingestion-time content validator).

---

## 1. Purpose

This runbook documents the routine steps for adding new blog or news articles to the Blog & News knowledge base, re-indexing the retrieval corpus, and verifying that the production pipeline still meets the frozen regression acceptance criteria.

It exists because the Day-11 frozen configuration is the production source of truth, but the corpus is living — new articles are published weekly on `xicteksystems.com/blog/`. Every content update must preserve the configuration's invariants: clean frontmatter, on-allowlist URLs, no prompt-injection content, no scope-violating URLs, no dangerous URI schemes.

The runbook also closes Defect D10 (article corpus integrity assumes CMS trust). The Day-7 security report flagged that an attacker who compromises the CMS could inject malicious content into a blog article, which the pipeline would faithfully surface. The content validator in `scripts/validate_new_article.py` runs at ingestion time to catch this.

---

## 2. Roles & Cadence

| Role | Responsibility | Cadence |
|---|---|---|
| Content editor | Drafts new article, ensures frontmatter is present and accurate | Per article |
| QA reviewer | Runs the content validator; reviews any warnings | Per article |
| On-call engineer | Re-indexes the corpus; runs the regression suite; signs off the release | Per content batch (weekly) |
| QA automation owner | Approves any config change request; re-freezes the spec | Per change request |

---

## 3. Ingestion-Time Content Validation

Every new or updated article must pass `scripts/validate_new_article.py` before it is added to the corpus. This is the gate that mitigates Defect D10.

### 3.1 What the validator checks

| Rule | What it checks | Failure mode caught |
|---|---|---|
| R1 | Required frontmatter is present (`Source`, `Category`, `Reading time`, `Published`, `Author`) | Incomplete metadata that breaks citation display or stale-article detection |
| R2 | Source URL is on the production blog allowlist (`https://www.xicteksystems.com/blog/<slug>`) | Off-domain source; possible CMS injection |
| R3 | Body length is within chunking limits (50 ≤ len ≤ 5000 chars; warn if longer) | Untrimmed dump; chunker will truncate but the source should be reviewed |
| R4 | No prompt-injection patterns in body (`ignore previous instructions`, `[SYSTEM]`, `<<SYS>>`, `<|im_start|>`, `reveal the system prompt`, etc.) | CMS-injected prompt-injection attack |
| R5 | No dangerous URI schemes (`javascript:`, `file:`, `data:`, `vbscript:`) | CMS-injected malicious link |
| R6 | No non-blog URLs masquerading as sources in body (`/services`, `/contact`, `hisabdo.app`, external domains) | Scope leak in the article content itself (would be propagated by retrieval) |
| R7 | No base64-looking blobs over 200 chars | Possible encoded injection payload (warned; error in strict mode) |
| R8 | No exfiltration patterns (`curl`, `wget`, `fetch()`, `eval()`, `XMLHttpRequest`) in body | Not normal blog content; possible script injection |

### 3.2 How to run the validator

```bash
# Single article
python3 scripts/validate_new_article.py data/articles/new-article.md

# Whole corpus (useful as a sanity check after a CMS export)
python3 scripts/validate_new_article.py data/articles/

# Strict mode (long bodies and base64 blobs become errors, not warnings)
python3 scripts/validate_new_article.py --strict data/articles/new-article.md

# JSON output (for CI integration)
python3 scripts/validate_new_article.py --json data/articles/new-article.md
```

Exit code: `0` = all articles PASS, `1` = at least one REJECT. A CI gate should treat exit code `1` as a build failure.

### 3.3 Pre-existing corpus note

When the validator runs against the frozen production corpus (47 articles as of 2026-11-17), 46/47 PASS and 1/47 is REJECTED: `dotnet-development-services.md` is missing `**Category:**` and `**Reading time:**` frontmatter. This is a real pre-existing defect in the corpus cleaner's output (the cleaner that produced this article skipped those fields); it does not affect retrieval (the missing fields are not used in retrieval scoring), but it should be patched the next time the corpus is re-cleaned. The content validator caught it — which is the point.

---

## 4. Routine Content Update Procedure

Use this procedure every time a new article is published on `xicteksystems.com/blog/`, or an existing article is materially updated.

### Step 1 — Acquire the cleaned article

The article must already be in the production Markdown format used by the corpus. If it is not, run the content cleaning pipeline (Day-2) on the raw HTML before proceeding. The cleaned file must:

- Be named `<slug>.md`, where `<slug>` matches the production blog URL slug.
- Have the header format used by the rest of the corpus:
  ```
  # <Article Title>

  *Source: https://www.xicteksystems.com/blog/<slug>*

  **Category:** <CATEGORY> · **Reading time:** <N> min · **Published:** <Month D, YYYY> · **Author:** XICTEK

  ---

  <body...>
  ```
- Use UTF-8 encoding with no BOM.
- Have a body length of 50–5000 characters (longer articles will be truncated by the chunker).

### Step 2 — Place the article in the corpus

```bash
cp /path/to/new-article.md data/articles/<slug>.md
```

### Step 3 — Run the content validator

```bash
python3 scripts/validate_new_article.py data/articles/<slug>.md
```

**If PASS:** proceed to Step 4.
**If REJECT:** read the error list. Fix the article (frontmatter, body content, or both). Re-run Step 3. Do not proceed until the validator passes.

### Step 4 — Update the article count in the config

Edit `configs/retrieval_config.json`:

```json
"data": {
  "articles_dir": "data/articles",
  "article_count": 48,        // ← increment
  "total_words": 47123         // ← recompute (wc -w data/articles/*.md)
}
```

### Step 5 — Re-index the corpus

The retriever rebuilds its index on the next call (lazy loading in dev; explicit in production). In production:

```bash
# Trigger a hot-reload of the retriever (production-specific command; substitute
# your deployment's reload signal — e.g. SIGHUP, supervisorctl restart, or a
# /admin/reload endpoint).
kill -HUP $(cat /var/run/xictek-blog-assistant.pid)
```

In dev (or for a full re-test):

```bash
python3 -c "
from src.retrieval import Retriever
r = Retriever()
print(f'Indexed {len(r.articles)} articles.')
"
```

### Step 6 — Run the regression suite

Re-run the Day-11 regression suite to confirm the new article did not break any invariants.

```bash
python3 scripts/run_e2e_regression.py
```

**Acceptance criteria** (from Frozen Domain Configuration Spec §11):

| Criterion | Threshold |
|---|---|
| Retrieval Hit@3 | ≥ 100% (24/24) |
| Retrieval MRR@3 | ≥ 1.0000 |
| Citation accuracy rate | ≥ 100% |
| URL validity rate | ≥ 100% |
| Scope-violation URLs leaked | = 0 |
| Failed-query recovery | 17/17 |
| Passing-query preservation | 7/7 |
| P95 latency | ≤ 5000 ms |

**If all criteria pass:** sign off and proceed to Step 7.
**If any criterion fails:** revert the article addition (`rm data/articles/<slug>.md`), re-index, re-run. Investigate why the new article caused a regression (often: the new article's slug collides with a Day-1 ground-truth slug, or the new article's body contains a term that mis-routes retrieval). Document the finding as a new defect in the Defect Closure Log.

### Step 7 — Log the update

Append to `results/content_updates.log` (create if missing):

```
2026-11-17 14:30:00  added  <slug>  validator=PASS  regression=PASS  by=<editor>
```

### Step 8 — Communicate

Notify the QA automation owner that the corpus has been updated and the regression suite passes. If the article count changed by more than 5%, a re-freeze of the frozen configuration spec is recommended (the spec's `article_count` field is informational but should be kept current).

---

## 5. Batch Update Procedure

For a larger content refresh (e.g. a monthly CMS export that adds or updates 5+ articles):

1. Place all new/updated `.md` files in `data/articles/`.
2. Run the validator on the directory:
   ```bash
   python3 scripts/validate_new_article.py data/articles/
   ```
3. If any article is REJECTED, fix or remove it; re-run.
4. Update `article_count` and `total_words` in `configs/retrieval_config.json`.
5. Re-index (Step 5 above).
6. Run the regression suite (Step 6 above).
7. If any new article's slug collides with an existing article's slug, the old article is overwritten — record this in `results/content_updates.log` with `replaced` instead of `added`.

---

## 6. Article Removal Procedure

When an article is taken down from `xicteksystems.com/blog/`:

1. `rm data/articles/<slug>.md`
2. Update `article_count` in `configs/retrieval_config.json`.
3. Re-index (Step 5 above).
4. Run the regression suite (Step 6 above). The Day-1 golden set references 24 specific slugs; if a removed article is in that set, the regression will fail for the corresponding query. Document this as a new defect and decide whether to:
   - Update the golden set to use a replacement article (requires QA owner approval), or
   - Restore the article on the production blog.
5. Log the removal in `results/content_updates.log`:
   ```
   2026-11-17 14:30:00  removed  <slug>  by=<editor>  reason=<takedown|duplicate|stale|...>
   ```

---

## 7. Configuration Drift Detection

Monthly, run a sanity check to confirm the live corpus matches the frozen configuration:

```bash
# Article count
ls data/articles/*.md | wc -l   # should equal configs/retrieval_config.json data.article_count

# Total word count
wc -w data/articles/*.md | tail -1   # should be within 5% of configs/retrieval_config.json data.total_words

# All articles pass the content validator
python3 scripts/validate_new_article.py data/articles/   # should exit 0 (or 1 for the known dotnet article)
```

If any of these drift, raise a change request (see Frozen Domain Configuration Spec §12).

---

## 8. Emergency Rollback

If a content update causes a production incident (e.g. users see broken citations, scope-violation URLs, or stale-article confusion):

1. `mv data/articles/<offending-slug>.md /tmp/rolled-back-<slug>.md`
2. Update `article_count` in `configs/retrieval_config.json`.
3. Re-index (Step 5 above).
4. Run the regression suite (Step 6 above).
5. Log the rollback in `results/content_updates.log`:
   ```
   2026-11-17 14:30:00  rolled-back  <slug>  by=<on-call>  reason=<incident-description>
   ```
6. Open a post-incident review. Add the finding to the Defect Closure Log as a new defect.

---

## 9. Companion Files

| File | Purpose |
|---|---|
| `scripts/validate_new_article.py` | The ingestion-time content validator (mitigates Defect D10) |
| `configs/retrieval_config.json` | The frozen retrieval configuration (article count is updated per Step 4) |
| `configs/synonyms.json` | The synonym map (rarely changes; only when a new domain term is added) |
| `configs/safe_logging_config.json` | The logging configuration (does not change with content updates) |
| `results/content_updates.log` | Append-only log of every content change (created on first update) |
| `scripts/run_e2e_regression.py` | The regression suite (re-run after every content update) |

---

## 10. Escalation

| Situation | Escalate to |
|---|---|
| Validator rejects an article and the editor cannot fix it | QA automation owner |
| Regression suite fails after a content update | QA automation owner + on-call engineer |
| Production incident (broken citations, scope leak, stale-article confusion) | On-call engineer immediately; QA owner in post-incident review |
| Suspected CMS compromise (validator flags injection patterns) | Security team immediately; freeze the corpus; do not re-index until cleared |
| Configuration change request (e.g. adding a new synonym, raising top-k) | QA automation owner (requires regression re-run and re-freeze per §12 of the Frozen Spec) |

---

## 11. Quick Reference

```bash
# Validate one article
python3 scripts/validate_new_article.py data/articles/<slug>.md

# Validate the whole corpus
python3 scripts/validate_new_article.py data/articles/

# Re-index (dev)
python3 -c "from src.retrieval import Retriever; r = Retriever(); print(f'Indexed {len(r.articles)} articles.')"

# Run the regression suite
python3 scripts/run_e2e_regression.py

# Log a content update
echo "$(date -Iseconds)  added  <slug>  validator=PASS  regression=PASS  by=<editor>" >> results/content_updates.log
```
