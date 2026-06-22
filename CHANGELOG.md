# Changelog

All notable changes to MediBook are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
Versioning: [Semantic Versioning](https://semver.org/)

---

## [Unreleased]

### Planned
- FastAPI health check endpoints
- Prometheus metrics export
- Rate limiting middleware
- MCP server integration
- Test coverage >80%

---

## [0.3.0] — 2026-06 (second-comp branch)

### Added
- Multi-LLM provider support: Groq, Gemini, OpenAI with auto-detection
- `LLMClient` universal client with singleton pattern
- LangSmith tracing integration via `LANGCHAIN_TRACING_V2`
- Supabase integration alongside PostgreSQL
- `render.yaml` for one-click Render deployment
- Prompt files externalized to `prompts/` directory
- `SchedulerState` with full session isolation via `session_id`
- Form distribution node for new patient PDF intake

### Changed
- Streamlit 3-panel layout: sidebar + chat + booking status
- Config system refactored to class-based with auto-provider detection
- Database layer upgraded to psycopg2 with parameterized queries

### Fixed
- UI flickering issue from frequent Streamlit reruns
- Protobuf / grpcio dependency conflicts in requirements.txt

---

## [0.2.0] — 2026-05

### Added
- LangGraph multi-node architecture (conversation → booking → reminders → forms)
- Email service for appointment confirmations
- Excel exporter for appointment reports
- Doctor availability checker from XLSX
- Insurance verification step in conversation flow

---

## [0.1.0] — 2026-04

### Added
- Initial LangGraph scheduling agent
- Basic Streamlit chat interface
- Groq API integration
- PostgreSQL schema for appointments
- Patient lookup and booking tools
