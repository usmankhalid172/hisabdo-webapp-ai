# Product Guidance, PDF Verification and Multilingual Test Coverage

**Owner:** Fahad Zubairi · **Date:** 2026-10-16 · **Branch:** `FahadZubairi_AI`

The HisabDo features for expenses, income, khata, udhar, reports and PDF statements are confirmed by four official sources. Exact button names and screen paths could not be confirmed, because the app's source code and an Android device were not available. The chatbot's intent router now sends 81% of new multilingual product questions to the right place, up from 37%.

## Sources used for verification

All were read on 2026-10-16. Nothing in this document comes from anywhere else.

| Source | URL |
|---|---|
| Official FAQ (30 answers) | https://hisabdo.app/faq |
| About the app | https://hisabdo.app/about-app |
| Home page | https://hisabdo.app/ |
| Google Play listing (updated 13 Oct 2026) | https://play.google.com/store/apps/details?id=com.usman.hisabdo |
| Official khata guide | https://hisabdo.app/blog/how-to-manage-daily-khata |

## Verified features

| Feature | Verified | What the sources say |
|---|---|---|
| Customers | Yes | Each customer has a profile (name, contact details), their own transaction history and a running balance |
| Khata / ledger | Yes | Records money given and money received; each customer is a separate account |
| Udhar (receivables) | Yes | Tracks what customers owe, with full history and current outstanding balance |
| Payables | Yes | Tracks money owed to suppliers or others, alongside receivables |
| Expenses and income | Yes | Expenses and income are recorded and tracked |
| Notes on entries | Yes | A descriptive note can be added to any transaction |
| PDF statements and reports | Yes | PDF statements for any customer account or time period, shared via WhatsApp, email or any messaging app |
| Voice entry | Yes | Records can be created by speaking |
| Analytics | Yes | Visual income trends, expense patterns and outstanding balances |
| Dashboard | Yes | Shows receivables, payables and cash position on opening; overdue balances are visible |
| Backup and restore | Yes | Local backup to the device or external storage; restore on any Android device running HisabDo |
| Guest mode and sync | Yes | Guest mode keeps records on the device and works offline; signed-in users can sync supported data with Supabase |
| Languages | Yes | Urdu, English, Hindi, Arabic and Roman Urdu, switchable in settings |
| Currencies | **Conflict** | Website: PKR, USD, INR. Google Play (newer, 13 Oct 2026): PKR, INR, AED, USD |
| Platform | Yes | Android only (6.0+, 8.0+ recommended); no iOS app |
| Price | Yes | Free; core features including khata, customer accounts, PDF export and backup cost nothing |

## Practical instructions

These are at the level the official sources confirm. Labels in *italics* come from screen names on the home page or a user review, not from an official walkthrough. **Confirm them in the app before publishing** (see "What still needs the app").

**Udhar (credit sale).**
1. Create the customer if they don't exist yet: name and contact details.
2. Record the transaction against that customer as **money given (udhar)**. Add the date, amount and a short note such as "grocery items".
3. The customer's running balance updates straight away.

**Payment received.**
1. Open the same customer.
2. Record the transaction as **money received (payment)**.
3. The outstanding balance goes down. Partial payments are recorded the same way.

**Khata.**
- Keep one account per customer, rather than one long list. That way "how much does Ahmed owe?" is answered from his own history.
- The official guide recommends recording entries the same day and reviewing them every evening.

**Expenses and income.**
- Record each expense or income entry as it happens.
- Voice entry is available when typing is slow.
- Notes make entries easier to review later.

**Reports and analytics.**
- The dashboard shows receivables, payables and cash position.
- Analytics show income trends, expense patterns and unpaid dues.

**PDF statement.**
1. Generate a PDF statement for a customer account or a time period. It shows what is owed, what has been paid and the running balance.
2. Share it through WhatsApp, email or any messaging app, straight from the phone.

**Backup before changing phones.**
- Create a backup first, then restore it on the new device.
- Uninstalling without a backup can lose local data.

## PDF workflow: test cases to run in the app

| ID | Steps | Expected | Languages to repeat in |
|---|---|---|---|
| PDF-01 | Generate a statement for one customer | PDF lists that customer's entries only, with amount owed, amount paid and running balance | EN, UR, Roman UR |
| PDF-02 | Generate a statement for a time period | Only entries within the period appear; the first and last days are included | EN, UR, Roman UR |
| PDF-03 | Compare the PDF totals with the in-app balance | Totals match exactly | Any |
| PDF-04 | Switch the app to Urdu and generate a PDF | Urdu text renders right-to-left with no missing or boxed characters | UR |
| PDF-05 | Share the PDF to WhatsApp, then email | The file arrives and opens on the receiving device | Any |
| PDF-06 | Customer with no entries | Clear empty statement, no error | Any |
| PDF-07 | Each supported currency | The correct currency symbol appears; check AED, given the currency conflict | Any |
| PDF-08 | Guest mode, offline | A PDF can still be generated | Any |

## Unsupported claims in the chatbot's knowledge base (`data/faq_docs.json`)

The live chatbot can repeat these today. Each needs product-team confirmation, or should be rewritten.

| Entry | Claim | Finding |
|---|---|---|
| `faq-005` | Export expenses as **CSV or PDF** from a **Reports section**, filtered by **date range, category or tag** | Official sources mention **PDF only**, by customer account or time period. CSV, a "Reports section" and category or tag filters are not mentioned. |
| `faq-002` | When you add an expense, HisabDo **predicts a category with a machine-learning model** | Not mentioned in any official source. This looks like the AI team's in-progress feature described as live. |
| `faq-001` | An "AI-assisted breakdown" of spending | Official sources describe visual analytics, not AI analysis |

## Multilingual test coverage

**Test sets:**
- `data/multilingual_product_test_cases.json`: 39 cases. Expenses, income, khata, udhar, reports, PDF and offline use, each in English, Urdu script and Roman Urdu.
- `data/multilingual_product_test_cases_heldout.json`: 27 more cases, written **before** any change and never used for tuning.

**Results**, from `python scripts/evaluate_multilingual_coverage.py` (add `--heldout` for the second set):

| Set | Before | After | Private questions on a public route (before → after) |
|---|---|---|---|
| Original 39 cases | 25/39 (64%) | 39/39 (100%) | 3 → 0 |
| Held-out 27 cases | 10/27 (37%) | **22/27 (81%)** | 7 → 1 |
| Saba's labelled set | 60/60 | 60/60 | 0 → 0 |
| Saba's held-out set | 30/33 | 30/33 | 0 → 0 |

The original 39 cases were used while writing the change, so their 100% is expected. The held-out 81% is the honest measure.

**The change**, in `src/financial_assistant/dialogue/recognizer.py`:
- **New vocabulary.** Urdu-script phrases for "how much was spent or earned", "owe me" and "baqi" in Urdu script, and khata, PDF and backup as product topics.
- **Three rules:**
  1. A how-to question about a PDF, statement, export, share or backup is a **product question**, not a request for the user's own report.
  2. "How much … owed / udhar / baqi" stays on the **private route**.
  3. "Show Ahmed's khata" is **private data**; "What is khata?" is a product question.
- **Not affected:** generic "how do I write…" requests, such as a payment reminder, still go to the general assistant.

**Still wrong on the held-out set:**

| Message | Expected | Got |
|---|---|---|
| What did I spend last month? | report (private) | general: **a private question on a public route** |
| What does udhar mean? | faq | general |
| Can HisabDo make a monthly report PDF? (in all 3 languages) | faq | report |

**Tests:** `tests/test_multilingual_product_coverage.py`, 42 tests. They check:
- every original case is routed correctly
- no private question reaches a public route
- every area is covered in all three languages
- Urdu-script messages are answered in Roman Urdu, per the team rule

## What still needs the app

1. Exact button labels and screen paths for each instruction above. Ideally capture screenshots for the knowledge base.
2. PDF test cases PDF-01 to PDF-08, run on an Android device.
3. Which currency list is current: the website's or Google Play's.
4. A product-team answer on the three `faq_docs.json` claims.
