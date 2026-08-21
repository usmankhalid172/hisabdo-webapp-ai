# Contributing to HisabDo Web App AI

This guide explains the simple Git/GitHub workflow for the Department 1 AI/ML team.

## 1. Clone the Repository

```bash
git clone https://github.com/usmankhalid172/hisabdo-webapp-ai.git
cd hisabdo-webapp-ai
```

## 2. Always Start From the Latest Main Branch

Before creating a new branch:

```bash
git checkout main
git pull origin main
```

## 3. Create Your Own Feature Branch

Use this format:

```text
feature/your-name-task-name-dayXX
```

Examples:

```text
feature/rameesha-zafar-financial-assistant-prompts
feature/mehar-ali-expense-categorization-day16
feature/rimsha-mushtaq-model-evaluation-day16
feature/faiza-asif-rag-retrieval-day16
feature/niha-batool-ai-service-architecture-day15
```

Create the branch:

```bash
git checkout -b feature/your-name-task-name
```

## 4. Work Only on Your Assigned Task

Check your ClickUp assignment before starting.

Avoid changing unrelated files unless the change is required for your assigned module and coordinated with the team.

## 5. Commit Your Work

Check changed files:

```bash
git status
```

Stage files:

```bash
git add .
```

Commit with a clear message:

```bash
git commit -m "Implement expense categorization preprocessing"
```

Good commit messages describe what changed.

Avoid messages such as:

```text
update
changes
done
final
```

## 6. Push Your Feature Branch

```bash
git push -u origin feature/your-name-task-name
```

If GitHub returns a permission error, send your GitHub username and the exact error to the Team Leads. Do not create a separate project repository unless instructed.

## 7. Open a Pull Request

On GitHub:

1. Open the repository.
2. Select your pushed feature branch.
3. Click **Compare & pull request**.
4. Set the base branch to `main`.
5. Add a clear title.
6. Complete the Pull Request description/template.
7. Submit the Pull Request for review.

Do not merge your own Pull Request unless a Team Lead confirms it.

## 8. Before Continuing Work Later

Return to your branch:

```bash
git checkout -b feature/abdullah-javed-ai-chatbot-day16
```

If `main` has been updated and you need the latest changes:

```bash
git checkout main
git pull origin main
git checkout feature/your-name-task-name
git merge main
```

If you see merge conflicts and are not sure how to resolve them, stop and ask a Team Lead before forcing changes.

## 9. Files That Must Not Be Committed

Never commit:

- `.env`
- API keys
- Tokens
- Passwords
- Private credentials
- Large unnecessary generated files
- Personal or sensitive user data

Use `.env.example` only when the team agrees on environment-variable names. Put fake/example values only.

## 10. Suggested Folder Usage

### `src/financial_assistant/`
Chatbot, RAG, prompts, retrieval, LLM processing, and related service code.

### `src/expense_categorization/`
Data preprocessing, model code, prediction logic, and expense-classification service code.

### `src/integration/`
FastAPI service integration, shared request/response models, application-facing API logic, and service orchestration.

### `tests/`
Unit tests, API tests, model tests, integration tests, and test fixtures.

### `data/`
Safe sample/test datasets only. Do not commit private or sensitive data.

### `research/`
Model/API comparisons, POC notes, cost/latency research, technical alternatives, and experiment notes.

### `docs/`
Architecture, integration notes, testing evidence, roadmap, blockers, and technical documentation.

## 11. Participation Evidence

A contribution should be traceable through at least one of the following:

- Commit(s)
- Pull Request
- Code or dataset change
- Test/evaluation evidence
- Research/documentation update
- ClickUp progress/blocker update

Keep work small enough that it can be reviewed and understood.
