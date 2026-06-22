# Contributing to MediBook

Thank you for your interest in contributing! This guide will help you get set up.

## 🏗️ Development Setup

```bash
git clone https://github.com/dasharatha19/Medical_assist.git
cd Medical_assist && git checkout second-comp
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
pip install ruff black isort pytest pytest-cov pytest-mock
cp env.example .env  # Fill in your keys
```

## 🌿 Branching Strategy

```
main          ← production-ready, protected
  └── second-comp   ← main dev branch (your current one)
        └── feat/short-description   ← feature branches
        └── fix/short-description    ← bug fix branches
        └── chore/short-description  ← maintenance
```

**Always branch off `second-comp`, open PR back to `second-comp`.**

## ✅ Before Submitting a PR

Run these locally:

```bash
# Format
black .
isort .

# Lint
ruff check .

# Tests
pytest tests/unit/ -v

# Security
bandit -r . -x tests/
```

All must pass. CI will block merging otherwise.

## 📝 Commit Message Convention

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add retry logic to booking node
fix: handle empty email in validator
chore: update requirements.txt
docs: improve README setup section
test: add unit tests for LLM client
refactor: extract prompt loading to utility
```

## 🔐 Security Rules

- **NEVER** commit `.env` files or API keys
- **NEVER** hardcode credentials anywhere in code
- **NEVER** log sensitive patient data
- All patient data handling must use parameterized queries

## 🧪 Writing Tests

- Unit tests go in `tests/unit/` — no external dependencies
- Integration tests go in `tests/integration/` — require DB
- Mock all LLM calls in unit tests with `unittest.mock`
- Test file naming: `test_<module_name>.py`

## 📋 PR Checklist

- [ ] Tests added/updated
- [ ] No secrets or API keys committed
- [ ] `ruff`, `black`, `isort` pass
- [ ] PR description explains what and why
- [ ] Linked to a GitHub Issue (if applicable)
