# Metadata Sample Records — Blog & News Cleaned Knowledge Set

**Cleaning date:** 2026-11-09  
**Total articles:** 47  
**Articles marked as duplicates:** 33  
**Primary articles (unique content):** 14  

---

## 1. Metadata Schema

Every cleaned article file starts with a YAML metadata block:

```yaml
---
article_id: <value>
title: <value>
section: <value>
category: <value>
source_url: <value>
language: <value>
published_date: <value>
updated_date: <value>
word_count: <value>
content_status: <value>
duplicate_of: <value>
---
```

### Field definitions

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `article_id` | string | Unique slug identifier | `custom-software-development-guide` |
| `title` | string | Article title (JSON-encoded) | `"Custom Software Development Guide for Growing Businesses"` |
| `section` | string | Always `Blog & News` | `Blog & News` |
| `category` | string | Article category | `SOFTWARE DEVELOPMENT` |
| `source_url` | string | Full source URL | `https://www.xicteksystems.com/blog/custom-software-development-guide` |
| `language` | string | ISO 639-1 language code | `en` |
| `published_date` | date/null | Original publish date (YYYY-MM-DD) | `2026-09-07` |
| `updated_date` | date | Date of this cleaning | `2026-11-07` |
| `word_count` | integer | Cleaned body word count | `1289` |
| `content_status` | string | Always `cleaned` | `cleaned` |
| `duplicate_of` | string/null | Slug of primary article if this is a near-duplicate | `custom-software-development-guide` or `null` |

## 2. Sample Records — Primary Articles (Unique Content)

Five representative primary articles (no duplicates):

### Sample 1: `ai-development-company-pakistan`

```yaml
---
article_id: ai-development-company-pakistan
title: "What to Expect from an AI Development Company in Pakistan"
section: Blog & News
category: ARTIFICIAL INTELLIGENCE
source_url: https://www.xicteksystems.com/blog/ai-development-company-pakistan
language: en
published_date: 2026-09-07
updated_date: 2026-11-09
word_count: 197
content_status: cleaned
duplicate_of: null
---
```

### Sample 2: `azure-development-services`

```yaml
---
article_id: azure-development-services
title: "Azure Development Services for Modern Applications"
section: Blog & News
category: CLOUD
source_url: https://www.xicteksystems.com/blog/azure-development-services
language: en
published_date: 2026-09-07
updated_date: 2026-11-09
word_count: 174
content_status: cleaned
duplicate_of: null
---
```

### Sample 3: `business-mobile-applications`

```yaml
---
article_id: business-mobile-applications
title: "Business Mobile Applications for Teams on the Move"
section: Blog & News
category: MOBILE DEVELOPMENT
source_url: https://www.xicteksystems.com/blog/business-mobile-applications
language: en
published_date: 2026-09-07
updated_date: 2026-11-09
word_count: 1223
content_status: cleaned
duplicate_of: null
---
```

### Sample 4: `custom-software-development`

```yaml
---
article_id: custom-software-development
title: "Custom Software Development: When Bespoke Software Makes Sense"
section: Blog & News
category: SOFTWARE DEVELOPMENT
source_url: https://www.xicteksystems.com/blog/custom-software-development
language: en
published_date: 2026-09-07
updated_date: 2026-11-09
word_count: 166
content_status: cleaned
duplicate_of: null
---
```

### Sample 5: `digital-transformation-services`

```yaml
---
article_id: digital-transformation-services
title: "Digital Transformation Services That Improve Everyday Work"
section: Blog & News
category: DIGITAL TRANSFORMATION
source_url: https://www.xicteksystems.com/blog/digital-transformation-services
language: en
published_date: 2026-09-07
updated_date: 2026-11-09
word_count: 187
content_status: cleaned
duplicate_of: null
---
```

## 3. Sample Records — Duplicate Articles

Three representative duplicate articles (marked `duplicate_of` their primary):

### Sample 1: `agile-software-development` (duplicate of `software-development-cost-pakistan`)

```yaml
---
article_id: agile-software-development
title: "Agile Software Development Without Losing Direction"
section: Blog & News
category: SOFTWARE DEVELOPMENT
source_url: https://www.xicteksystems.com/blog/agile-software-development
language: en
published_date: 2026-09-07
updated_date: 2026-11-09
word_count: 1201
content_status: cleaned
duplicate_of: software-development-cost-pakistan
---
```

### Sample 2: `ai-chatbot-development` (duplicate of `future-of-ai-in-business`)

```yaml
---
article_id: ai-chatbot-development
title: "AI Chatbot Development for Useful Customer Conversations"
section: Blog & News
category: AI AND AUTOMATION
source_url: https://www.xicteksystems.com/blog/ai-chatbot-development
language: en
published_date: 2026-09-07
updated_date: 2026-11-09
word_count: 1205
content_status: cleaned
duplicate_of: future-of-ai-in-business
---
```

### Sample 3: `ai-customer-support` (duplicate of `future-of-ai-in-business`)

```yaml
---
article_id: ai-customer-support
title: "AI Customer Support: Improve Speed Without Losing Empathy"
section: Blog & News
category: AI AND AUTOMATION
source_url: https://www.xicteksystems.com/blog/ai-customer-support
language: en
published_date: 2026-09-07
updated_date: 2026-11-09
word_count: 1209
content_status: cleaned
duplicate_of: future-of-ai-in-business
---
```

## 4. Full Article Inventory

All 47 cleaned articles with metadata summary:

| # | article_id | title | category | published_date | word_count | duplicate_of |
|---|-----------|-------|----------|----------------|------------|--------------|
| 1 | agile-software-development | Agile Software Development Without  | SOFTWARE DEVELOPMENT | 2026-09-07 | 1201 | software-development-cost-pakistan |
| 2 | ai-chatbot-development | AI Chatbot Development for Useful C | AI AND AUTOMATION | 2026-09-07 | 1205 | future-of-ai-in-business |
| 3 | ai-customer-support | AI Customer Support: Improve Speed  | AI AND AUTOMATION | 2026-09-07 | 1209 | future-of-ai-in-business |
| 4 | ai-development-company-pakistan | What to Expect from an AI Developme | ARTIFICIAL INTELLIGENCE | 2026-09-07 | 197 | — |
| 5 | ai-for-smes | AI for SMEs: Practical Opportunitie | AI AND AUTOMATION | 2026-09-07 | 1219 | future-of-ai-in-business |
| 6 | ai-in-erp-systems | AI in ERP Systems: Better Decisions | AI AND AUTOMATION | 2026-09-07 | 1220 | future-of-ai-in-business |
| 7 | ai-saas-platforms | AI SaaS Platforms: Product Foundati | AI AND AUTOMATION | 2026-09-07 | 1216 | future-of-ai-in-business |
| 8 | ai-workflow-automation | AI Workflow Automation for Knowledg | AI AND AUTOMATION | 2026-09-07 | 1202 | future-of-ai-in-business |
| 9 | android-app-development | Android App Development for Real-Wo | MOBILE DEVELOPMENT | 2026-09-07 | 1210 | business-mobile-applications |
| 10 | app-maintenance-services | App Maintenance Services for Reliab | MOBILE DEVELOPMENT | 2026-09-07 | 1206 | business-mobile-applications |
| 11 | azure-development-services | Azure Development Services for Mode | CLOUD | 2026-09-07 | 174 | — |
| 12 | business-mobile-applications | Business Mobile Applications for Te | MOBILE DEVELOPMENT | 2026-09-07 | 1223 | — |
| 13 | business-process-automation | Business Process Automation: A Prac | AI AND AUTOMATION | 2026-09-07 | 1197 | future-of-ai-in-business |
| 14 | cross-platform-development | Cross Platform Development: A Pract | MOBILE DEVELOPMENT | 2026-09-07 | 1208 | business-mobile-applications |
| 15 | custom-software-development-guide | Custom Software Development Guide f | SOFTWARE DEVELOPMENT | 2026-09-07 | 1211 | software-development-cost-pakistan |
| 16 | custom-software-development | Custom Software Development: When B | SOFTWARE DEVELOPMENT | 2026-09-07 | 166 | — |
| 17 | custom-web-application-development | Custom Web Application Development  | WEB DEVELOPMENT | 2026-09-07 | 1205 | web-development-company-pakistan |
| 18 | digital-product-development | Digital Product Development: A Busi | SOFTWARE DEVELOPMENT | 2026-09-07 | 1211 | software-development-cost-pakistan |
| 19 | digital-transformation-services | Digital Transformation Services Tha | DIGITAL TRANSFORMATION | 2026-09-07 | 187 | — |
| 20 | dotnet-development-services | .NET Development Services for Busin | Uncategorized | 2026-09-07 | 153 | — |
| 21 | ecommerce-development | Ecommerce Development for Reliable  | WEB DEVELOPMENT | 2026-09-07 | 1193 | web-development-company-pakistan |
| 22 | enterprise-software-development | Enterprise Software Development for | SOFTWARE DEVELOPMENT | 2026-09-07 | 1200 | software-development-cost-pakistan |
| 23 | enterprise-web-applications | Enterprise Web Applications That Co | WEB DEVELOPMENT | 2026-09-07 | 1206 | web-development-company-pakistan |
| 24 | erp-software-development | ERP Software Development: Building  | ERP | 2026-09-07 | 185 | — |
| 25 | flutter-app-development | Flutter App Development for Cross-P | MOBILE APPS | 2026-09-07 | 153 | — |
| 26 | full-stack-development-guide | Full Stack Development Guide for Mo | WEB DEVELOPMENT | 2026-09-07 | 1205 | web-development-company-pakistan |
| 27 | future-of-ai-in-business | The Future of AI in Business: Prepa | AI AND AUTOMATION | 2026-09-07 | 1235 | — |
| 28 | generative-ai-applications | Generative AI Applications for Real | AI AND AUTOMATION | 2026-09-07 | 1207 | future-of-ai-in-business |
| 29 | ios-app-development | iOS App Development with Product Qu | MOBILE DEVELOPMENT | 2026-09-07 | 1214 | business-mobile-applications |
| 30 | mobile-app-cost-guide | Mobile App Cost Guide: What Shapes  | MOBILE DEVELOPMENT | 2026-09-07 | 1212 | business-mobile-applications |
| 31 | mobile-app-development-company | How to Evaluate a Mobile App Develo | MOBILE APPS | 2026-09-07 | 188 | — |
| 32 | mobile-app-security | Mobile App Security: Protecting Dat | MOBILE DEVELOPMENT | 2026-09-07 | 1223 | business-mobile-applications |
| 33 | mvp-development-guide | MVP Development Guide: Build the Sm | SOFTWARE DEVELOPMENT | 2026-09-07 | 1209 | software-development-cost-pakistan |
| 34 | nextjs-development-services | Next.js Development Services for Fa | WEB DEVELOPMENT | 2026-09-07 | 1201 | web-development-company-pakistan |
| 35 | portal-development | Portal Development for Customers, P | WEB DEVELOPMENT | 2026-09-07 | 1198 | web-development-company-pakistan |
| 36 | progressive-web-apps | Progressive Web Apps: When the Brow | WEB DEVELOPMENT | 2026-09-07 | 1210 | web-development-company-pakistan |
| 37 | react-development-services | React Development Services for Prod | WEB DEVELOPMENT | 2026-09-07 | 1187 | web-development-company-pakistan |
| 38 | saas-development-services | SaaS Development Services: From MVP | SAAS | 2026-09-07 | 152 | — |
| 39 | saas-product-development | SaaS Product Development from MVP t | SOFTWARE DEVELOPMENT | 2026-09-07 | 1202 | software-development-cost-pakistan |
| 40 | software-development-company-pakistan | How to Choose a Software Developmen | SOFTWARE DEVELOPMENT | 2026-09-07 | 232 | — |
| 41 | software-development-cost-pakistan | Software Development Cost in Pakist | SOFTWARE DEVELOPMENT | 2026-09-07 | 1224 | — |
| 42 | software-development-process | The Software Development Process: A | SOFTWARE DEVELOPMENT | 2026-09-07 | 1202 | software-development-cost-pakistan |
| 43 | software-maintenance-services | Software Maintenance Services: Keep | SOFTWARE DEVELOPMENT | 2026-09-07 | 1199 | software-development-cost-pakistan |
| 44 | startup-mobile-apps | Startup Mobile Apps: Validate the J | MOBILE DEVELOPMENT | 2026-09-07 | 1212 | business-mobile-applications |
| 45 | startup-software-development | Startup Software Development: From  | SOFTWARE DEVELOPMENT | 2026-09-07 | 1217 | software-development-cost-pakistan |
| 46 | web-development-company-pakistan | How to Choose a Web Development Com | WEB DEVELOPMENT | 2026-09-07 | 1216 | — |
| 47 | website-performance-optimization | Website Performance Optimization fo | WEB DEVELOPMENT | 2026-09-07 | 1209 | web-development-company-pakistan |

---

*Generated 2026-11-09 by QA Automation — Knowledge Base Cleaning & Metadata Schema*