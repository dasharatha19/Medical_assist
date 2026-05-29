# MediBook — Technical Documentation

**Version**: 2.0  
**Last Updated**: May 2026  
**Stack**: Python 3.11 · LangGraph · Groq LLM · PostgreSQL · Streamlit · Docker

---

## Table of Contents

1. [System Architecture](#1-system-architecture)
2. [LangGraph Pipeline](#2-langgraph-pipeline)
3. [Node Reference](#3-node-reference)
4. [State Management](#4-state-management)
5. [Database Schema](#5-database-schema)
6. [Services Layer](#6-services-layer)
7. [Tools Layer](#7-tools-layer)
8. [LLM Configuration](#8-llm-configuration)
9. [UI Components](#9-ui-components)
10. [Prompt System](#10-prompt-system)
11. [Configuration Reference](#11-configuration-reference)
12. [Deployment Guide](#12-deployment-guide)
13. [Troubleshooting](#13-troubleshooting)

---

## 1. System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        MEDIBOOK SYSTEM                          │
│                                                                 │
│  ┌──────────┐    ┌──────────────────────────────────────────┐  │
│  │Streamlit │    │         LangGraph Agent Pipeline         │  │
│  │   UI     │───▶│  conversation → booking → reminder →     │  │
│  │main.py   │    │  form_distribution                       │  │
│  └──────────┘    └──────────────────┬───────────────────────┘  │
│                                     │                           │
│  ┌──────────────────────────────────▼───────────────────────┐  │
│  │                    Services Layer                        │  │
│  │  patient_service · scheduling_service · reminder_service │  │
│  │  form_distribution_service · email_service · report      │  │
│  └──────────────────────────────────┬───────────────────────┘  │
│                                     │                           │
│  ┌──────────────────────────────────▼───────────────────────┐  │
│  │                   PostgreSQL (Supabase)                  │  │
│  │  patients · doctors · doctor_slots · appointments        │  │
│  │  forms · reminders                                       │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

- **No MemorySaver** — SessionManager holds single `agent_state` dict in memory
- **PostgreSQL as source of truth** — No JSON files for data persistence
- **Prompt injection** — System prompt built dynamically with current state at each turn
- **LLM-first with rule-based fallback** — Gemini/Groq extracts fields; NLParser as fallback

---

## 2. LangGraph Pipeline

### Graph Definition (`agents/graph.py`)

```python
conversation_node → booking_node → reminder_node → form_distribution_node → END
```

### Routing Logic

```
After conversation_node:
  if booking_confirmed == True → booking_node
  else → END (wait for next user message)

After booking_node:
  if booking_success == True → reminder_node
  else → END

After reminder_node:
  → form_distribution_node (always)

After form_distribution_node:
  → END
```

### Auto-Cascade

`SessionManager.run_agent_step()` automatically runs all nodes in sequence when triggered. The entire pipeline from booking confirmation to form delivery happens in one call.

---

## 3. Node Reference

### 3.1 conversation_node

**File**: `agents/nodes/conversation_node.py`  
**Purpose**: Primary AI chatbot — collects all patient information, checks availability, handles confirmation

**Processing Steps:**
1. Pre-resolve relative dates ("tomorrow" → "2026-05-30")
2. Detect third-party booking ("my sister is sick")
3. Load doctors from PostgreSQL
4. Pre-match doctor names from user input
5. Build dynamic system prompt with current state
6. Call LLM (Groq/Gemini) → get JSON response
7. Extract fields from LLM response
8. Handle correction intent (user wants to change info)
9. Handle cancellation intent
10. Patient lookup (if name + DOB collected)
11. Availability check (if doctor + date known)
12. Validate selected time against real slots
13. Check if all fields collected → set confirming phase
14. Check if ready_to_book → set booking_confirmed

**Key State Outputs:**
```python
state["patient_name"]         # Validated full name
state["patient_dob"]          # YYYY-MM-DD format
state["patient_phone"]        # 10-digit phone
state["patient_email"]        # Valid email
state["preferred_doctor"]     # Exact doctor name from DB
state["appointment_date"]     # YYYY-MM-DD format
state["selected_time"]        # HH:MM format (from available_slots)
state["insurance_carrier"]    # Carrier name or "None"
state["booking_confirmed"]    # True when user confirms
state["available_slots"]      # List of available time strings
state["patient_id"]           # DB patient ID
state["patient_type"]         # "new" or "returning"
state["appointment_duration"] # 60 (new) or 30 (returning)
```

**System Prompt Construction:**
```python
_build_system_prompt(state, doctors_info, slots_block)
# Injects: collected fields, missing fields, available doctors,
# available slots, patient status, scheduling rules
```

---

### 3.2 booking_node

**File**: `agents/nodes/booking_node.py`  
**Purpose**: Reserves appointment slot and saves to database

**Processing Steps:**
1. Call `tools.booking.book()` → reserves slot via `DoctorAvailability`
2. Generate appointment ID (UUID 8-char)
3. Save appointment to PostgreSQL via `save_appointment(state)`
4. Generate Excel admin report via `report_service`
5. Set `current_step = "reminders"`

**Key State Outputs:**
```python
state["appointment_id"]   # e.g. "APT7F3A2B"
state["booking_success"]  # True
state["db_saved"]         # True
```

**Double-Booking Prevention:**
- `DoctorAvailability.book_slot()` checks overlap against existing appointments
- Verifies slot status in `doctor_slots` table before marking as booked

---

### 3.3 reminder_node

**File**: `agents/nodes/reminder_node.py`  
**Purpose**: Sets up reminders and creates intake form

**Processing Steps:**
1. Generate appointment ID if missing
2. Save appointment to PostgreSQL
3. Generate Excel report
4. Setup 3 reminders via `tools.reminder.setup()`
5. Create intake form with unique UUID token
6. Save form to PostgreSQL
7. Mark form as sent

**Reminder Schedule:**
| Reminder | Type | Timing |
|----------|------|--------|
| R1 | Forms Check | 48 hours before |
| R2 | General Reminder | 24 hours before |
| R3 | Confirmation | 1 hour before |

**Form Token:**
```python
form_token = str(uuid.uuid4())  # e.g. "a1b2c3d4-..."
form_url = f"https://forms.medical-scheduler.com/patient-form/{form_token}"
```

---

### 3.4 form_distribution_node

**File**: `agents/nodes/form_distribution_node.py`  
**Purpose**: Sends intake form to patient and tracks delivery

**Processing Steps:**
1. Verify booking was successful
2. Determine patient type (new → comprehensive form, returning → update form)
3. Initialize FormDistributionService
4. Create form record if not exists
5. Send form email via EmailService
6. Track delivery status
7. Set `workflow_complete = True`

**Form Types:**
- **New Patient**: Comprehensive Intake Form (8 fields including medical history)
- **Returning Patient**: Patient Update Form (3 fields)

---

## 4. State Management

### SchedulerState (`agents/state.py`)

Complete state dictionary passed through all nodes:

```python
class SchedulerState(TypedDict):
    # Patient Info
    patient_name: str
    patient_dob: str
    patient_phone: str
    patient_email: str
    patient_id: str
    patient_type: str           # "new" | "returning"
    appointment_duration: int   # 60 | 30

    # Appointment Info
    preferred_doctor: str
    appointment_date: str
    selected_time: str
    available_slots: list
    available_doctors: list

    # Insurance
    insurance_carrier: str
    insurance_member_id: str
    insurance_group_id: str

    # Booking Status
    booking_confirmed: bool
    booking_success: bool
    appointment_id: str
    workflow_complete: bool
    current_step: str

    # Forms & Reminders
    form_sent: bool
    form_url: str
    form_type: str
    reminders_setup: bool
    reminders_count: int

    # Conversation
    user_input: str
    response: str
    conversation_context: list  # [{role, content}, ...]
    conversation_phase: str     # greeting|collecting|scheduling|insurance|confirming|done
    intent: str
    missing_fields: list

    # Third-party booking
    booking_for_person: str
    booking_for_someone_else_confirmed: bool
```

---

## 5. Database Schema

### patients
```sql
CREATE TABLE patients (
    patient_id        TEXT PRIMARY KEY,
    first_name        TEXT,
    last_name         TEXT,
    full_name         TEXT,
    dob               TEXT,
    phone             TEXT,
    email             TEXT,
    insurance_carrier TEXT,
    member_id         TEXT,
    group_id          TEXT,
    last_visit        TEXT,
    patient_type      TEXT DEFAULT 'new'
);
```

### doctors
```sql
CREATE TABLE doctors (
    doctor_id      TEXT PRIMARY KEY,
    name           TEXT,
    specialization TEXT,
    location       TEXT,
    working_hours  TEXT,    -- "09:00 - 17:00"
    break_time     TEXT,    -- "12:00 - 13:00"
    conditions     TEXT     -- comma-separated conditions treated
);
```

### doctor_slots
```sql
CREATE TABLE doctor_slots (
    id          SERIAL PRIMARY KEY,
    doctor_id   TEXT REFERENCES doctors(doctor_id),
    date        TEXT,       -- "YYYY-MM-DD"
    time_slot   TEXT,       -- "HH:MM"
    status      TEXT DEFAULT 'available'  -- available|booked|break
);
```

### appointments
```sql
CREATE TABLE appointments (
    appointment_id      TEXT PRIMARY KEY,
    patient_id          TEXT,
    patient_name        TEXT,
    patient_dob         TEXT,
    patient_email       TEXT,
    patient_phone       TEXT,
    doctor_name         TEXT,
    appointment_date    TEXT,
    appointment_time    TEXT,
    duration_minutes    INTEGER,
    patient_type        TEXT,
    insurance_carrier   TEXT,
    insurance_member_id TEXT,
    insurance_group_id  TEXT,
    booking_confirmed   BOOLEAN DEFAULT FALSE,
    booking_success     BOOLEAN DEFAULT FALSE,
    reminders_setup     BOOLEAN DEFAULT FALSE,
    form_sent           BOOLEAN DEFAULT FALSE,
    status              TEXT DEFAULT 'pending',
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### forms
```sql
CREATE TABLE forms (
    form_id           TEXT PRIMARY KEY,
    appointment_id    TEXT,
    patient_id        TEXT,
    patient_name      TEXT,
    patient_email     TEXT,
    doctor            TEXT,
    appointment_date  TEXT,
    form_type         TEXT,
    form_token        TEXT,
    form_url          TEXT,
    is_new_patient    BOOLEAN DEFAULT TRUE,
    sent              BOOLEAN DEFAULT FALSE,
    sent_at           TIMESTAMP,
    completed         BOOLEAN DEFAULT FALSE,
    completed_at      TIMESTAMP,
    delivery_attempts INTEGER DEFAULT 0,
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### reminders
```sql
CREATE TABLE reminders (
    reminder_id      TEXT PRIMARY KEY,
    appointment_id   TEXT,
    patient_email    TEXT,
    patient_phone    TEXT,
    reminder_type    TEXT,   -- "Forms Check"|"General Reminder"|"Confirmation"
    scheduled_time   TIMESTAMP,
    sent             BOOLEAN DEFAULT FALSE,
    sent_at          TIMESTAMP,
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Auto-Initialization

On app startup, `initialize_database()` in `database/db.py`:
1. Creates database if not exists
2. Creates all tables if not exists
3. Runs `migrate_add_conditions()` — adds conditions column
4. Seeds patients from `data/patients.csv`
5. Seeds doctors from `data/doctor_schedules.xlsx`

---

## 6. Services Layer

### patient_service.py
```python
lookup_patient(name, dob)          # Find patient in PostgreSQL
register_new_patient(data)          # Create new patient record
update_patient_preferences(...)     # Update doctor/location preference
record_appointment(patient_id, ...) # Update last_visit, set type=returning
```

### scheduling_service.py
```python
get_available_doctors()             # Returns list of doctor dicts with conditions
check_doctor_availability(doctor, date, duration)  # Returns available slots
reserve_slot(doctor, date, time, patient_id, duration)  # Book slot
```

### reminder_service.py
```python
setup_appointment_reminders(appointment_id, datetime, email, phone)
# Creates 3 reminder records: 48h, 24h, 1h before appointment

get_appointment_reminders(appointment_id)  # Fetch reminders from DB
mark_reminder_sent(appointment_id, reminder_id)  # Update sent status
check_form_completion(appointment_id)  # Check if patient completed form
```

### form_distribution_service.py
```python
create_form_for_appointment(...)    # Generate form with unique token
send_form_email(appointment_id, email, name)  # Send via EmailService
mark_form_completed(appointment_id) # Track completion
get_form_status(appointment_id)     # Get current form status
get_pending_form_reminders()        # Forms sent but not completed
```

### report_service.py
```python
record_appointment(state)           # Append to Excel admin report
```

---

## 7. Tools Layer

Tools are thin wrappers around services, providing the LangChain tool interface:

```
tools/patient_lookup_tool.py  → patient_service.lookup_patient()
tools/schedule_checker_tool.py → scheduling_service.get_available_doctors()
                               → scheduling_service.check_doctor_availability()
tools/booking_tool.py         → scheduling_service.reserve_slot()
                               → patient_service.record_appointment()
tools/reminder_tool.py        → reminder_service.setup_appointment_reminders()
tools/notification_tool.py    → PostgreSQL direct (insurance + forms)
```

### Tool Registry (`tools/__init__.py`)
```python
tools.patient_lookup    # PatientLookupTool instance
tools.schedule_checker  # ScheduleCheckerTool instance
tools.booking           # BookingTool instance
tools.reminder          # ReminderTool instance
tools.notification      # NotificationTool instance
```

---

## 8. LLM Configuration

### Provider Priority (`utils/config.py`)

```
1. Groq      → llama-3.3-70b-versatile  (fastest, recommended)
2. Gemini    → gemini-1.5-flash          (free tier)
3. OpenAI    → gpt-4o-mini               (fallback)
4. Anthropic → claude-3-5-haiku          (final fallback)
```

### LLM Client (`utils/llm_client.py`)

```python
llm = get_llm_client()
result = llm.chat_json(prompt=prompt, system=system)
# Returns: {"intent": ..., "extracted": {...}, "response": ..., "phase": ..., "ready_to_book": bool}
```

### LLM Response Format

```json
{
    "intent": "general_question|book_appointment|provide_info|confirm|cancel|correct_info",
    "extracted": {
        "patient_name": null,
        "patient_dob": null,
        "patient_phone": null,
        "patient_email": null,
        "preferred_doctor": null,
        "appointment_date": null,
        "selected_time": null,
        "insurance_carrier": null,
        "insurance_member_id": null,
        "insurance_group_id": null,
        "has_insurance": null
    },
    "response": "Natural language response to patient",
    "phase": "greeting|collecting|scheduling|insurance|confirming|done",
    "ready_to_book": false
}
```

### Configuration Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| Temperature | 0.3 | Deterministic responses |
| Max tokens | 1000 | Response length limit |
| Timeout | 30s | API call timeout |
| Fallback | Rule-based NLP | When LLM fails |

---

## 9. UI Components

### Layout (`app/main.py`)

```
┌─────────────┬─────────────────────────┬──────────────┐
│  Left Panel │    Center (Chat)        │ Right Panel  │
│  (Sidebar)  │                         │              │
│             │  ┌───────────────────┐  │ Progress     │
│ Past Appts  │  │  Chat History     │  │ Steps 1-6    │
│             │  │                   │  │              │
│ New Conv    │  │  Bot messages     │  │ Booking      │
│             │  │  User messages    │  │ Summary      │
│             │  └───────────────────┘  │              │
│             │  ─────────────────────  │ Patient      │
│             │  Quick Reply Buttons    │ Doctor       │
│             │  ─────────────────────  │ Date         │
│             │  Your Response Input    │ Time         │
│             │                         │ Insurance    │
└─────────────┴─────────────────────────┴──────────────┘
```

### Quick Reply Components

| Component | Trigger | Options Shown |
|-----------|---------|---------------|
| Doctor buttons | Bot asks about doctor | All available doctors |
| Date buttons | Bot asks about date | 3 next weekdays |
| Slot buttons | Bot shows availability | All available slots (4-col grid) |
| Yes/No buttons | Bot asks to confirm | Yes / No |
| DOB picker | Bot asks for DOB | Calendar date picker |
| Change appointment card | User wants to modify | Step 1: Date, Step 2: Doctor |

### Progress Panel

Shows 6 steps with visual indicators:
1. Your Name
2. Patient Check
3. Pick a Date
4. Insurance
5. Confirm
6. Done!

---

## 10. Prompt System

### Files in `prompts/`

| File | Purpose |
|------|---------|
| `system_prompt.txt` | Core personality, rules, policies |
| `scheduling_prompt.txt` | Slot selection and date handling rules |
| `confirmation_prompt.txt` | Confirmation flow instructions |
| `insurance_prompt.txt` | Insurance collection rules |
| `reminder_prompt.txt` | Reminder message templates |
| `extraction_prompt.txt` | Field extraction instructions |

### Dynamic Prompt Injection

At each turn, `_build_system_prompt()` injects:

```
ALREADY COLLECTED (never ask again):
  ✅ full name: John
  ✅ date of birth: 1990-03-15

STILL NEEDED (ask one at a time):
  ❓ phone number
  ❓ insurance

AVAILABLE DOCTORS:
  - Dr. John Smith (General Practice) at Downtown Clinic | Hours: 09:00-17:00
  - Dr. Sarah Johnson (Cardiology) at Westside Medical Center | Hours: 08:00-16:00

AVAILABLE SLOTS for Dr. John Smith on 2026-05-30:
  1. 09:00  2. 09:30  3. 10:00 ...
```

### Key Prompt Policies

- **PRIORITY RULE**: Answer availability questions before collecting info
- **MEMORY RULE**: ALREADY COLLECTED is source of truth — never re-ask
- **CANCELLATION POLICY**: Save info, acknowledge warmly
- **CORRECTION POLICY**: intent=correct_info, never cancel
- **SYMPTOM MATCHING**: Route to closest doctor specialty
- **DOCTOR SUGGESTION**: Suggest, never assign without confirmation
- **BOOKING FOR SOMEONE ELSE**: Ask confirmation, collect their info

---

## 11. Configuration Reference

### `utils/config.py`

```python
Config.LLM_PROVIDER         # "groq"|"gemini"|"openai"|"anthropic"|"auto"
Config.LLM_MODEL            # Model name for active provider
Config.USE_LLM_FOR_PARSING  # True = use LLM; False = rule-based only
Config.FALLBACK_TO_RULE_BASED  # True = fallback on LLM failure
Config.get_active_provider() # Returns currently active provider
Config.get_active_model()    # Returns currently active model
Config.is_llm_enabled()      # True if LLM is configured and enabled
```

### `database/db.py`

```python
initialize_database()         # Run once on startup
get_connection()              # Returns psycopg2 connection
lookup_patient(name, dob)     # Returns patient dict or None
register_new_patient(data)    # Returns new patient_id
get_all_doctors()             # Returns list of doctor dicts
get_available_slots(doctor, date)  # Returns list of time strings
book_slot(doctor, date, time)  # Returns True/False
save_appointment(state)        # Returns appointment_id
save_form(form_data)           # Returns True
save_reminders(appointment_id, email, phone, reminders)  # Returns True
```

---

## 12. Deployment Guide

### Docker Build & Run

```bash
# Build
docker build --no-cache -t medibook .

# Run locally
docker run -p 8501:8501 --env-file .env --dns 8.8.8.8 medibook

# Access at http://localhost:8501
```

### Render.com Deployment

1. Push code to GitHub
2. In Render dashboard → New Web Service → Connect GitHub repo
3. Set environment variables (never commit real keys):
   - `GROQ_API_KEY`
   - `DATABASE_URL` (Supabase pooler URL)
   - `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
   - `LLM_ENABLED=true`
   - `LLM_PROVIDER=groq`
4. Render auto-deploys on every push to main branch

### Supabase PostgreSQL Setup

Use Session Pooler for IPv4 compatibility:
```
Host: aws-1-ap-northeast-1.pooler.supabase.com
Port: 5432
User: postgres.[project-ref]
DB:   postgres
```

Tables are auto-created on first app startup.

---

## 13. Troubleshooting

### App won't start

```
SyntaxError: f-string unmatched '('
```
**Fix**: Use single quotes inside f-strings: `f"{state.get('key')}"` not `f"{state.get("key")}"`

---

```
ModuleNotFoundError: No module named 'form_manager'
```
**Fix**: `form_manager.py` was deleted. Check `tools/notification_tool.py` imports.

---

### Database connection fails

```
could not translate host name "db.xxx.supabase.co"
```
**Fix**: Use Session Pooler URL (IPv4) not Direct Connection (IPv6):
```
aws-1-ap-northeast-1.pooler.supabase.com:5432
```

---

```
Network is unreachable (IPv6 address)
```
**Fix**: Same as above — use pooler URL.

---

### No slots available

**Cause**: `doctor_slots` table only has past dates.  
**Fix**: Run the slot generation SQL in Supabase SQL Editor:
```sql
INSERT INTO doctor_slots (doctor_id, date, time_slot, status)
SELECT 'DR_Dr_Sarah_Johnson', date_val::text, time_val, 'available'
FROM generate_series('2026-05-29'::date, '2026-07-31'::date, '1 day'::interval) AS date_val,
     unnest(ARRAY['08:00','08:30','09:00'...]) AS time_val
WHERE EXTRACT(DOW FROM date_val) BETWEEN 1 AND 5;
```

---

### LLM not responding

**Check**: `LLM_ENABLED=true` and `GROQ_API_KEY` is set correctly.  
**Fallback**: App uses rule-based NLParser if LLM fails.

---

### Booking confirmed but workflow doesn't trigger

**Cause**: `selected_time` missing — user confirmed without picking a slot.  
**Fix**: Check `conversation_node.py` step 11 — `user_confirming` detection should force availability check.

---

### Doctor buttons showing at wrong time

**Cause**: Bot message contains doctor name even in non-selection context.  
**Fix**: `render_quick_replies()` in `main.py` — check `personal_info_questions` list and `slots_already_shown` flag.

---

*For additional support, check the verbose terminal logs — the app outputs detailed node-by-node trace with state summaries.*
