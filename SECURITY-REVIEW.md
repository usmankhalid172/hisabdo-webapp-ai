# Careers Data Privacy & Compliance Review

**Scope:** Careers and Job Openings applicant interactions, including chatbot guidance and handling of applicant-submitted chat content.

## Findings

### MEDIUM — CVs are directed to an email route outside the documented process

- **Location:** `src/xictek_website_assistant/prompts.py:63`
- **Confidence:** 8/10
- **Risk:** Careers guidance recommends emailing a full CV to `xicteksystems@gmail.com`. CVs may contain names, contact details, education, and employment history. The bundled privacy-policy content instead describes resume storage in a private Supabase bucket and names Supabase, Resend, and Vercel as service providers (`src/xictek_website_assistant/data/index/chunks.json:594,610,618`). It also describes application retention and deletion rights (`:642,648`), but does not document equivalent handling for this email route.
- **Recommendation:** Direct applicants to an approved application route with documented access, retention, and deletion controls, or formally document and secure the email-based process before recommending it.

### MEDIUM — Eligibility-chat content can be sent to Groq without applicant notice

- **Location:** `src/xictek_website_assistant/prompts.py:60`
- **Confidence:** 8/10
- **Risk:** The eligibility-assessment guidance may lead applicants to share personal qualifications or identifying details in chat. The widget sends the current message and recent conversation history (`src/xictek_website_assistant/widget/xictek-widget.js:337-348`); when Groq is configured, the backend sends that content to Groq (`src/xictek_website_assistant/llm_client.py:105-118`). The bundled privacy-policy content does not name Groq among its service providers (`src/xictek_website_assistant/data/index/chunks.json:618`), and the widget does not provide notice or obtain consent before this transfer.
- **Recommendation:** Warn applicants not to enter personal information, disclose and obtain appropriate consent for the Groq transfer, and/or redact applicant PII before sending prompts to the provider.

## Validation and limitations

Focused pytest collection could not run because the environment does not have `joblib` installed. Existing careers tests cover prompt wording and provider wiring, but do not test applicant-data disclosure or privacy controls. The Groq transfer finding applies when that provider is configured.
