# 📖 Complete Codebase Documentation

**Project:** AI-Powered Medical Appointment Scheduling System  
**Framework:** LangGraph + LangChain + Streamlit  
**Date:** May 6, 2026  
**Status:** 🟡 70% Complete - Core workflow functional, final integrations in progress

> 📌 **QUICK REFERENCE:** For project completion status, next steps, and what still needs to be done, see [PROJECT_STATUS.md](PROJECT_STATUS.md) - this is the comprehensive handoff guide.

This document provides an in-depth guide to understanding the entire codebase. Start with the section that matches your learning goal.

---

## 🎯 Quick Navigation

- [Project Overview](#project-overview) - What the system does
- [Architecture](#architecture) - How it's structured
- [Core Components](#core-components) - Deep dive into each module
- [Data Flow](#data-flow) - How data moves through the system
- [Workflow Guide](#workflow-guide) - Step-by-step appointment booking
- [Configuration](#configuration) - Setup and environment
- [API Reference](#api-reference) - Functions, classes, and services
- [Extension Guide](#extension-guide) - How to add new features
- [Debugging Guide](#debugging-guide) - Troubleshooting common issues

---

## 📋 Project Overview

### What Does It Do?

This is an **AI-powered appointment scheduling system** for medical clinics. It:

1. **Collects patient information** via conversational AI (name, DOB, contact, insurance)
2. **Checks doctor availability** in real-time
3. **Books appointments** into the doctor's schedule
4. **Sends reminders** (48h, 24h, 1h before appointment)
5. **Distributes forms** via email with unique patient links
6. **Generates reports** in Excel for admin review

### Key Capabilities

| Capability | How It Works | Where It's Implemented |
|-----------|-------------|------------------------|
| **Conversational AI** | LangGraph nodes handle multi-turn conversation | `agents/nodes/*.py` |
| **Doctor Availability** | Real-time slot checking from doctors.json | `services/scheduling_service.py` |
| **Patient Verification** | Lookup existing patients or register new ones | `services/patient_service.py` |
| **Insurance Validation** | Multi-field validation (carrier, ID, group) | `utils/validators.py` |
| **Multi-Tier Reminders** | Automated scheduling (48h, 24h, 1h) | `services/reminder_service.py` |
| **Email Distribution** | SMTP with retry logic (3 attempts) | `services/email_service.py` |
| **Unique Form URLs** | UUID tokens for security | `services/form_distribution_service.py` |
| **Excel Reports** | Multi-sheet workbook generation | `services/excel_exporter.py` |
| **Web UI** | Streamlit-based chat interface | `app/main.py` |
| **Session Persistence** | Conversations resume mid-workflow | `app/session_manager.py` |

---

## 🏗️ Architecture

### High-Level System Design

```
┌──────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                             │
│                    (Streamlit Web Chat UI)                        │
│                      app/main.py                                  │
└─────────────────────────────┬──────────────────────────────────────┘
                              │
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│                    SESSION MANAGEMENT                             │
│          (Thread ID, State Persistence, History)                 │
│              app/session_manager.py                              │
└─────────────────────────────┬──────────────────────────────────────┘
                              │
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│                    LANGGRAPH WORKFLOW                             │
│          (7 Orchestrated Nodes with State Management)            │
│                      agents/graph.py                             │
└──────────┬─────────────┬─────────────┬──────────────────────────┘
           │             │             │
    ┌──────▼────┐  ┌─────▼─────┐ ┌───▼──────────┐
    │ Node 1-2  │  │ Node 3-4  │ │ Node 5-7     │
    │ Greeting  │  │ Scheduling│ │ Confirmation,│
    │ Lookup    │  │ Insurance │ │ Reminders,   │
    │           │  │           │ │ Forms        │
    └─────┬─────┘  └─────┬─────┘ └───┬──────────┘
          │               │           │
          └───────┬───────┴─────┬─────┘
                  │             │
         ┌────────▼──────┐ ┌────▼──────────┐
         │ STATE OBJECT  │ │ TOOLS/SERVICES│
         │(43 fields)    │ │(6 services)   │
         │agents/state.py│ │services/      │
         └────────┬──────┘ └────┬──────────┘
                  │             │
          ┌───────▼─────────────▼──────┐
          │   DATA PERSISTENCE         │
          │  (JSON files + Excel)      │
          │  data/ files/              │
          └────────────────────────────┘
```

### Three-Layer Architecture

#### **Layer 1: Orchestration (Nodes)**
- **Where:** `agents/nodes/*.py` (7 files)
- **What:** Orchestrate conversation flow using LangGraph
- **Each node:**
  - Validates user input
  - Calls appropriate service
  - Updates state
  - Routes to next node

#### **Layer 2: Business Logic (Services)**
- **Where:** `services/*.py` (6 files)
- **What:** Implement business rules for each domain
- **Services:**
  - SchedulingService - Availability, booking
  - PatientService - Lookup, registration
  - ReminderService - 3-tier scheduling
  - EmailService - SMTP delivery
  - FormDistributionService - URL generation, tracking
  - ReportService - Excel generation

#### **Layer 3: Data Persistence**
- **Where:** Root directory (JSON files)
- **Files:**
  - `patients.json` - Patient registry
  - `doctors.json` - Doctor profiles, schedules
  - `appointments.json` - Booked appointments
  - `forms.json` - Form records with tokens
  - `form_delivery_log.json` - Email delivery tracking

---

## 🧩 Core Components

### 1. **LangGraph Workflow** (`agents/graph.py`)

**Purpose:** Orchestrates the 7-node appointment scheduling workflow

**Key Concept:** A `StateGraph` is a directed graph where:
- Each node is a step in the conversation
- State flows through nodes (gets updated at each step)
- Conditional edges allow branching (retry, cancel, etc.)

**The 7 Nodes:**

```python
def create_scheduler_graph():
    graph = StateGraph(SchedulerState)
    
    # 1. GREETING_NODE
    graph.add_node("greeting", greeting_node)
    
    # 2. PATIENT_LOOKUP_NODE
    graph.add_node("patient_lookup", patient_lookup_node)
    
    # 3. SCHEDULING_NODE
    graph.add_node("scheduling", scheduling_node)
    
    # 4. INSURANCE_NODE
    graph.add_node("insurance", insurance_node)
    
    # 5. CONFIRMATION_NODE
    graph.add_node("confirmation", confirmation_node)
    
    # 6. REMINDER_NODE
    graph.add_node("reminder", reminder_node)
    
    # 7. FORM_DISTRIBUTION_NODE
    graph.add_node("form_distribution", form_distribution_node)
    
    # Set edges (greeting → patient_lookup → scheduling → ...)
    graph.set_entry_point("greeting")
    graph.add_edge("greeting", "patient_lookup")
    graph.add_edge("patient_lookup", "scheduling")
    # ... etc
    
    # Conditional edges for branching
    graph.add_conditional_edges("scheduling", should_retry_scheduling, ...)
    graph.add_conditional_edges("confirmation", should_confirm, ...)
    
    return graph.compile(checkpointer=MemorySaver())
```

**Key Feature: MemorySaver Checkpointer**
- Saves state after each node completes
- Session resumes from last checkpoint (never restarts)
- Enables multi-turn conversations that pause and resume

---

### 2. **State Object** (`agents/state.py`)

**Purpose:** Central data structure flowing through all nodes (43 typed fields)

**Structure:**

```python
class SchedulerState(TypedDict):
    # ── Patient Information ──
    patient_name: str
    patient_dob: str
    patient_id: str
    patient_type: str  # "new" or "returning"
    appointment_duration: int  # minutes
    patient_email: str
    patient_phone: str
    
    # ── Scheduling ──
    preferred_doctor: str
    appointment_date: str
    available_slots: list
    selected_slot: str
    selected_time: str
    
    # ── Insurance ──
    insurance_carrier: str
    insurance_member_id: str
    insurance_group_id: str
    insurance_valid: bool
    
    # ── Appointment Booking ──
    appointment_id: str
    booking_confirmed: bool
    booking_success: bool
    
    # ── Reminders & Forms ──
    reminders_setup: bool
    reminders_count: int
    form_created: bool
    form_sent: bool
    form_token: str
    form_url: str
    
    # ── Workflow Control ──
    current_step: str
    error_message: str
    retry_count: int
    workflow_complete: bool
    user_input: str
    booking_confirmation_status: str  # "pending", "confirmed", "rejected"
```

**Usage Pattern:**
```python
def some_node(state: SchedulerState) -> SchedulerState:
    # Read from state
    name = state.get("patient_name")
    
    # Process (call service, validate, etc.)
    result = some_service.process(name)
    
    # Update state
    state["patient_name"] = result
    state["current_step"] = "next_step"
    
    return state  # Flows to next node
```

---

### 3. **Nodes** (`agents/nodes/`)

Each node is a Python file implementing one step of the workflow. All nodes follow this pattern:

```python
def node_name(state: SchedulerState) -> SchedulerState:
    """
    Step X: Description
    
    Input from state: Which fields it reads
    Output to state: Which fields it updates
    Error handling: How it handles failures
    Routing: Where it goes next (via state fields)
    """
    
    # 1. Extract input from state
    user_input = state.get("user_input")
    
    # 2. Validate input
    if not user_input:
        state["error_message"] = "Input required"
        state["retry_count"] += 1
        return state
    
    # 3. Call appropriate service
    service = SomeService()
    result = service.process(user_input)
    
    # 4. Update state
    state["field_name"] = result
    state["current_step"] = "next_step"
    
    # 5. Return (flows to next node)
    return state
```

**The 7 Nodes Explained:**

| Node | Purpose | Key Actions | Conditional Exit |
|------|---------|-----------|-----------------|
| **greeting_node** | Welcome, explain workflow | Print welcome message | Always → patient_lookup |
| **patient_lookup_node** | Collect patient info | Name, DOB, email, phone lookup | Always → scheduling |
| **scheduling_node** | Book appointment slot | List doctors, show slots, reserve | Retry up to 3x if no slots |
| **insurance_node** | Collect insurance details | Carrier, member ID, group ID | Always → confirmation |
| **confirmation_node** | Review & confirm | Display summary, ask Y/N | Y → reminder, N → END |
| **reminder_node** | Create appointment, setup reminders | Book appointment, schedule 3 reminders | Always → form_distribution |
| **form_distribution_node** | Send forms to patient | Generate UUID URL, send email | Always → END |

---

### 4. **Services** (`services/`)

Each service implements business logic for one domain. Services are **called by nodes** and **return results** (no direct state manipulation).

#### **SchedulingService** (`scheduling_service.py`)
```python
class SchedulingService:
    def get_available_doctors(self) -> list:
        """Returns list of doctor objects from doctors.json"""
    
    def check_doctor_availability(self, doctor_id: str, date: str) -> list:
        """Returns available 30-min time slots for a doctor on a date"""
    
    def reserve_slot(self, doctor_id: str, patient_id: str, date: str, time: str) -> str:
        """Reserves a slot, returns appointment_id"""
    
    def get_doctor_by_name(self, name: str):
        """Lookup doctor by name"""
```

#### **PatientService** (`patient_service.py`)
```python
class PatientService:
    def lookup_patient(self, name: str, dob: str) -> dict or None:
        """Returns patient record if exists, else None"""
    
    def register_patient(self, name: str, dob: str, email: str, phone: str) -> str:
        """Creates new patient, returns patient_id"""
    
    def is_new_patient(self, patient_id: str) -> bool:
        """True if patient has no previous appointments"""
```

#### **ReminderService** (`reminder_service.py`)
```python
class ReminderService:
    def setup_appointment_reminders(self, appointment: dict) -> bool:
        """
        Creates 3 reminders:
        - 48h before: Form completion check
        - 24h before: General appointment reminder
        - 1h before: Confirmation check
        """
    
    def check_form_completion(self, appointment_id: str) -> bool:
        """Returns True if patient completed form"""
    
    def send_reminder(self, recipient_email: str, reminder_text: str) -> bool:
        """Sends reminder email via EmailService"""
```

#### **EmailService** (`email_service.py`)
```python
class EmailService:
    def send_email(self, to: str, subject: str, body: str, 
                   html: str = None, attachments: list = None) -> bool:
        """
        Sends email via SMTP with retry logic:
        - Attempt 1: Immediate
        - Attempt 2: After 5 seconds
        - Attempt 3: After 10 seconds
        Returns True if sent successfully
        """
```

#### **FormDistributionService** (`form_distribution_service.py`)
```python
class FormDistributionService:
    def create_form_for_appointment(self, appointment: dict, patient_type: str) -> dict:
        """
        Generates unique form record:
        - Creates UUID token
        - Builds form URL: https://clinic.com/forms/{UUID}
        - Returns form object with metadata
        """
    
    def send_form_to_patient(self, patient_email: str, form: dict) -> bool:
        """Sends form URL via EmailService with retry"""
    
    def check_form_completion(self, form_token: str) -> bool:
        """Returns True if form was completed"""
```

#### **ReportService** (`report_service.py`)
```python
class ReportService:
    def generate_appointment_report(self, appointment_data: dict) -> str:
        """
        Generates Excel workbook with:
        - Appointment details
        - Patient information
        - Insurance information
        - Reminders scheduled
        Returns path to saved Excel file
        """
```

---

### 5. **Utilities** (`utils/`)

#### **Validators** (`validators.py`)
```python
class PatientDataValidator:
    @staticmethod
    def validate_name(name: str) -> tuple[bool, str]:
        """Returns (is_valid, cleaned_name)"""
    
    @staticmethod
    def validate_dob(dob: str) -> tuple[bool, datetime]:
        """Returns (is_valid, parsed_date)"""

class ContactValidator:
    @staticmethod
    def validate_email(email: str) -> bool
    @staticmethod
    def validate_phone(phone: str) -> bool

class InsuranceValidator:
    @staticmethod
    def validate_carrier(carrier: str) -> bool
    @staticmethod
    def validate_member_id(member_id: str) -> bool
```

#### **LLM Service** (`llm_service.py`)
```python
class LLMService:
    def __init__(self):
        """Initializes Google Gemini API with fallback to rule-based parser"""
    
    def extract_patient_info(self, user_input: str) -> dict:
        """
        Uses Gemini to extract:
        - Name, DOB, email, phone, doctor preference, insurance
        Fallback: Rule-based parser if Gemini unavailable
        """
```

#### **Config** (`config.py`)
```python
# Centralized configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LLM_ENABLED = os.getenv("LLM_ENABLED", "true").lower() == "true"
REQUIRE_LLM = os.getenv("REQUIRE_LLM", "false").lower() == "true"

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")

EMAIL_MAX_RETRIES = int(os.getenv("EMAIL_MAX_RETRIES", "3"))
EMAIL_RETRY_DELAY = int(os.getenv("EMAIL_RETRY_DELAY", "5"))
```

#### **Prompt Loader** (`prompt_loader.py`)
```python
def get_section_safe(prompt_file: str, section: str, default: str = "") -> str:
    """
    Loads prompt from prompts/{prompt_file}.txt
    Extracts section between markers: # ── SECTION ──
    Falls back to default if not found
    """
```

---

### 6. **Web UI** (`app/`)

#### **Main App** (`main.py`)
```python
# Streamlit web interface
st.set_page_config(page_title="MediBook", layout="centered")

if "session_manager" not in st.session_state:
    st.session_state.session_manager = SessionManager()

# Conversation loop
if user_input := st.chat_input("You:"):
    # 1. Invoke graph with current state
    result = st.session_state.session_manager.invoke(user_input)
    
    # 2. Display agent response
    st.chat_message("assistant").write(result["output"])
    
    # 3. State persists via MemorySaver
```

#### **Session Manager** (`session_manager.py`)
```python
class SessionManager:
    def __init__(self):
        """Initialize with unique thread_id for this user"""
        self.thread_id = str(uuid.uuid4())  # Unique per browser session
        self.graph = create_scheduler_graph()  # LangGraph workflow
    
    def invoke(self, user_input: str) -> dict:
        """
        1. Sets user_input in state
        2. Executes graph from last checkpoint
        3. Returns output for display
        Workflow RESUMES from last step (never restarts)
        """
        state = {"user_input": user_input}
        result = self.graph.invoke(
            state,
            config={"configurable": {"thread_id": self.thread_id}}
        )
        return result
```

---

### 7. **Tools** (`tools/`)

Tools are wrappers around services for LLM integration. Each tool:
- Takes input parameters
- Calls underlying service
- Returns structured result

```python
# booking_tool.py
@tool
def booking_tool(doctor_id: str, date: str, time: str, patient_id: str) -> str:
    """Books an appointment slot"""
    service = SchedulingService()
    appointment_id = service.reserve_slot(doctor_id, patient_id, date, time)
    return f"Appointment {appointment_id} booked"
```

---

### 8. **Prompts** (`prompts/`)

Centralized LLM prompts stored as text files:
- `system_prompt.txt` - System instructions for LLM
- `extraction_prompt.txt` - Extract patient info from input
- `scheduling_prompt.txt` - Help schedule appointments
- `insurance_prompt.txt` - Insurance info extraction
- `confirmation_prompt.txt` - Confirmation message template
- `reminder_prompt.txt` - Reminder email template

**Usage:**
```python
prompt_text = get_section_safe("extraction_prompt", "PATIENT_NAME")
```

---

## 🔄 Data Flow

### Complete Request Lifecycle

```
1. USER INPUT
   └─→ "I'd like to book an appointment with Dr. Smith on Monday at 2 PM"

2. STREAMLIT UI (app/main.py)
   └─→ Captures input, passes to SessionManager

3. SESSION MANAGER (app/session_manager.py)
   └─→ Sets state["user_input"]
   └─→ Calls graph.invoke() with thread_id

4. LANGGRAPH WORKFLOW (agents/graph.py)
   └─→ Resumes from last checkpoint via MemorySaver
   └─→ Executes next node

5. CURRENT NODE (agents/nodes/*.py)
   └─→ Reads from state["user_input"]
   └─→ Validates input
   └─→ Calls appropriate service

6. SERVICE LAYER (services/*.py)
   └─→ SchedulingService.get_available_doctors()
   └─→ SchedulingService.check_doctor_availability()
   └─→ Returns structured result

7. DATA PERSISTENCE (JSON files)
   └─→ Reads doctors.json (doctor profiles)
   └─→ Checks appointments.json (existing bookings)
   └─→ Creates entry in appointments.json (new booking)

8. STATE UPDATE (agents/state.py)
   └─→ Node updates state with:
   ├─ appointment_id: str
   ├─ appointment_date: str
   ├─ selected_time: str
   ├─ booking_confirmed: bool
   └─ current_step: "next_step"

9. ROUTING (agents/graph.py)
   └─→ Graph evaluates conditional edges
   └─→ Routes to next node (usually "insurance")

10. CHECKPOINT (MemorySaver)
    └─→ Saves state snapshot
    └─→ Session can resume here on next user input

11. OUTPUT TO UI (app/main.py)
    └─→ Formats state for display
    └─→ Shows to user: "Great! Appointment booked for Monday at 2 PM"

12. BACKGROUND PROCESSES
    └─→ ReminderService creates scheduled reminders
    └─→ EmailService queues emails
    └─→ FormDistributionService generates form URL
    └─→ ReportService creates Excel report
```

---

## 📅 Workflow Guide

### Complete Appointment Booking Flow

```
START
  ↓
┌─────────────────────────────────────┐
│ 1. GREETING NODE                    │
│ Output: "Welcome to MediBook"       │
└────────────┬────────────────────────┘
             ↓
┌─────────────────────────────────────┐
│ 2. PATIENT LOOKUP NODE              │
│ Collect: Name, DOB, Email, Phone    │
│ Action: Lookup in patients.json     │
│ Output: "Hi [Name], new/returning"  │
└────────────┬────────────────────────┘
             ↓
┌─────────────────────────────────────┐
│ 3. SCHEDULING NODE                  │
│ Collect: Doctor, Date, Time         │
│ Action: Check availability          │
│ Output: "Here are available slots"  │
│ Retry: Up to 3x if no slots         │
└────────────┬────────────────────────┘
             ↓
┌─────────────────────────────────────┐
│ 4. INSURANCE NODE                   │
│ Collect: Carrier, Member ID, etc.   │
│ Action: Validate insurance details  │
│ Output: "Insurance recorded"        │
└────────────┬────────────────────────┘
             ↓
┌─────────────────────────────────────┐
│ 5. CONFIRMATION NODE                │
│ Display: Full appointment summary   │
│ Ask: "Confirm? (Yes/No)"            │
│ Routes:                             │
│   Yes → Proceed to reminder_node    │
│   No  → END (Cancelled)             │
└────────────┬────────────────────────┘
             ↓
       [User confirms: YES]
             ↓
┌─────────────────────────────────────┐
│ 6. REMINDER NODE                    │
│ Action: Create appointment record   │
│ Action: Setup 3 reminders (48h/24h/1h)
│ Action: Generate Excel report       │
│ Output: "Appointment confirmed!"    │
└────────────┬────────────────────────┘
             ↓
┌─────────────────────────────────────┐
│ 7. FORM DISTRIBUTION NODE           │
│ Action: Generate UUID form token    │
│ Action: Create form URL             │
│ Action: Send form via email         │
│ Output: "Form sent to your email"   │
└────────────┬────────────────────────┘
             ↓
           END
             ↓
    [BACKGROUND PROCESSES]
    • Reminders scheduled (check every minute)
    • Forms tracked (check completion)
    • Excel reports generated (in files/)
```

### State Transitions Example

**After User Says:** "I'd like to book with Dr. Smith, I'm John Doe, DOB 05/15/1990"

```
Initial State:
{
  "user_input": "I'd like to book with Dr. Smith, I'm John Doe, DOB 05/15/1990",
  "current_step": "patient_lookup",
  ...
}
        ↓ patient_lookup_node processes
        ↓ PatientService.lookup_patient("John Doe", "05/15/1990")
        ↓ Found existing patient
Updated State:
{
  "user_input": "",  # Cleared
  "patient_name": "John Doe",
  "patient_dob": "05/15/1990",
  "patient_id": "P12345",
  "patient_type": "returning",  # Had previous appointment
  "appointment_duration": 30,  # Returning: 30 min
  "current_step": "scheduling",
  "error_message": "",  # No errors
  ...
}
        ↓ Graph routes to scheduling_node
        ↓ SchedulingService checks availability
        ↓ Found 3 slots on requested date
Updated State:
{
  "available_slots": ["14:00", "14:30", "15:00"],
  "current_step": "insurance",
  "preferred_doctor": "Dr. Smith",
  ...
}
        ↓ Graph routes to insurance_node
        ↓ Continues until confirmation
        ↓ User confirms: YES
Updated State:
{
  "booking_confirmed": true,
  "appointment_id": "APT20260421001",
  "booking_confirmation_status": "confirmed",
  ...
}
        ↓ Graph routes to reminder_node
        ↓ Creates 3 scheduled reminders
        ↓ Generates Excel report
        ↓ Routes to form_distribution_node
Updated State:
{
  "reminders_setup": true,
  "reminders_count": 3,
  "form_token": "a1b2c3d4-e5f6-...",
  "form_url": "https://clinic.com/forms/a1b2c3d4-e5f6-...",
  "form_sent": true,
  "workflow_complete": true,
  ...
}
        ↓ State checkpoint saved
        ↓ Session resumes here on next user input
```

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root with:

```bash
# Google Gemini LLM (Optional - can run without)
GEMINI_API_KEY=your_gemini_api_key
LLM_ENABLED=true          # Set to false to disable Gemini
REQUIRE_LLM=false         # If true, app fails without Gemini

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your_clinic_email@gmail.com
SENDER_PASSWORD=your_app_password  # Gmail: use app password, not account password
SMTP_USE_TLS=true

# Email Retry Settings
EMAIL_MAX_RETRIES=3       # Retry failed emails 3 times
EMAIL_RETRY_DELAY=5       # Start with 5-second delay, exponential backoff

# Feature Flags
TEST_MODE=false           # If true, emails not actually sent
```

### JSON Data Files

#### `doctors.json`
```json
[
  {
    "id": "DOC001",
    "name": "Dr. Smith",
    "specialization": "General Practice",
    "location": "Downtown Clinic",
    "working_hours": "09:00-17:00",
    "break_times": [{"start": "12:00", "end": "13:00"}],
    "appointments": []  # Will be populated with booked appointments
  }
]
```

#### `patients.json`
```json
[
  {
    "id": "P12345",
    "name": "John Doe",
    "dob": "1990-05-15",
    "email": "john@example.com",
    "phone": "555-0123",
    "appointments": ["APT001", "APT002"]
  }
]
```

#### `appointments.json`
```json
[
  {
    "id": "APT001",
    "patient_id": "P12345",
    "doctor_id": "DOC001",
    "date": "2026-04-25",
    "time": "14:00",
    "duration": 30,
    "status": "confirmed"
  }
]
```

#### `forms.json`
```json
[
  {
    "id": "F001",
    "appointment_id": "APT001",
    "patient_id": "P12345",
    "form_type": "new_patient",
    "token": "a1b2c3d4-e5f6-...",
    "url": "https://clinic.com/forms/a1b2c3d4-e5f6-...",
    "status": "sent",
    "sent_at": "2026-04-21T10:30:00"
  }
]
```

---

## 📡 API Reference

### Key Functions by Module

#### `agents/graph.py`
```python
def create_scheduler_graph() -> CompiledGraph:
    """Creates and compiles the 7-node workflow with MemorySaver"""

def get_graph() -> CompiledGraph:
    """Returns the compiled graph (creates if needed)"""
```

#### `services/scheduling_service.py`
```python
class SchedulingService:
    def get_available_doctors(self) -> List[Dict]:
    def check_doctor_availability(self, doctor_id: str, date: str) -> List[str]:
    def reserve_slot(self, doctor_id: str, patient_id: str, date: str, time: str) -> str:
    def get_doctor_by_name(self, name: str) -> Dict or None:
```

#### `services/patient_service.py`
```python
class PatientService:
    def lookup_patient(self, name: str, dob: str) -> Dict or None:
    def register_patient(self, name: str, dob: str, email: str, phone: str) -> str:
    def is_new_patient(self, patient_id: str) -> bool:
```

#### `services/reminder_service.py`
```python
class ReminderService:
    def setup_appointment_reminders(self, appointment: Dict) -> bool:
    def check_form_completion(self, appointment_id: str) -> bool:
    def send_reminder(self, recipient_email: str, reminder_text: str) -> bool:
```

#### `services/email_service.py`
```python
class EmailService:
    def send_email(self, to: str, subject: str, body: str, 
                   html: str = None, attachments: List[str] = None) -> bool:
```

#### `services/form_distribution_service.py`
```python
class FormDistributionService:
    def create_form_for_appointment(self, appointment: Dict, patient_type: str) -> Dict:
    def send_form_to_patient(self, patient_email: str, form: Dict) -> bool:
    def check_form_completion(self, form_token: str) -> bool:
```

#### `app/session_manager.py`
```python
class SessionManager:
    def __init__(self):
    def invoke(self, user_input: str) -> Dict:
```

---

## 🔧 Extension Guide

### Adding a New Node

1. **Create file:** `agents/nodes/new_node.py`
   ```python
   from agents.state import SchedulerState
   
   def new_node(state: SchedulerState) -> SchedulerState:
       """Step X: Description"""
       # Read from state
       user_input = state.get("user_input")
       
       # Process
       result = some_service.process(user_input)
       
       # Update state
       state["field_name"] = result
       
       return state
   ```

2. **Register in graph:** `agents/graph.py`
   ```python
   from agents.nodes.new_node import new_node
   
   graph.add_node("new_node", new_node)
   graph.add_edge("previous_node", "new_node")
   ```

3. **Update state:** `agents/state.py`
   ```python
   class SchedulerState(TypedDict):
       # Add new fields
       new_field_name: str
   ```

### Adding a New Service

1. **Create file:** `services/new_service.py`
   ```python
   class NewService:
       def __init__(self):
           self.data_file = "new_data.json"
       
       def process(self, input_data: str) -> Any:
           # Business logic here
           pass
   ```

2. **Use in node:** `agents/nodes/some_node.py`
   ```python
   from services.new_service import NewService
   
   def some_node(state: SchedulerState) -> SchedulerState:
       service = NewService()
       result = service.process(state.get("input"))
       state["output"] = result
       return state
   ```

### Adding a New Reminder Type

1. **Update config:** `utils/config.py`
   ```python
   REMINDER_TIERS = [
       {"hours_before": 48, "type": "form_check"},
       {"hours_before": 24, "type": "general"},
       {"hours_before": 1, "type": "confirmation"},
       {"hours_before": 0.5, "type": "new_type"}  # New
   ]
   ```

2. **Update template:** `prompts/reminder_prompt.txt`
   ```
   # ── NEW_TYPE ──
   Subject: Your appointment reminder
   Body: Your new type reminder text...
   ```

3. **Update service:** `services/reminder_service.py`
   ```python
   def setup_appointment_reminders(self, appointment):
       for tier in REMINDER_TIERS:
           # Send based on tier type
           if tier["type"] == "new_type":
               # Custom logic for new type
               pass
   ```

### Adding a New Validator

1. **Update validators:** `utils/validators.py`
   ```python
   class NewValidator:
       @staticmethod
       def validate_new_field(value: str) -> tuple[bool, str]:
           """Returns (is_valid, cleaned_value)"""
           # Validation logic
           return True, value.strip()
   ```

2. **Use in node:**
   ```python
   from utils.validators import NewValidator
   
   is_valid, cleaned = NewValidator.validate_new_field(user_input)
   ```

---

## 🐛 Debugging Guide

### Common Issues & Solutions

#### Issue: "Workflow keeps restarting from greeting"
**Cause:** MemorySaver checkpoint not working  
**Solution:**
- Check SessionManager creates unique thread_id: `str(uuid.uuid4())`
- Verify MemorySaver is used in graph compilation
- Check `config={"configurable": {"thread_id": self.thread_id}}` in invoke call

#### Issue: "Doctor slots not showing up"
**Cause:** Doctor availability check failing  
**Solution:**
- Verify `doctors.json` exists and has doctor records
- Check date format (YYYY-MM-DD)
- Verify doctor working hours are set
- Log SchedulingService.check_doctor_availability() output

#### Issue: "Emails not sending"
**Cause:** SMTP configuration or network issue  
**Solution:**
- Verify `.env` has correct SMTP credentials
- Gmail: Use "App Password" not account password
- Check internet connection
- Enable "Less secure app access" if using Gmail
- EmailService implements 3-attempt retry with backoff
- Check `form_delivery_log.json` for detailed logs

#### Issue: "Form tokens not unique"
**Cause:** UUID collision (extremely rare) or token reuse  
**Solution:**
- Verify uuid.uuid4() is used in FormDistributionService
- Check forms.json for duplicate tokens
- Regenerate if collision detected

#### Issue: "Reminders not sending"
**Cause:** Reminder scheduler not running  
**Solution:**
- Reminders are scheduled but need background process
- Current implementation: Scheduled data stored in JSON
- Check ReminderService.setup_appointment_reminders() execution
- Verify EmailService working first

#### Issue: "State fields are None"
**Cause:** Node not updating state properly  
**Solution:**
- Check node always returns state dict
- Verify all reads use state.get("field") with defaults
- Ensure fields are defined in SchedulerState TypedDict
- Add None checks: `if state.get("field"): ...`

### Debugging Techniques

#### 1. Enable Debug Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# In node
logger.debug(f"State at {node_name}: {state}")
```

#### 2. Inspect State Between Nodes
```python
def debug_node(state: SchedulerState) -> SchedulerState:
    print(f"=== DEBUG {state['current_step']} ===")
    print(f"User input: {state.get('user_input')}")
    print(f"Patient name: {state.get('patient_name')}")
    print(f"Error: {state.get('error_message')}")
    return state
```

#### 3. Test Service in Isolation
```python
# Test scheduling_service.py directly
from services.scheduling_service import SchedulingService

service = SchedulingService()
doctors = service.get_available_doctors()
print(doctors)  # Should see doctor list
```

#### 4. Verify JSON Files
```bash
# Check doctors.json format
python -c "import json; print(json.dumps(json.load(open('doctors.json')), indent=2))"
```

#### 5. Check Email Logs
```bash
# View form delivery log
cat form_delivery_log.json
```

---

## 📊 System Metrics

| Metric | Value | Notes |
|--------|-------|-------|
| **Nodes** | 7 | greeting, patient_lookup, scheduling, insurance, confirmation, reminder, form_distribution |
| **Services** | 6 | scheduling, patient, reminder, email, form_distribution, report |
| **State Fields** | 43 | Typed dictionary with full coverage |
| **Email Retries** | 3 | Exponential backoff: 5s → 10s → 30s |
| **Reminder Tiers** | 3 | 48h, 24h, 1h before appointment |
| **Form Security** | UUID tokens | Globally unique, unguessable URLs |
| **Workflow Duration** | 2-3 min | Typical user → confirmation |
| **Session Persistence** | MemorySaver | Resumes mid-workflow, never restarts |
| **Data Format** | JSON | Human-readable, easy to debug |
| **Excel Sheets** | 4+ | Appointments, patients, forms, reminders |

---

## 📚 Quick Reference

### Running the App

```bash
# Start web UI (Recommended)
streamlit run app/main.py

# Start CLI version
python appointment_scheduler_v2.py

# Start demo
python demo.py
```

### Key Files by Purpose

| Purpose | File |
|---------|------|
| Workflow orchestration | `agents/graph.py` |
| State definition | `agents/state.py` |
| 7 workflow steps | `agents/nodes/*.py` |
| Business logic | `services/*.py` |
| Validation | `utils/validators.py` |
| Web interface | `app/main.py` |
| Session management | `app/session_manager.py` |
| Configuration | `utils/config.py` |
| Doctor/patient data | `doctors.json`, `patients.json` |

### Import Pattern

```python
# From a node
from agents.state import SchedulerState
from services.scheduling_service import SchedulingService
from utils.validators import PatientDataValidator

# Standard imports
import json
import os
from datetime import datetime, timedelta
```

---

## 🎓 Learning Path

**If you're new to the codebase, follow this learning path:**

1. **Day 1:** Read this document (Sections: Overview → Architecture → Components)
2. **Day 2:** Read source code (Start: `agents/graph.py` → `agents/nodes/greeting_node.py`)
3. **Day 3:** Trace a workflow (User input → greeting_node → patient_lookup_node → state update)
4. **Day 4:** Understand services (Pick one: `services/scheduling_service.py`)
5. **Day 5:** Modify something (Add a new field to state, create new node)
6. **Day 6:** Debug something (Add logging, find and fix a bug)
7. **Day 7:** Extend feature (Add new reminder type or validator)

**Key concepts to master:**
- LangGraph StateGraph pattern
- MemorySaver checkpointer (session persistence)
- Layered architecture (Nodes → Services → Data)
- State TypedDict (central data structure)
- JSON file persistence (doctor/patient/appointment data)

---

## ✅ Checklist for Understanding

- [ ] Read project overview and understand what system does
- [ ] Understand the 7-node workflow and how they connect
- [ ] Know the 43 state fields and their purposes
- [ ] Can explain data flow from user input to database
- [ ] Understand how MemorySaver enables session persistence
- [ ] Know the 6 services and their responsibilities
- [ ] Can identify which file implements which feature
- [ ] Understand validators and error handling
- [ ] Know how to run the app (Streamlit, CLI, demo)
- [ ] Can trace a complete appointment booking workflow
- [ ] Know how to add a new node or service
- [ ] Can debug and fix common issues

---

## 📞 Support

**Common Questions:**

Q: Where's the email configuration?  
A: `.env` file or `utils/config.py`

Q: How do I add a new doctor?  
A: Edit `doctors.json` directly or use admin UI

Q: Can I run without Gemini API?  
A: Yes! Set `LLM_ENABLED=false` in `.env`

Q: How do I test the workflow?  
A: Run `python demo.py` to see all features

Q: Where are reminders scheduled?  
A: `ReminderService.setup_appointment_reminders()` in `services/reminder_service.py`

Q: How do I customize the UI?  
A: Edit `app/main.py` (Streamlit components)

Q: How do I change appointment duration?  
A: Modify `PatientService.register_patient()` logic for new/returning

Q: Where's the Excel report generated?  
A: `services/excel_exporter.py`, saved to `files/` directory

---

**Last Updated:** April 21, 2026  
**Status:** Production Ready ✅  
**Version:** 1.0  
