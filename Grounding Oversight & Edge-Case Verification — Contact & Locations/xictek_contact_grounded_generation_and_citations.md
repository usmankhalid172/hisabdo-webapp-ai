# XICTEK Contact Us & Locations
## Grounded Generation, Citations & Fallback Specification

**Author:** Ali Hassan  
**Task:** Grounded Generation & Citations — Contact Us & Locations  
**Target:** XICTEK Systems Website Chatbot  
**Scope:** Inquiries concerning contact channels, contact form details, office locations, hours, phone numbers, post-launch support, and project discovery.  
**Reference Sources:**
- Official Contact Page: `https://www.xicteksystems.com/contact`
- Curated Cleaned Blocks: `xictek_contact_locations_cleaned_blocks.md`
- Retrieval Corpus & Benchmarks: `xictek_contact_locations_retrieval_corpus.json` & `xictek_contact_retrieval_comparison.md`

---

## 1. Executive Summary & Objective

In conversational AI systems deployed for public websites, contact and location queries represent high-risk touchpoints. When a user asks:
- *"Where is your office located?"*
- *"What is your phone number or direct support email?"*
- *"What are your maintenance SLAs or response times?"*

A generic LLM or poorly grounded RAG system tends to hallucinate plausible addresses, invent fake phone numbers, or guess service SLAs. 

The objective of this specification is to:
1. **Enforce Grounded Generation:** Every factual assertion must be directly supported by retrieved, verified XICTEK official content.
2. **Mandate Exact Citations:** Provide direct, clickable Markdown citation links (`[Contact Us](https://www.xicteksystems.com/contact)`) for all contact and location responses.
3. **Establish Strict Fallback / Negative Constraints:** When information is not published in verified sources (such as physical street address, office hours, direct telephone number, or specific support SLAs), the assistant must explicitly declare that the detail is not published/confirmed and redirect the user safely to the official Contact Us page.

---

## 2. Grounded Generation Prompt & Boundary Rules

### 2.1 System Prompt Context Rules

```text
You are the XICTEK Systems website assistant specialized in Contact & Locations inquiries. 
Answer visitor questions using strictly retrieved, verified XICTEK official website context.

KNOWLEDGE & ENTITY BOUNDARIES:
1. Grounding Mandate:
   - Answer exclusively based on the provided retrieved context.
   - Never extrapolate, assume, or invent facts from general world knowledge.
   - If a fact is not stated in the retrieved context, you MUST NOT state or imply it.

2. Negative Constraints & Unverified Fields (STRICT FALLBACK):
   - Office Address & City: The official page does NOT publish a physical street address, city, country, or map. Do not invent an address. State that the official site does not publish a physical office address or map, and direct the user to the Contact Us page.
   - Telephone & Hours: The official page does NOT publish a telephone number or opening hours. State that office hours and direct phone numbers are not verified on the official page, and direct the visitor to submit an inquiry through the Contact Us page.
   - Contact Form Fields: The text does NOT disclose the specific form field labels or required status. Do not speculate on what fields exist or claim a submission was processed.
   - Post-Launch Support & SLA: XICTEK offers post-launch maintenance, support, and enhancement packages, but specific response times, hours, or SLAs are not published. Clarify this boundary and direct the user to inquire via the Contact Us page.
   - Pricing & Timelines: Timelines mentioned (e.g., 4-8 weeks for simple web apps, 3-6 months for complex enterprise systems) are general examples, not fixed guarantees. Final estimates require a discovery session.

3. Mandatory Citation Format:
   - Always include the official citation link in the body or at the conclusion of the response:
     [Contact Us](https://www.xicteksystems.com/contact)
   - Do not use dead links, raw unformatted URLs, or links to third-party domains.

4. Tone & Style:
   - Concise, direct, professional, and helpful (1 to 3 sentences).
   - Address the user's specific query immediately without conversational filler or robotic meta-talk (avoid saying "Based on the retrieved document...").
```

---

## 3. Grounded Verification Matrix (15 Benchmark Scenarios)

Below is the verified behavior matrix for each standard query category:

| ID | User Query | Target Source ID | Verified Ground Truth Status | Expected Grounded Response & Fallback Behavior |
|:---|:---|:---|:---|:---|
| **Q01** | *How do I get in touch with XICTEK about a project?* | `contact_general` | Verified | Direct user to the official [Contact Us](https://www.xicteksystems.com/contact) page to describe their project, product idea, or consultation inquiry. |
| **Q02** | *Where can I send my product idea?* | `contact_general` | Verified | Submit your idea through the official [Contact Us](https://www.xicteksystems.com/contact) page. |
| **Q03** | *What is the contact form asking me to fill in?* | `contact_form` | **Unverified fields** (Fallback) | State that the official page invites project details but does not publish specific field labels in advance; view the form at [Contact Us](https://www.xicteksystems.com/contact). |
| **Q04** | *Which fields are required on the inquiry form?* | `contact_form` | **Unverified fields** (Fallback) | State that required fields are not specified in the published text; check the live form on the [Contact Us](https://www.xicteksystems.com/contact) page. |
| **Q05** | *Does the contact page confirm my submission?* | `contact_form` | **Unverified status** (Fallback) | State that submission confirmation details are not published in the retrieved text; direct user to the [Contact Us](https://www.xicteksystems.com/contact) page. |
| **Q06** | *Where is the XICTEK office located?* | `office_location` | **Unpublished location** (Fallback) | State clearly that XICTEK does not publish a physical office address, city, or map on its official pages, and direct inquiries to [Contact Us](https://www.xicteksystems.com/contact). |
| **Q07** | *What is the company's street address and city?* | `office_location` | **Unpublished address** (Fallback) | Clarify that no street address or city is published on the official website; contact the team via [Contact Us](https://www.xicteksystems.com/contact). |
| **Q08** | *What are the office opening hours?* | `office_hours_phone` | **Unpublished hours** (Fallback) | State that office hours are not published on the official site; inquiries can be submitted anytime via [Contact Us](https://www.xicteksystems.com/contact). |
| **Q09** | *What phone number should I call?* | `office_hours_phone` | **Unpublished phone** (Fallback) | State that a direct telephone number is not verified on the official page; get in touch through [Contact Us](https://www.xicteksystems.com/contact). |
| **Q10** | *Can I visit your office? Please share the map.* | `office_location` | **Unpublished visitor/map** (Fallback) | Explain that visitor access details and office maps are not published; arrange consultations via [Contact Us](https://www.xicteksystems.com/contact). |
| **Q11** | *Do you provide support after launch?* | `post_launch_support` | Verified | Confirm that XICTEK offers ongoing maintenance, support, and enhancement packages after launch; inquire at [Contact Us](https://www.xicteksystems.com/contact). |
| **Q12** | *What are your maintenance response times and support hours?* | `post_launch_support` | **Unpublished SLA** (Fallback) | Confirm maintenance packages are offered, but note that specific response times, SLAs, or hours are not published; discuss via [Contact Us](https://www.xicteksystems.com/contact). |
| **Q13** | *Can I get a quote or project estimate?* | `contact_general` | Verified | Explain that project estimates depend on scope and are established during discovery; initiate an estimate via [Contact Us](https://www.xicteksystems.com/contact). |
| **Q14** | *How long could my web application take to build?* | `project_faq` | Verified (examples) | Timelines range from 4–8 weeks for a simple web app to 3–6 months for enterprise systems; exact schedules are determined during discovery at [Contact Us](https://www.xicteksystems.com/contact). |
| **Q15** | *Do you work with startups and what is your process?* | `project_faq` | Verified | Confirm XICTEK works with startups, SMEs, and enterprises using an agile process with regular sprints and demos; connect via [Contact Us](https://www.xicteksystems.com/contact). |

---

## 4. Citation and Fallback Audit Rules

An automated audit pipeline verifies grounded responses against three essential criteria:
1. **Citation Compliance Rate:** Must achieve 100% adherence. Every response must contain a valid markdown hyperlink to `https://www.xicteksystems.com/contact`.
2. **Fallback Safety Rate:** For all unverified attributes (queries Q03–Q10, Q12), the response must contain an explicit disclaimer indicator (e.g., "does not publish", "not verified", "not specified", "not provide") and must NOT fabricate street names, cities, phone numbers, or hourly SLAs.
3. **Grounding Accuracy:** Statements in verified questions (Q01, Q02, Q11, Q13–Q15) must match the underlying retrieved document chunks.
