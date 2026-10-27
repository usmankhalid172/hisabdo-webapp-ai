# Content Cleaning — Careers & Job Openings

**Owner:** 4. Muhammad Daniyal  
**Task:** Content Cleaning — Careers & Job Openings  
**Objective:** Standardize recruitment details, hiring FAQs, and job opening descriptions into a consistent layout format. Filter out outdated application links, expired notices, and stale text.

## 1. Executive Summary

This task cleans public recruitment information associated with XICTEK Systems and HisabDo. The objective is to make career information easier for an AI retrieval system to understand while preventing expired notices or outdated application instructions from being presented as current openings.

The current public XICTEK Careers page lists four openings: Senior Full-Stack Developer, Mobile App Developer, Cloud Solutions Architect, and UI/UX Designer. It also provides an internship-program link. citeturn0search1

The HisabDo Careers page is handled separately because its 60-Day Remote Internship Bootcamp 2026 cohort was scheduled to start on August 1, 2026, and that date has passed. The page says no separate job openings are listed and asks candidates to contact the team about future opportunities. citeturn0search0

## 2. Sources Reviewed

- XICTEK Careers: https://www.xicteksystems.com/careers
- XICTEK Internship Program: https://www.xicteksystems.com/careers/internship
- HisabDo Careers: https://hisabdo.app/careers
- XICTEK About: https://www.xicteksystems.com/about
- HisabDo Company: https://hisabdo.app/company

## 3. Cleaning Rules

1. Keep roles explicitly listed as current openings.
2. Keep job title, employment type, work mode, and listed skills/technologies.
3. Keep current internship requirements and program structure.
4. Separate active roles from expired cohorts.
5. Do not treat an old “Apply Now” link as proof that a role is still open.
6. Do not invent salary, closing dates, benefits, locations, or hiring guarantees.
7. Remove promotional slogans and decorative website text from factual job chunks.
8. Preserve official source URLs for traceability.
9. Mark dated notices as time-sensitive and revalidate them before indexing as current.
10. Keep placeholder form values out of company facts.
11. Keep each job role independently retrievable.

## 4. Current XICTEK Openings

### ROLE_01 — Senior Full-Stack Developer

**Status:** Current opening as listed on the Careers page  
**Employment:** Full-time  
**Work mode:** Remote  
**Listed technologies:** React, Next.js, .NET, PostgreSQL  
**Source:** https://www.xicteksystems.com/careers

**Clean retrieval text:** XICTEK Systems currently lists a Senior Full-Stack Developer role as a full-time remote position. The page lists React, Next.js, .NET, and PostgreSQL with the role. citeturn0search1

### ROLE_02 — Mobile App Developer

**Status:** Current opening as listed on the Careers page  
**Employment:** Full-time  
**Work mode:** Remote  
**Listed technologies:** Flutter, React Native, iOS, Android  
**Source:** https://www.xicteksystems.com/careers

**Clean retrieval text:** XICTEK Systems currently lists a Mobile App Developer role as a full-time remote position. The page lists Flutter, React Native, iOS, and Android with the role. citeturn0search1

### ROLE_03 — Cloud Solutions Architect

**Status:** Current opening as listed on the Careers page  
**Employment:** Full-time  
**Work mode:** Remote  
**Listed technologies:** Azure, AWS, DevOps, Terraform  
**Source:** https://www.xicteksystems.com/careers

**Clean retrieval text:** XICTEK Systems currently lists a Cloud Solutions Architect role as a full-time remote position. The page lists Azure, AWS, DevOps, and Terraform with the role. citeturn0search1

### ROLE_04 — UI/UX Designer

**Status:** Current opening as listed on the Careers page  
**Employment:** Full-time  
**Work mode:** Remote  
**Listed skills/tools:** Figma, Design Systems, Prototyping  
**Source:** https://www.xicteksystems.com/careers

**Clean retrieval text:** XICTEK Systems currently lists a UI/UX Designer role as a full-time remote position. The page lists Figma, Design Systems, and Prototyping with the role. citeturn0search1

## 5. Current XICTEK Internship Program

The official XICTEK Internship Program describes a 12-week structured internship with real projects, mentorship, code reviews, and a possible path to a full-time role for strong candidates. citeturn0search9

**Program:** 12-week structured internship  
**Target applicants:** Current students or recent graduates in CS, SE, or a related program  
**Requirements:** Basic programming knowledge, eagerness to learn, willingness to take on challenges, strong communication/teamwork, and ability to commit to the full program  
**Benefits:** Real projects, mentorship, team collaboration, career development  
**Application review:** The page says applications are reviewed within 3–5 business days  
**Source:** https://www.xicteksystems.com/careers/internship

### Learning roadmap

- Weeks 1–2: Onboarding, codebase walkthrough, tools setup, team introduction.
- Weeks 3–6: Guided development, real tasks, mentorship, code reviews.
- Weeks 7–10: Independent contribution, feature work, production deployments.
- Weeks 11–12: Capstone, presentation, feedback, and discussion of next steps. citeturn0search9

## 6. HisabDo Careers — Expired/Time-Sensitive Content

The HisabDo Careers page states that the 60-Day Remote Internship Bootcamp 2026 cohort was scheduled for August–September 2026 with a start date of August 1, 2026. That date has passed. The page also says there are no separate job openings listed and asks candidates to confirm future internship availability with the team. citeturn0search0

### HISTORICAL_INTERNSHIP_2026

**Program:** 60-Day Remote Internship Bootcamp — 2026 Cohort  
**Published schedule:** August–September 2026  
**Start date:** August 1, 2026  
**Mode:** Remote / Work From Home  
**Status:** EXPIRED / HISTORICAL  
**Source:** https://hisabdo.app/careers

**Ingestion rule:** Keep as historical/time-sensitive content only. Do not present it as a currently open cohort without confirmation.

### CURRENT_HISABDO_CAREERS_STATUS

**Separate job openings:** None listed on the HisabDo Careers page.  
**Future internship availability:** Confirm with the team.  
**Contact:** hisabdo.app@gmail.com  
**Source:** https://hisabdo.app/careers

## 7. Company Culture Guidelines

### CULTURE_01 — Collaborative Culture
XICTEK describes a supportive environment where team members can contribute ideas and have their voice heard. citeturn0search1

### CULTURE_02 — Continuous Learning
The Careers page describes regular training, workshops, and learning opportunities. citeturn0search1

### CULTURE_03 — Meaningful Work
The company describes its work as building products that solve real problems for real people. citeturn0search1

### CULTURE_04 — Career Growth
XICTEK describes career growth through mentorship and clear growth paths. citeturn0search1

### CULTURE_05 — Remote Friendly
The Careers page describes flexible work arrangements as part of its workplace approach. citeturn0search1

### CULTURE_06 — Practical Product Thinking
The XICTEK About page emphasizes useful products, real operational problems, direct communication, visible trade-offs, and continuous improvement. citeturn0search4

## 8. Standardized Layout

```text
ROLE_ID:
Company:
Job Title:
Status:
Employment Type:
Work Mode:
Skills / Technologies:
Requirements:
Responsibilities:
Benefits:
Application:
Source URL:
Freshness:
QA Notes:
```

For culture:

```text
CULTURE_ID:
Company:
Theme:
Description:
Source URL:
Freshness:
QA Notes:
```

For dated notices:

```text
NOTICE_ID:
Company:
Program / Notice:
Original Date:
Status:
Current Availability:
Source URL:
QA Rule:
```

## 9. Metadata Schema

| Field | Purpose | Example |
|---|---|---|
| section | Website section | careers |
| content_type | Semantic type | job_opening |
| company | Organization | XICTEK Systems |
| role_id | Stable identifier | ROLE_01 |
| status | Current state | active |
| employment_type | Job arrangement | full_time |
| work_mode | Location arrangement | remote |
| skills | Listed technologies | React; Next.js; .NET; PostgreSQL |
| source_url | Official source | XICTEK Careers |
| freshness | Temporal state | current |
| qa_status | Cleaning state | verified_from_source |

## 10. Outdated Content Filtering

Filter, archive, or mark as historical:

- Expired internship cohorts.
- Past application deadlines.
- Closed job listings.
- Broken or redirected application links.
- Old “Apply Now” destinations that no longer correspond to a role.
- Dated hiring announcements.
- Temporary recruitment campaigns.
- Old mock-interview availability notices.
- Any role no longer listed on the current official Careers page.

The HisabDo August–September 2026 internship is the key example because its published start date has passed. citeturn0search0

## 11. Retrieval Examples

| User Query | Expected Result |
|---|---|
| What jobs is XICTEK hiring for? | Four current XICTEK roles listed on Careers. |
| Is there a senior developer role? | Senior Full-Stack Developer. |
| What technologies are listed for the mobile role? | Flutter, React Native, iOS, Android. |
| Is the Cloud Architect role remote? | Yes, as listed on Careers. |
| What is XICTEK's internship program? | Current 12-week internship program. |
| What happened to the HisabDo 2026 internship? | Historical/expired; confirm future opportunities. |
| What is the company culture? | Collaboration, learning, meaningful work, career growth, remote-friendly work, practical thinking. |
| Can I use an old application link? | Do not rely on it; use the current official Careers/application route. |

## 12. QA Checklist

- [x] Current XICTEK roles identified from the official Careers page.
- [x] Each current role has a separate structured block.
- [x] Employment type and work mode are preserved.
- [x] Listed technologies/skills are preserved.
- [x] Current XICTEK internship is separated from the older HisabDo cohort.
- [x] HisabDo August–September 2026 internship is marked historical/expired.
- [x] No salary, closing date, or hiring guarantee has been invented.
- [x] Promotional wording is excluded from factual job records.
- [x] Company culture is separated from job-opening records.
- [x] Source URLs are preserved.
- [x] Freshness/status is explicit.
- [x] Retrieval examples are defined.

## 13. Final Status

**STATUS: CLEANED, STANDARDIZED, AND READY FOR CAREER-CONTENT INGESTION**

The recruitment content has been separated into active roles, current internship information, company-culture guidance, and historical/time-sensitive notices. This structure is designed to prevent the AI assistant from presenting an expired internship cohort or stale recruitment notice as an active opportunity.

**Operational rule:** Before each production refresh, re-check the official Careers pages and application destinations. A role should be treated as active only when the current official source still lists it.
