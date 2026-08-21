# HisabDo Web App AI

Shared AI/ML development repository for **HisabDo Department 1 – Capstone Development**.

## Current AI/ML Workstreams

### 1. AI Financial Assistant / Chatbot
- LLM/NLP response flow
- RAG / knowledge-base support
- Prompting and response validation
- Financial question handling

### 2. Smart Expense Categorization
- Data preprocessing
- ML model / prediction logic
- Model evaluation
- FastAPI prediction service

### 3. AI Service / Application Integration
- FastAPI service layer
- Request/response validation
- Error handling and fallback behavior
- Integration with the HisabDo application

### 4. Testing, Research & Documentation
- Model/service testing
- Evaluation evidence
- API/model research
- Technical documentation
- Roadmap and blocker tracking

## ClickUp

Department 1 – Capstone Development:

https://app.clickup.com/90182979594/v/l/li/901820544827

Team members should check ClickUp for their exact Day 15–19 responsibilities before starting work.

## Repository Structure

```text
hisabdo-webapp-ai/
├── src/
│   ├── financial_assistant/
│   ├── expense_categorization/
│   └── integration/
├── tests/
├── data/
├── research/
├── docs/
├── .github/
│   └── pull_request_template.md
├── .gitignore
├── CONTRIBUTING.md
└── README.md
```

## Git Workflow

Do **not** develop directly on `main`.

Start from the latest `main`:

```bash
git clone https://github.com/usmankhalid172/hisabdo-webapp-ai.git
cd hisabdo-webapp-ai
git checkout main
git pull origin main
```

Create your own feature branch:

```bash
git checkout -b feature/your-name-task-name
```

Example:

```bash
git checkout -b feature/ahmed-ali-ghori-ai-chatbot
```

After making useful progress:

```bash
git add .
git commit -m "Implement <your task>"
git push -u origin feature/your-name-task-name
```

Then open a Pull Request to `main` for Team Lead review.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the complete team workflow.

## Contribution Evidence

Each member should keep traceable evidence through one or more of the following:

- GitHub branch and commits
- Pull Request
- Code contribution
- Dataset contribution
- Testing/evaluation results
- Research or technical documentation
- ClickUp progress/blocker update

## Security

Never commit:

- `.env` files
- API keys
- Access tokens
- Passwords
- Private credentials
- Sensitive user or financial data

Use environment variables and safe sample values instead.

## Workflow Note

The branch, PR, evidence, and folder workflow in this repository is the **Department 1 AI/ML Team Leads' implementation process** for organizing the management-created capstone tasks. It should not be treated as a separate management policy unless management explicitly confirms it.
