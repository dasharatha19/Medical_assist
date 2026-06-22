# MediBook — Product Roadmap

> Organized by priority. Each item tagged with effort estimate.

---

## 🔴 HIGH PRIORITY (Do These First)

### Security & Secrets
- [ ] **[SEC-01]** Add `detect-secrets` pre-commit hook — *1 hour*
- [ ] **[SEC-02]** Remove `files/Data Science Intern - RagaAI.pdf` from repo (personal file leaked) — *15 min*
- [ ] **[SEC-03]** Rotate any API keys that may have been committed historically — *30 min*
- [ ] **[SEC-04]** Add input sanitization for prompt injection (strip `\n`, `ignore previous instructions`) — *3 hours*
- [ ] **[SEC-05]** Parameterize all DB queries (audit for any f-string SQL) — *2 hours*

### Testing
- [ ] **[TEST-01]** Set up pytest + CI coverage gate at 60% — *2 hours*
- [ ] **[TEST-02]** Unit tests for all validators — *3 hours*
- [ ] **[TEST-03]** Unit tests for routing logic — *2 hours*
- [ ] **[TEST-04]** Mock-based tests for LLM client — *2 hours*

### Production Readiness
- [ ] **[PROD-01]** Add `/health` endpoint (FastAPI sidecar or Streamlit custom component) — *4 hours*
- [ ] **[PROD-02]** Structured JSON logging with `structlog` — *3 hours*
- [ ] **[PROD-03]** Add retry logic with `tenacity` to LLM calls — *2 hours*
- [ ] **[PROD-04]** Graceful error messages in UI (no raw tracebacks to user) — *2 hours*

---

## 🟡 MEDIUM PRIORITY (Next Sprint)

### CI/CD
- [ ] **[CICD-01]** GitHub Actions: lint + test + docker build on every PR — *3 hours*
- [ ] **[CICD-02]** Auto-deploy to Render on merge to `main` — *2 hours*
- [ ] **[CICD-03]** Weekly dependency vulnerability scan — *1 hour*
- [ ] **[CICD-04]** Codecov integration for coverage tracking — *1 hour*

### Observability
- [ ] **[OBS-01]** LangSmith tracing on all agent nodes — *2 hours*
- [ ] **[OBS-02]** Cost tracking per session (tokens used × price) — *4 hours*
- [ ] **[OBS-03]** Agent success rate dashboard — *6 hours*
- [ ] **[OBS-04]** Prometheus metrics endpoint for Grafana — *6 hours*

### AI Quality
- [ ] **[AI-01]** Prompt versioning system (prompts tracked like code) — *4 hours*
- [ ] **[AI-02]** Output schema validation with Pydantic before state update — *4 hours*
- [ ] **[AI-03]** Hallucination guard: check doctor names against known list — *3 hours*
- [ ] **[AI-04]** Conversation evaluation with LangSmith datasets — *8 hours*

---

## 🟢 LOW PRIORITY (Future Enhancements)

### MCP Integration
- [ ] **[MCP-01]** Expose scheduling agent as MCP server — *8 hours*
- [ ] **[MCP-02]** MCP tool: `check_availability(doctor, date)` — *4 hours*
- [ ] **[MCP-03]** MCP tool: `book_appointment(patient_data)` — *4 hours*
- [ ] **[MCP-04]** MCP tool: `get_patient_history(patient_id)` — *4 hours*

### Scalability
- [ ] **[SCALE-01]** Redis session store (replace Streamlit session_state) — *8 hours*
- [ ] **[SCALE-02]** Connection pooling with `pgbouncer` or `asyncpg` — *4 hours*
- [ ] **[SCALE-03]** Multi-user support with auth (Streamlit-Authenticator) — *12 hours*
- [ ] **[SCALE-04]** Async LLM calls to reduce latency — *8 hours*

### Features
- [ ] **[FEAT-01]** WhatsApp reminder integration (Twilio) — *8 hours*
- [ ] **[FEAT-02]** Calendar sync (Google Calendar API) — *12 hours*
- [ ] **[FEAT-03]** Multi-language support (Hindi, Kannada) — *16 hours*
- [ ] **[FEAT-04]** Voice input via Whisper API — *12 hours*
- [ ] **[FEAT-05]** Admin dashboard for clinic staff — *24 hours*

---

## ⚡ Quick Wins (< 1 hour each)

| Task | Time |
|------|------|
| Remove personal PDF from `files/` | 15 min |
| Add `__init__.py` test files | 10 min |
| Fix `.dockerignore` (rename from `dockerignore`) | 5 min |
| Add `PYTHONPATH` to `.env.example` | 5 min |
| Pin `websockets` to exact version | 5 min |
| Add `ruff.toml` config file | 15 min |
| Add `tests/__init__.py` | 2 min |
