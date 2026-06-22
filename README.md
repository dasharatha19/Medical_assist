# 🏥 MediBook — AI-Powered Medical Appointment Scheduling Agent

[![CI](https://github.com/dasharatha19/Medical_assist/actions/workflows/ci.yml/badge.svg)](https://github.com/dasharatha19/Medical_assist/actions)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.1-green.svg)](https://langgraph.readthedocs.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

MediBook is a production-grade, agentic AI application for medical appointment scheduling. Built with **LangGraph**, **Groq/Gemini/OpenAI**, **PostgreSQL/Supabase**, and **Streamlit**, it orchestrates a multi-node AI workflow covering patient intake, scheduling, insurance verification, booking, reminders, and form distribution.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Streamlit UI (app/)                   │
│         3-Panel: Sidebar | Chat | Booking Status         │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│              LangGraph Agent (agents/)                   │
│  conversation_node → booking_node → reminder_node        │
│                    → form_distribution_node              │
└────────┬───────────────┬──────────────┬─────────────────┘
         │               │              │
   ┌─────▼─────┐  ┌──────▼──────┐  ┌───▼────────┐
   │ LLM Layer │  │  Tools      │  │  Database  │
   │ Groq/Gem/ │  │  booking,   │  │ PostgreSQL │
   │ OpenAI    │  │  schedule,  │  │ /Supabase  │
   └───────────┘  │  patient_  │  └────────────┘
                  │  lookup    │
                  └────────────┘
```

## ✨ Features

- 🤖 **Multi-node LangGraph agent** — conversation, booking, reminders, forms
- 🔄 **Multi-LLM support** — Groq, Gemini, OpenAI with auto-fallback
- 🗄️ **PostgreSQL + Supabase** — production-grade persistence
- 📧 **Email & reminder** automation
- 📋 **PDF form distribution** for new patients
- 🛡️ **Input validation** with rule-based fallback
- 📊 **LangSmith tracing** for observability

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 14+ (or Supabase project)
- Groq / Gemini / OpenAI API key

### 1. Clone & setup environment

```bash
git clone https://github.com/dasharatha19/Medical_assist.git
cd Medical_assist
git checkout second-comp

python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp env.example .env
# Edit .env with your keys
```

Required variables:

```env
# LLM — pick one
GROQ_API_KEY=gsk_...
# GEMINI_API_KEY=...
LLM_PROVIDER=groq

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/medibook
# OR Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=...

# Optional — LangSmith tracing
LANGCHAIN_TRACING_V2=true
LANGSMITH_API_KEY=...
LANGCHAIN_PROJECT=medibook-agent
```

### 3. Initialize database

```bash
python scripts/init_db.py
```

### 4. Run the app

```bash
streamlit run app/main.py
```

Open [http://localhost:8501](http://localhost:8501)

---

## 🐳 Docker

```bash
docker build -t medibook .
docker run -p 8501:8501 --env-file .env medibook
```

Or with compose:

```bash
docker-compose up --build
```

---

## 🧪 Testing

```bash
# All tests
pytest

# Unit tests only
pytest tests/unit/ -v

# With coverage
pytest --cov=. --cov-report=html
open htmlcov/index.html
```

---

## 📁 Project Structure

```
Medical_assist/
├── agents/               # LangGraph graph + nodes
│   ├── graph.py          # Graph wiring
│   ├── state.py          # SchedulerState TypedDict
│   └── nodes/            # conversation, booking, reminder, forms
├── app/                  # Streamlit UI
│   ├── main.py           # Entry point
│   ├── session_manager.py
│   └── ui_components.py
├── services/             # Business logic
│   ├── llm_service.py
│   ├── scheduling_service.py
│   ├── email_service.py
│   └── ...
├── tools/                # LangGraph tools
├── utils/                # Config, LLM client, validators
├── prompts/              # Prompt files (.txt)
├── database/             # DB layer (PostgreSQL)
├── tests/                # Unit + integration + API tests
├── .github/workflows/    # CI/CD
├── monitoring/           # Health checks, metrics
├── scripts/              # DB init, migrations
├── Dockerfile
├── docker-compose.yml
└── render.yaml
```

---

## 🔐 Security

- All secrets via environment variables — never hardcoded
- Input validation on all user-provided fields
- SQL injection protection via parameterized queries
- Rate limiting recommended via Nginx/reverse proxy in production

---

## 📖 Documentation

- [Architecture & Design](DOCUMENTATION.md)
- [Contributing Guide](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)
- [Roadmap](ROADMAP.md)

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). PRs welcome!

---

## 📄 License

MIT License — see [LICENSE](LICENSE)
