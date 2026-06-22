# GitHub Issues Backlog — Create These One by One

Copy-paste each block to create a GitHub Issue on your repo.

---

## 🔴 HIGH PRIORITY

### Issue #1 — [SEC] Remove personal PDF from repository
**Labels:** security, quick-win
**Description:**
`files/Data Science Intern - RagaAI.pdf` is a personal job application document committed to a public repo.
- Delete the file
- Add `files/*.pdf` to `.gitignore` (keep only `New Patient Intake Form.pdf`)
- Run `git filter-branch` or BFQ to purge from git history
**Effort:** 30 min

---

### Issue #2 — [SEC] Add prompt injection protection
**Labels:** security, ai-safety
**Description:**
User inputs are passed directly to LLM prompts. Need:
- Pattern-based detection of injection attempts
- Input length limits (max 1000 chars for scheduling chatbot)
- Strip control characters and HTML before passing to LLM
- Log flagged inputs (without PII)
**Effort:** 3 hours

---

### Issue #3 — [TEST] Add unit test suite with CI coverage gate
**Labels:** testing, ci-cd
**Description:**
Zero tests currently. Add:
- `pytest` + `pytest-cov` to dev requirements
- Unit tests for validators, routing, LLM client
- CI gate: fail if coverage < 60%
**Effort:** 4 hours

---

### Issue #4 — [CICD] Set up GitHub Actions CI pipeline
**Labels:** ci-cd, devops
**Description:**
Add `.github/workflows/ci.yml` that runs on every push/PR:
1. Lint (ruff)
2. Format check (black)
3. Unit tests
4. Docker build verification
**Effort:** 2 hours

---

### Issue #5 — [PROD] Fix .dockerignore (currently named `dockerignore`)
**Labels:** bug, devops, quick-win
**Description:**
The file is named `dockerignore` instead of `.dockerignore` — Docker ignores it.
This means `.env` files and `__pycache__` get copied into the image.
Fix: `git mv dockerignore .dockerignore`
**Effort:** 5 min

---

### Issue #6 — [PROD] Add structured logging (replace basicConfig)
**Labels:** observability, production-readiness
**Description:**
Multiple files call `logging.basicConfig()` — this conflicts in multi-module apps.
Replace with centralized structured logging using JSON format in production.
**Effort:** 3 hours

---

## 🟡 MEDIUM PRIORITY

### Issue #7 — [AI] Add LLM retry logic with tenacity
**Labels:** reliability, ai
**Description:**
LLM calls can fail transiently (rate limits, network). Add:
- `@retry` decorator from `tenacity` with exponential backoff
- Max 3 retries, 2s initial wait
- Log retry attempts
**Effort:** 2 hours

---

### Issue #8 — [OBS] Add LangSmith tracing to all nodes
**Labels:** observability, ai
**Description:**
LangSmith env vars are set but nodes aren't decorated with tracing.
Add `@traceable` decorator or use LangGraph's native LangSmith integration.
**Effort:** 2 hours

---

### Issue #9 — [PROD] Add health check endpoint
**Labels:** production-readiness, devops
**Description:**
Render `healthCheckPath: /` just checks HTTP 200 from Streamlit.
Add a proper `/health` endpoint that checks:
- DB connectivity
- LLM availability
- Config validity
Can use FastAPI sidecar or Streamlit custom endpoint.
**Effort:** 4 hours

---

### Issue #10 — [AI] Externalize and version prompts
**Labels:** ai, maintainability
**Description:**
Prompts are in `prompts/*.txt` — good start. Improvements:
- Add prompt version header in each file (`# v1.2`)
- Track which prompt version was used per conversation (log it)
- Allow runtime prompt reload without app restart
**Effort:** 3 hours

---

## 🟢 LOW PRIORITY

### Issue #11 — [SCALE] Redis session store
**Labels:** scalability, architecture
**Description:**
Currently `st.session_state` ties sessions to a single Streamlit process.
Replace with Redis for multi-instance support.
**Effort:** 8 hours

### Issue #12 — [MCP] Design MCP server interface
**Labels:** mcp, architecture, enhancement
**Description:**
Define which tools to expose via MCP:
- `check_availability(doctor, date)` → available slots
- `book_appointment(patient_data)` → appointment ID
- `get_patient_history(patient_id)` → appointment list
Create architecture doc and implementation plan.
**Effort:** 8 hours

### Issue #13 — [FEAT] Multi-language support (Hindi/Kannada)
**Labels:** enhancement, ai
**Description:**
Add language detection and response in Hindi/Kannada for Indian patients.
Use Groq's multilingual models.
**Effort:** 16 hours
