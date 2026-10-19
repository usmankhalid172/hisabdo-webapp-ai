# Deployment and Configuration Guide

## Scope
This guide covers the AI service repository. Confirm the deployment entry point and required settings against the current root `README.md`, `src/financial_assistant/README.md`, and `.env.example`. Do not assume that the AI service is already connected to the production HisabDo application.

## Prerequisites
- A supported Python version for the project.
- Git and access to the repository.
- The project's approved environment configuration.
- Provider credentials only if the selected LLM provider requires them.
- Access to the trusted upstream application backend for end-to-end integration testing.

## Local Setup (Windows PowerShell)

From the repository root:

```powershell
python --version
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If the financial assistant has additional dependencies required by its documented setup, review and install `src/financial_assistant/requirements.txt` as appropriate. Avoid installing conflicting versions without checking the project's dependency requirements.

## Configuration
1. Review `.env.example` and the current configuration module.
2. Create a local environment configuration using only the variables documented by the project.
3. Set a strong, non-empty internal service token in the approved secret configuration.
4. Configure the selected LLM provider only when required.
5. Never commit a real `.env` file or secrets.
6. Ensure the upstream backend validates the user's login/session before sending authenticated identity to the AI service.

The service uses the `X-Internal-Token` header for trusted service requests and `X-Authenticated-User-ID` for the user identity supplied by the trusted backend. The second header is not proof of a valid login on its own.

## Validation

Run the automated tests:

```powershell
python -m pytest -q
```

Validate the FAQ JSON:

```powershell
python -c "import json; json.load(open('data/faq_docs.json', encoding='utf-8')); print('FAQ JSON is valid')"
```

Check the root and module README files for the authoritative application startup command, required environment variables, and health-check endpoint before starting the service. This guide intentionally does not invent an entry-point command.

## Deployment Checklist
- [ ] Dependencies installed using the documented project setup.
- [ ] Environment variables checked against `.env.example` and the configuration code.
- [ ] Secrets stored securely and excluded from version control.
- [ ] Full automated test suite passes; warnings and skips reviewed.
- [ ] Health check and service startup verified in the target environment.
- [ ] Internal service token configured securely.
- [ ] Upstream authentication and user identity integration verified end-to-end.
- [ ] Cross-user access isolation tested with authorized test accounts.
- [ ] Live provider operation checked if applicable.
- [ ] Logs, monitoring, rollback, and secret rotation procedures confirmed.
- [ ] Team lead review and QA sign-off recorded.

## Rollback
Follow the team's release procedure to redeploy the last known-good version. Do not roll back by copying unreviewed backup data into the knowledge base. Verify the service health check and critical security tests after rollback.

## Deployment Status
This document is a setup and verification guide, not evidence that production deployment has occurred. Environment-specific commands and upstream application integration must be confirmed by the project team.
