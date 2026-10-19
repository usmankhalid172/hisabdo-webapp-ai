# Deployment and Configuration Guide

## Prerequisites
Use the project's supported Python environment and install dependencies from `requirements.txt`.

## Local Setup
1. Open the repository root in VS Code.
2. Create a local `.env` based on `.env.example`.
3. Configure the required environment variables for the selected provider.
4. Never commit `.env`, API keys, or production secrets.
5. Run the relevant automated tests before starting the service.

## Configuration
Review `.env.example` for the available settings. Depending on the deployment, these may include:
- `SERVICE_NAME` and `SERVICE_VERSION`
- `INTERNAL_SERVICE_TOKEN`
- `LLM_PROVIDER`
- Provider API keys such as `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, or `GROQ_API_KEY`
- Categorization and confidence thresholds
- Dataset and transaction-limit settings
- Allowed origins for the Xictek widget, if applicable

Only configure credentials for the selected provider. Use strong, unique production secrets and store them in the deployment platform's secret manager.

## Local Run
From the repository root, run:

`.\.venv312\Scripts\python.exe -m uvicorn src.main:app --reload --port 8000`

The reload option is intended for local development, not production.

## Pre-deployment Checklist
- Confirm required environment variables are set.
- Confirm production secrets are not committed.
- Run relevant unit, integration, retrieval, and security tests.
- Verify authentication, authorization, and cross-account data isolation.
- Review logs for accidental exposure of secrets or financial data.
- Obtain team lead review and QA sign-off before release.

## Production Warning
Production server settings, database connectivity, migrations, and deployment infrastructure must be verified against the actual target environment. This guide alone does not confirm production readiness.
