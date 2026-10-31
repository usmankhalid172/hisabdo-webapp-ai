# Day 4 - About Us Chunking & Retrieval Report
**Owner:** Alisha Noor
**Source:** https://YOUR-WEBSITE.com/about-us
**Queries tested:** 15 per config, top-3 checked

## Config comparison
| Config | Size | Overlap | Chunks | Hit@3 | Top-1 | MRR | Avg similarity | Chunks cut mid-sentence |
|---|---|---|---|---|---|---|---|---|
| A | 300 | 30 | 4 | 9/15 | 5/15 | 0.467 | 0.345 | 1 |
| B | 500 | 75 | 3 | 9/15 | 5/15 | 0.467 | 0.318 | 1 |
| C | 800 | 100 | 2 | 9/15 | 7/15 | 0.533 | 0.275 | 1 |
| D | 500 | 0 | 3 | 9/15 | 5/15 | 0.467 | 0.318 | 1 |

## Final choice: Config C (chunk size 800, overlap 100)
Reason: highest top-1 accuracy / hit rate / MRR in the table above. (Add your own note here about chunk completeness after reading a few chunks.)

## Failed queries (Config C)
| Query | Category | Expected keyword | Status | Suspected cause |
|---|---|---|---|---|
| What is your company mission? | direct | mission | FAIL | Check chunk boundaries / keyword wording |
| What is your company vision? | direct | vision | FAIL | Check chunk boundaries / keyword wording |
| What does your company stand for? | paraphrase | mission | FAIL | Check chunk boundaries / keyword wording |
| mission | keyword | mission | FAIL | Check chunk boundaries / keyword wording |
| I want to know who runs the company and what experience they have | long | team | PARTIAL | Check chunk boundaries / keyword wording |
| COMPANY VISION | typo_case | vision | FAIL | Typo/casing -> pass to Marsha (preprocessing) |
| company history | related | history | FAIL | Check chunk boundaries / keyword wording |
| years of experience | related | experience | PARTIAL | Check chunk boundaries / keyword wording |