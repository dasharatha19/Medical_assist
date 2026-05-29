# 🏥 MediBook — AI Medical Appointment Scheduling Assistant

MediBook is an intelligent conversational AI agent that automates medical appointment scheduling. Built with LangGraph, Groq LLM, and PostgreSQL, it handles the complete booking workflow through natural conversation — from patient greeting to appointment confirmation, reminders, and intake forms.

**Live Demo**: https://medical-assistant-57o7.onrender.com

---

## ✨ Features

- **Natural Conversation** — Handles typos, informal language, and messy input
- **Smart Patient Detection** — Automatically identifies new vs returning patients (60min vs 30min slots)
- **Third-Party Booking** — Detects booking for family members ("my sister is sick")
- **Doctor Matching** — Fuzzy matching, symptom-to-doctor routing, female/male doctor preference
- **Real-Time Availability** — 30-min slots with break time, overlap, and DB conflict detection
- **Insurance Collection** — Optional insurance with carrier/member ID/group ID
- **3-Tier Reminders** — Automated reminders at 48h, 24h, and 1h before appointment
- **Intake Forms** — Auto-generated forms with unique tokens sent after confirmation
- **Admin Reports** — Excel export of all appointments
- **Multi-Provider LLM** — Groq → Gemini → OpenAI → Anthropic fallback chain
- **Quick Reply Buttons** — Doctor, date, time slot, insurance, yes/no buttons in UI
- **DOB Date Picker** — Calendar widget for date of birth

---

## 🏗️ Architecture

```
User Message
     ↓
┌─────────────────────────────────────────────┐
│           4-Node LangGraph Pipeline          │
│                                             │
│  1. conversation_node                       │
│     • Collects patient info via Groq LLM    │
│     • Doctor selection & availability       │
│     • Insurance collection                  │
│     • Sets booking_confirmed = True         │
│              ↓                              │
│  2. booking_node                            │
│     • Reserves slot in PostgreSQL           │
│     • Generates Excel admin report          │
│     • Sets booking_success = True           │
│              ↓                              │
│  3. reminder_node                           │
│     • Saves 3 reminders to DB               │
│     • Creates intake form with token        │
│     • Saves appointment to DB               │
│              ↓                              │
│  4. form_distribution_node                  │
│     • Sends form via email                  │
│     • Tracks delivery status                │
│     • Sets workflow_complete = True         │
└─────────────────────────────────────────────┘
     ↓
PostgreSQL (Supabase)
```

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| UI | Streamlit |
| Agent Framework | LangGraph |
| Primary LLM | Groq (llama-3.3-70b-versatile) |
| Fallback LLMs | Gemini, OpenAI, Anthropic |
| Database | PostgreSQL (Supabase) |
| ORM | psycopg2 |
| Deployment | Docker + Render.com |
| Language | Python 3.11 |

---

## 🚀 Quick Start

### Option 1 — Local Setup

**Prerequisites:** Python 3.11+, PostgreSQL

```bash
# 1. Clone the repo
git clone https://github.com/your-username/medical-assistant.git
cd medical-assistant

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp env.example .env
# Edit .env with your keys (see Environment Variables section)

# 5. Run the app
streamlit run app/main.py
```

Open http://localhost:8501

---

### Option 2 — Docker

```bash
# Build image
docker build -t medibook .

# Run with env file
docker run -p 8501:8501 --env-file .env medibook
```

Open http://localhost:8501

---

### Option 3 — Render Deployment

1. Push code to GitHub
2. Connect repo to Render.com
3. Set environment variables in Render dashboard
4. Render auto-deploys on every push

---

## ⚙️ Environment Variables

Create a `.env` file with these variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `LLM_ENABLED` | Enable LLM | `true` |
| `LLM_PROVIDER` | LLM provider | `groq` |
| `GROQ_API_KEY` | Groq API key | `gsk_...` |
| `GEMINI_API_KEY` | Gemini API key | `AIza...` |
| `OPENAI_API_KEY` | OpenAI API key | `sk-...` |
| `DB_HOST` | PostgreSQL host | `aws-1-ap-northeast-1.pooler.supabase.com` |
| `DB_PORT` | PostgreSQL port | `5432` |
| `DB_NAME` | Database name | `postgres` |
| `DB_USER` | Database user | `postgres.xxxx` |
| `DB_PASSWORD` | Database password | `your_password` |
| `DATABASE_URL` | Full connection URL | `postgresql://...` |
| `LANGCHAIN_TRACING_V2` | LangSmith tracing | `false` |
| `LANGSMITH_API_KEY` | LangSmith key | `ls_...` |

---

## 📁 Project Structure

```
medical-assistant/
├── agents/                    # LangGraph pipeline
│   ├── graph.py               # 4-node workflow definition
│   ├── state.py               # SchedulerState TypedDict
│   └── nodes/
│       ├── conversation_node.py   # AI chatbot + info collection
│       ├── booking_node.py        # Slot reservation
│       ├── reminder_node.py       # Reminders + form creation
│       └── form_distribution_node.py  # Form delivery
│
├── app/                       # Streamlit UI
│   ├── main.py                # Entry point + UI layout
│   ├── session_manager.py     # Session orchestration
│   ├── ui_components.py       # Chat components
│   └── conversation_helper.py # Message formatting
│
├── services/                  # Business logic
│   ├── patient_service.py     # Patient lookup/registration
│   ├── scheduling_service.py  # Doctor availability
│   ├── reminder_service.py    # Reminder management
│   ├── form_distribution_service.py  # Form lifecycle
│   ├── email_service.py       # Email sending
│   ├── report_service.py      # Excel reporting
│   └── excel_exporter.py      # Excel generation
│
├── tools/                     # LangChain tool wrappers
│   ├── patient_lookup_tool.py
│   ├── schedule_checker_tool.py
│   ├── booking_tool.py
│   ├── reminder_tool.py
│   └── notification_tool.py
│
├── database/
│   └── db.py                  # All PostgreSQL operations
│
├── utils/                     # Utilities
│   ├── config.py              # LLM configuration
│   ├── llm_client.py          # Universal LLM client
│   ├── llm_provider.py        # Provider auto-detection
│   ├── validators.py          # Input validation
│   ├── nl_parser.py           # Rule-based NLP fallback
│   └── verbose_logger.py      # Terminal logging
│
├── prompts/                   # LLM system prompts
│   ├── system_prompt.txt      # Core instructions
│   ├── scheduling_prompt.txt  # Scheduling rules
│   ├── confirmation_prompt.txt # Confirmation flow
│   ├── insurance_prompt.txt   # Insurance collection
│   └── reminder_prompt.txt    # Reminder messages
│
├── data/
│   ├── patients.csv           # 50 synthetic patients
│   └── doctor_schedules.xlsx  # Doctor schedule template
│
├── doctor_availability.py     # Slot generation logic
├── Dockerfile                 # Container definition
├── render.yaml                # Render deployment config
├── requirements.txt           # Python dependencies
└── .env.example               # Environment template
```

---

## 💬 Sample Conversation

```
User: hi i need an appointment with dr sarah for tomorrow, 
      my name is John and dob is 15 march 1990

Bot:  Dr. Sarah Johnson is available tomorrow! I've noted 
      your details. Here are available slots:
      1. 08:00  2. 08:30  3. 09:00 ...
      Would you like to book one?

User: 09:00 please, no insurance

Bot:  To confirm:
      Patient: John | DOB: 1990-03-15
      Doctor: Dr. Sarah Johnson | Date: 2026-05-30 | Time: 09:00
      Insurance: Self Pay
      Shall I confirm this appointment?

User: yes

Bot:  🎉 Appointment Confirmed!
      ID: APT7F3A2B
      3 reminders scheduled ✅
      Intake form sent to your email 📋
```

---

## 🗄️ Database Schema

| Table | Purpose |
|-------|---------|
| `patients` | Patient records (name, DOB, contact, insurance) |
| `doctors` | Doctor info (specialization, hours, conditions) |
| `doctor_slots` | Available/booked time slots |
| `appointments` | Confirmed appointment records |
| `forms` | Intake form tracking |
| `reminders` | Scheduled reminder records |

Tables are auto-created on first run via `initialize_database()`.

---

## 🧪 Testing the App

```bash
# Test the full booking flow:
# 1. Open http://localhost:8501
# 2. Say: "I need an appointment with Dr. John Smith for tomorrow"
# 3. Provide name, DOB, phone, email when asked
# 4. Select a time slot
# 5. Say "no insurance" or provide insurance details
# 6. Confirm the appointment

# Test returning patient:
# Use name "Aarav Sharma" and DOB "1990-03-15"
# Bot should detect as returning patient (30min slot)
```

---

## 📝 License

This project was built as part of the Internship case study.

---

## 👤 Author

Dasharatha R
