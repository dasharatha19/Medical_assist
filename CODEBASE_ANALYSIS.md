# Medical Assistant Codebase - Comprehensive Analysis

**Last Updated**: May 14, 2026  
**Status**: 70% Complete (Core workflow functional)  
**LLM Providers**: Groq (primary), Gemini, OpenAI, Anthropic (fallback chain)

---

## 📊 Current Project Status

| **Component** | **Status** | **Details** |
|---|---|---|
| **Core Workflow** | ✅ Functional | 4-node LangGraph (greeting → conversation → reminders → forms) |
| **Patient Collection** | ✅ Functional | LLM-driven intelligent conversation |
| **Scheduling** | ✅ Functional | Doctor selection, date/time picking with availability check |
| **Insurance** | ✅ Functional | Integrated into conversation node |
| **Confirmation** | ✅ Functional | Review & booking confirmation |
| **Appointment Booking** | ✅ Functional | Local database operations |
| **Reminders** | ✅ Functional | Email & SMS setup (requires SMTP config) |
| **Form Distribution** | 🟡 Partial | Form creation working, UI integration pending |
| **Demo/Packaging** | 🟡 In Progress | Submission deadline: Sept 6, 2026 |

**Overall**: 70% complete, production-ready for core features

---

## 1. Complete File Inventory

| **Category** | **Files** | **Purpose** |
|---|---|---|
| **Core App** | `main.py` | Streamlit UI with sidebar, chat, and right panels |
| | `session_manager.py` | Manual node orchestration & state routing |
| | `ui_components.py` | Chat/form UI rendering |
| | `conversation_helper.py` | Message formatting & history |
| **LangGraph** | `agents/graph.py` | 4-node state machine with conditional routing |
| | `agents/state.py` | SchedulerState TypedDict (complete workflow state) |
| **Agent Nodes** | `greeting_node.py`, `patient_lookup_node.py`, `scheduling_node.py`, `reminder_node.py`, `form_distribution_node.py` | 4-5 sequential nodes for appointment workflow |
| **Services** | `llm_service.py` | Unified multi-provider LLM (Groq, Gemini, OpenAI, Anthropic) |
| | `patient_service.py`, `scheduling_service.py`, etc. | 8 active business logic services |
| **Utils** | `config.py` | Configuration loader (env vars) |
| | `gemini_parser.py`, `nl_parser.py` | LLM & rule-based field extraction |
| | `prompt_loader.py`, `validators.py` | Prompts & validation |
| **Data** | `patients.json`, `doctors.json`, `forms.json` | Local databases |

---

## 2. How session_manager.py Calls Agent Nodes

### Key Insight
SessionManager **bypasses LangGraph** and manually routes to nodes based on state:

```python
def run_agent_step(self, user_input: str):
    # Manual dispatch based on current_step
    node_fn = self._get_current_node()  # Returns correct node function
    result = node_fn(self.agent_state)  # Direct function call (not graph)
    self.agent_state.update(result)
    
    # Auto-trigger subsequent nodes without waiting for user input
    if self.agent_state.get("collecting_step") == "lookup":
        result2 = patient_lookup_node(self.agent_state)
        self.agent_state.update(result2)
```

### Node Invocation Pattern
Each node:
- Takes `SchedulerState` dict as input
- Returns updated state dict with `response` field for UI
- Uses sub-step tracking (`collecting_step`, `scheduling_step`, etc.)
- Sets `current_step` to control workflow progression

### Routing Logic
```python
def _get_current_node(self):
    """Routes to correct node based on state"""
    current_step = self.agent_state.get("current_step", "")
    collecting_step = self.agent_state.get("collecting_step", "")
    
    if collecting_step and collecting_step != "done":
        return patient_lookup_node
    if not self.agent_state.get("patient_name"):
        return patient_lookup_node
    if current_step == "scheduling":
        return scheduling_node
    if current_step == "insurance":
        return insurance_node
    if current_step == "confirmation":
        return confirmation_node
    if current_step == "reminders":
        return reminder_node
    if current_step == "form_distribution":
        return form_distribution_node
```

---

## 3. LLM/AI Integrations in utils/

### **gemini_parser.py** - Google Gemini API Integration

```python
class LLMService:
    def __init__(self):
        """
        Intelligent multi-provider orchestration (NEW - May 2026)
        Priority: Groq → Gemini → OpenAI → Anthropic → NLParser
        """
        self.providers = [
            GroqProvider(),        # PRIMARY - llama-3.3-70b-versatile
            GeminiProvider(),      # FALLBACK
            OpenAIProvider(),      # TERTIARY
            AnthropicProvider()    # QUATERNARY
        ]
        self.fallback = NLParser() # FINAL FALLBACK - Rule-based regex
    
    def parse_patient_info(self, user_input: str):
        """Try each provider in order until one succeeds"""
        for provider in self.providers:
            if not provider.enabled:
                continue
            try:
                result = provider.extract_fields(user_input)
                if result.success:
                    return result
            except Exception:
                continue
        return self.fallback.extract_fields(user_input)
```

**Purpose**: Routes requests to best available LLM, graceful fallback chain

### **groq_parser.py** - Groq LLM Integration (PRIMARY - NEW)

```python
class GroqProvider:
    def __init__(self, api_key: Optional[str] = None):
        """
        Groq llama-3.3-70b-versatile (PRIMARY CHOICE)
        - Fastest inference, free tier available
        - Best for real-time medical applications
        - Auto-selected if GROQ_API_KEY set
        """
        self.api_key = api_key or os.getenv('GROQ_API_KEY')
        self.model = "llama-3.3-70b-versatile"
        self.temperature = 0.3
        self.max_tokens = 500
        self.enabled = bool(self.api_key)
```

**Purpose**: Primary LLM parser - fastest, most reliable for real-time use

### **gemini_parser.py** - Google Gemini API Integration (FALLBACK)

```python
class GeminiProvider:
    def __init__(self, api_key: Optional[str] = None):
        """
        Initializes Gemini (Fallback to Groq)
        - Gets API key from: parameter → env var → config
        - Falls back gracefully if package missing
        """
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        self.model_name = 'gemini-pro'
        self.temperature = 0.3
        self.max_tokens = 500
        self.enabled = bool(self.api_key)
```

**Purpose**: Secondary LLM parser (attempted if Groq fails)

### **nl_parser.py** - Rule-Based Natural Language Parser

```python
class NLParser:
    @staticmethod
    def extract_name(user_input: str) -> Optional[str]:
        """
        Regex patterns for name extraction:
        - "My name is John Smith"
        - "I am John Smith"
        - "John Smith" (direct)
        - Returns capitalized name or None
        """
        patterns = [
            r'(?:my name is|i am|call me)\s+([A-Z][a-zA-Z\s\.]+)',
            r'(?:my name is|i am|call me)\s+"(.+?)"',
        ]
    
    @staticmethod
    def extract_dob(user_input: str) -> Optional[str]:
        """
        Handles multiple date formats:
        - 1990-05-15 (YYYY-MM-DD)
        - 05/15/1990 (MM/DD/YYYY)
        - May 15, 1990 (Month DD, YYYY)
        - Returns YYYY-MM-DD or None
        """
    
    @staticmethod
    def extract_phone(user_input: str) -> Optional[str]:
        # Normalize phone numbers
    
    @staticmethod
    def extract_email(user_input: str) -> Optional[str]:
        # Email regex validation
```

**Purpose**: Lightweight regex-based field extraction. Used as fallback when Gemini unavailable.

### **prompt_loader.py** - Dynamic Prompt Management

```python
class PromptLoader:
    def __init__(self, prompts_dir: str = None):
        """Dynamically loads prompts from prompts/ folder"""
        self.prompts_dir = Path(prompts_dir or "prompts")
        self._cache: Dict[str, str] = {}
    
    def load_prompt(self, name: str) -> str:
        """Load entire prompt file (e.g., 'system_prompt')"""
        # Returns full content of prompts/system_prompt.txt
    
    def get_section(self, prompt_name: str, section: str) -> str:
        """Extract specific [SECTION: NAME] from prompt file"""
        # Parses sections marked with tags like [SECTION: HEADER]
```

**Prompt Files Used**:
- `system_prompt.txt` - Overall system instructions
- `extraction_prompt.txt` - Field extraction instructions
- `scheduling_prompt.txt` - Doctor/time selection prompts
- `insurance_prompt.txt` - Insurance collection prompts
- `confirmation_prompt.txt` - Confirmation display
- `reminder_prompt.txt` - Reminder messaging

---

## 4. Parser Files - Specific Purposes

| **File** | **Input** | **Output** | **Method** |
|---|---|---|---|
| **gemini_parser.py** | Free-form user text | JSON with 10 fields (name, DOB, email, etc.) | Gemini API call |
| **nl_parser.py** | Structured or free-form text | Extracted field or None | Regex patterns |

### Data Flow

```
User Input → LLMService.parse_patient_info()
  ├─ Try: Gemini API (if enabled)
  │  └─ Success? Return parsed JSON
  └─ Fallback: NLParser (rule-based)
     └─ Extract name, DOB, phone, email via regex
```

---

## 5. API Keys Configuration in .env (Current)

```bash
# .env file - Multi-Provider LLM Support
LLM_ENABLED=true

# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=medibook
DB_USER=postgres
DB_PASSWORD=postgres123

# Set ANY of these — system auto-detects in priority order
GEMINI_API_KEY=AIzaSyAZJtmaA7HIyQFHbE6h3noSYxDotMDEvu4
GROQ_API_KEY=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  
OPENAI_API_KEY=your_key
ANTHROPIC_API_KEY=your_key

# Force a specific provider (optional)
LLM_PROVIDER=groq  # gemini|groq|openai|anthropic|auto
```

### LLM Provider Priority (Auto-Detection)

```
1. GROQ (llama-3.3-70b-versatile) - PRIMARY
   ├─ Fastest & free tier available
   ├─ Best for real-time applications
   └─ ✅ Currently active
   
2. GEMINI (gemini-pro) - FALLBACK
   ├─ Reliable, good quality
   └─ Backup if Groq fails
   
3. OPENAI (gpt-3.5-turbo) - TERTIARY
4. ANTHROPIC (claude) - QUATERNARY
5. Rule-Based NLParser - FINAL FALLBACK (no API needed)
```

### Configuration Properties (from utils/config.py)

```python
# LLM Settings
LLM_ENABLED: bool = True               # Enable/disable LLM
LLM_PROVIDER: str = 'auto'             # Provider selection strategy
LLM_TEMPERATURE: float = 0.3           # Creativity (0.0-2.0)
LLM_MAX_TOKENS: int = 500              # Max response length
LLM_TIMEOUT: int = 10                  # Request timeout (seconds)

# Feature Flags
USE_LLM_FOR_PARSING: bool = True       # Use LLM for field extraction
USE_LLM_FOR_DOCTOR_SELECTION: bool = True
USE_LLM_FOR_INSURANCE: bool = True
FALLBACK_TO_RULE_BASED: bool = True    # Fallback to regex if all LLMs fail
REQUIRE_LLM_SUCCESS: bool = False      # Must use LLM (no fallback)

# Supported Providers
GEMINI_API_KEY: Optional[str]
GROQ_API_KEY: Optional[str]
OPENAI_API_KEY: Optional[str]
ANTHROPIC_API_KEY: Optional[str]

# Validation
@classmethod
def get_active_provider(cls) -> str:
    """Returns active provider in priority order: groq → gemini → openai → anthropic → rule-based"""
```

---

## 6. How LangGraph graph.py Works

### Graph Architecture (4-Node Workflow - Current)

```python
def create_scheduling_graph():
    graph = StateGraph(SchedulerState)
    
    # 4 Core Agent Nodes
    graph.add_node("greeting",          greeting_node)
    graph.add_node("conversation",      patient_lookup_node)  # Intelligent multi-step collection
    graph.add_node("reminders",         reminder_node)         # Book appointment, set reminders
    graph.add_node("form_distribution", form_distribution_node) # Send forms
    
    # Linear Edges
    graph.add_edge("greeting",          "conversation")
    graph.add_edge("conversation",      "reminders")
    
    # Conditional: Only proceed if booking confirmed
    def should_send_forms(state):
        if state.get("booking_confirmed", False):
            return "form_distribution"
        return END
    
    graph.add_conditional_edges(
        "reminders",
        should_send_forms,
        {"form_distribution": "form_distribution", END: END}
    )
    
    graph.add_edge("form_distribution", END)
    
    graph.set_entry_point("greeting")
    
    # In-memory checkpoint for state persistence
    checkpointer = MemorySaver()
    return graph.compile(checkpointer=checkpointer)
```

### Workflow Flow (Current - Simplified)

```
greeting (init)
    ↓
conversation (intelligent multi-turn dialog)
    ├─ Collect: name, DOB, email, phone (LLM-driven natural flow)
    ├─ Collect: doctor preference, date, time (with availability checking)
    ├─ Collect: insurance info (optional)
    └─ Confirm appointment details
    ↓
reminders (book appointment, send confirmation)
    ├─ Book via tools.booking.book()
    ├─ Setup email/SMS reminders
    ├─ Generate Excel report
    └─ If confirmed → send forms
    ↓
form_distribution (create & send post-appointment forms)
    ├─ Determine form type (new vs returning patient)
    ├─ Create form with patient data
    └─ Send via email
    ↓
END (workflow complete)
```

### Key Architecture Changes (vs Previous 7-Node Model)

| Aspect | Previous (7 Nodes) | Current (4 Nodes) |
|---|---|---|
| **Nodes** | greeting → patient_lookup → scheduling → insurance → confirmation → reminders → forms | greeting → conversation → reminders → forms |
| **Patient Collection** | Sequential (name → DOB → phone → email one per turn) | Intelligent dialog (LLM understands context) |
| **Decision Making** | Hardcoded state transitions | LLM-driven + hardcoded fallback |
| **Insurance Handling** | Separate node | Integrated into conversation |
| **Confirmation** | Separate node | Integrated into conversation |
| **UI Complexity** | High (7 node transitions) | Low (4 transitions, cleaner) |

### Key Features

- ✅ **Intelligent conversation node**: LLM drives multi-step collection naturally
- ✅ **Fewer state transitions**: Reduced complexity, cleaner flow
- ✅ **Conditional termination**: Stops if patient rejects confirmation
- ✅ **MemorySaver checkpoint**: In-memory state persistence
- ✅ **Multi-provider LLM support**: Groq → Gemini → OpenAI → Anthropic → Rule-based fallback

---

## 7. Service Layer Interactions

### Data Flow Architecture

```
SessionManager (Orchestrator)
    ↓
Agent Nodes (State manipulation)
    ├─ Patient Lookup Node
    │   ├─ calls → patient_service.lookup_patient()
    │   └─ calls → tools.patient_lookup.lookup()
    │
    ├─ Scheduling Node
    │   ├─ calls → tools.schedule_checker.get_doctors()
    │   ├─ calls → tools.schedule_checker.check_availability()
    │   └─ calls → scheduling_service.reserve_slot()
    │
    ├─ Insurance Node
    │   └─ calls → tools.notification.get_valid_carriers()
    │
    ├─ Reminder Node
    │   ├─ calls → tools.booking.book()
    │   ├─ calls → report_service.record_appointment()
    │   └─ calls → tools.reminder.setup()
    │
    └─ Form Distribution Node
        ├─ calls → form_distribution_service.create_form_for_appointment()
        └─ calls → form_distribution_service.send_form_email()
```

### Key Service Examples

**LLMService** (Unified Parser):
```python
class LLMService:
    def parse_patient_info(self, user_input: str) -> Tuple[bool, Dict]:
        """Try Gemini first, fallback to rule-based"""
        if self.use_llm:
            success, fields = parse_with_gemini(user_input)
            if success:
                return True, fields
        
        if not self.require_llm:
            return self._parse_patient_info_rulebased(user_input)
        
        return False, {}
```

**PatientService**:
```python
class PatientService:
    def lookup_patient(self, name: str, dob: str) -> dict:
        """Returns: {found, patient_id, is_new, status, duration}"""
        result = self.db.search_patient_by_details(name, dob)
        if result:
            return {'found': True, 'is_new': False, ...}
        else:
            patient_id = self.db.register_new_patient(name, dob, '', '')
            return {'found': False, 'is_new': True, ...}
```

---

## 8. Agent Nodes Workflow - Complete Conversation Flow

### Detailed Node Walkthrough

#### **1️⃣ greeting_node**
```python
def greeting_node(state):
    """Initialize state, don't print"""
    state["current_step"] = "patient_lookup"
    state["error_message"] = ""
    return state
# SessionManager shows greeting UI separately
```

#### **2️⃣ patient_lookup_node**
```python
def patient_lookup_node(state):
    """Collects patient info ONE FIELD PER TURN"""
    
    # Track progress with state.collecting_step
    if not state.get("collecting_step"):
        state["collecting_step"] = "name"
    
    # STEP 1: Collect Name
    if state["collecting_step"] == "name":
        valid, name = PatientDataValidator.validate_name(user_input)
        if valid:
            state["patient_name"] = name
            state["collecting_step"] = "dob"
            state["response"] = "📅 What is your date of birth? (YYYY-MM-DD)"
        else:
            state["response"] = f"⚠️ Invalid name. {remaining} attempts left"
    
    # STEP 2: Collect DOB
    elif state["collecting_step"] == "dob":
        valid, dob = PatientDataValidator.validate_dob(user_input)
        if valid:
            state["patient_dob"] = dob
            state["collecting_step"] = "phone"
            state["response"] = "📞 Please enter your phone number"
        # ...retry logic
    
    # STEP 3: Collect Phone
    elif state["collecting_step"] == "phone":
        # Similar validation, move to email
    
    # STEP 4: Collect Email
    elif state["collecting_step"] == "email":
        # Similar validation, then lookup patient
        lookup_result = tools.patient_lookup.lookup(name, dob)
        state["patient_id"] = lookup_result["patient_id"]
        state["patient_type"] = "new" if lookup_result["is_new"] else "returning"
        state["appointment_duration"] = lookup_result["duration_minutes"]
        
        state["collecting_step"] = "done"
        state["current_step"] = "scheduling"
        state["response"] = "✅ Moving to scheduling..."
```

#### **3️⃣ scheduling_node**
```python
def scheduling_node(state):
    """Selects doctor → date → time slot"""
    
    # STEP 1: Show Doctors
    if state["scheduling_step"] == "show_doctors":
        doctors = tools.schedule_checker.get_doctors()
        state["available_doctors"] = doctors
        state["scheduling_step"] = "select_doctor"
        state["response"] = "👨‍⚕️ **Available Doctors:**\n1. Dr. John Smith\n2. Dr. Sarah Johnson\n..."
    
    # STEP 2: Collect Doctor Selection
    elif state["scheduling_step"] == "select_doctor":
        doctor = parse_selection(user_input)  # "1" → Dr. John Smith
        state["preferred_doctor"] = doctor
        state["scheduling_step"] = "select_date"
        state["response"] = "📅 What date do you prefer? (YYYY-MM-DD)"
    
    # STEP 3: Collect Date
    elif state["scheduling_step"] == "select_date":
        date = validate_date(user_input)
        availability = tools.schedule_checker.check_availability(
            doctor=state["preferred_doctor"],
            date=date,
            duration=state["appointment_duration"]
        )
        if not availability["available"]:
            # Retry or suggest alternative date
        else:
            state["appointment_date"] = date
            state["available_slots"] = availability["slots"]
            state["scheduling_step"] = "select_time"
    
    # STEP 4: Collect Time Slot
    elif state["scheduling_step"] == "select_time":
        time_slot = validate_time(user_input, state["available_slots"])
        state["selected_time"] = time_slot
        state["selected_slot"] = time_slot
        state["scheduling_step"] = "done"
        state["current_step"] = "insurance"
        state["response"] = "✅ Scheduling confirmed. Moving to insurance..."
```

#### **4️⃣ insurance_node**
```python
def insurance_node(state):
    """Collects insurance info"""
    
    # STEP 1: Ask Insurance Coverage
    if state["insurance_step"] == "ask_coverage":
        state["insurance_step"] = "collect_coverage_answer"
        state["response"] = "🏥 Do you have health insurance? (yes/no)"
    
    # STEP 2: Handle Yes/No
    elif state["insurance_step"] == "collect_coverage_answer":
        is_yes = validate_yes_no(user_input)
        
        if not is_yes:
            state["insurance_carrier"] = "None"
            state["insurance_step"] = "done"
            state["current_step"] = "confirmation"
            state["response"] = "✅ Noted — no insurance. Moving to confirmation..."
        else:
            # Get insurance carriers
            carriers = tools.notification.get_valid_carriers()
            state["available_carriers"] = carriers
            state["insurance_step"] = "select_carrier"
    
    # STEP 3: Select Carrier
    elif state["insurance_step"] == "select_carrier":
        # Similar multi-step collection for:
        # - Carrier name
        # - Member ID
        # - Group ID
```

#### **5️⃣ confirmation_node**
```python
def confirmation_node(state):
    """Review appointment & confirm"""
    
    if state["confirmation_step"] == "show_summary":
        # Build summary from all collected fields
        summary = f"""
        📋 **Appointment Summary**
        
        **Patient:** {state["patient_name"]}
        **Date of Birth:** {state["patient_dob"]}
        **Email:** {state["patient_email"]}
        **Phone:** {state["patient_phone"]}
        
        **Doctor:** {state["preferred_doctor"]}
        **Date:** {state["appointment_date"]}
        **Time:** {state["selected_time"]}
        **Duration:** {state["appointment_duration"]} minutes
        
        **Insurance:** {state["insurance_carrier"]}
        **Member ID:** {state["insurance_member_id"] or 'N/A'}
        
        ✅ Confirm? (yes/no)
        """
        
        state["confirmation_step"] = "collect_answer"
        state["response"] = summary
    
    elif state["confirmation_step"] == "collect_answer":
        is_confirmed = validate_yes_no(user_input)
        
        if is_confirmed:
            state["booking_confirmed"] = True
            state["current_step"] = "reminders"
            state["response"] = "🎉 Confirmed! Booking appointment..."
        else:
            state["workflow_complete"] = True
            state["response"] = "❌ Booking cancelled."
```

#### **6️⃣ reminder_node**
```python
def reminder_node(state):
    """Book appointment, set reminders, generate report"""
    
    # 1. BOOK APPOINTMENT
    booking_result = tools.booking.book(
        patient_id=state["patient_id"],
        doctor=state["preferred_doctor"],
        date=state["appointment_date"],
        time=state["selected_time"],
        duration=state["appointment_duration"]
    )
    
    state["appointment_id"] = booking_result["appointment_id"]
    state["booking_success"] = True
    
    # 2. GENERATE EXCEL REPORT
    report_service.record_appointment(state)
    
    # 3. SETUP REMINDERS (email/SMS)
    reminder_result = tools.reminder.setup(
        patient_id=state["patient_id"],
        appointment_id=state["appointment_id"],
        appointment_date=state["appointment_date"],
        appointment_time=state["selected_time"],
        email=state["patient_email"],
        phone=state["patient_phone"]
    )
    
    state["reminders_setup"] = reminder_result["success"]
    state["current_step"] = "form_distribution"
    state["response"] = f"""
    🎉 **Appointment Confirmed & Booked!**
    **Appointment ID:** {state["appointment_id"]}
    **Doctor:** {state["preferred_doctor"]}
    **Date:** {state["appointment_date"]}
    **Time:** {state["selected_time"]}
    """
```

#### **7️⃣ form_distribution_node**
```python
def form_distribution_node(state):
    """Create and send forms to patient"""
    
    # Determine form type (new vs returning patient)
    is_new_patient = state["patient_type"].lower() == 'new'
    
    # Create form for appointment
    form_service = get_form_distribution_service()
    form = form_service.create_form_for_appointment(
        appointment_id=state["appointment_id"],
        patient_id=state["patient_id"],
        patient_name=state["patient_name"],
        is_new_patient=is_new_patient
    )
    
    state["form_created"] = True
    state["form_token"] = form["form_token"]
    state["form_url"] = form["form_url"]
    
    # Send form via email
    form_service.send_form_email(
        appointment_id=state["appointment_id"],
        patient_email=state["patient_email"],
        form=form
    )
    
    state["form_sent"] = True
    state["workflow_complete"] = True
    state["response"] = f"""
    📋 **Forms Sent!**
    Please check your email for appointment forms.
    **Form URL:** {state["form_url"]}
    """
```

---

## Complete Request Flow (4-Node Simplified)

```
User Types "John" 
    ↓
main.py renders UI → calls SessionManager.run_agent_step("John")
    ↓
greeting_node initializes state → routes to conversation
    ↓
conversation_node (intelligent multi-step)
    ├─ LLM (Groq → Gemini → OpenAI → Anthropic) analyzes input
    ├─ Extracts patient info in natural flow
    ├─ Auto-collects: name, DOB, email, phone
    ├─ Auto-selects: doctor, date, time (with availability check)
    ├─ Auto-collects: insurance (optional)
    └─ Confirms appointment details
    ↓
When booking_confirmed=True:
    ↓
reminder_node
    ├─ Books appointment via tools.booking.book()
    ├─ Generates Excel report
    ├─ Sets up email/SMS reminders
    └─ Routes to form_distribution
    ↓
form_distribution_node
    ├─ Creates appointment forms (new vs returning)
    └─ Sends via email
    ↓
workflow_complete=True → Show completion message
```

---

## Key Architectural Insights

1. **LangGraph orchestration**: 4-node state machine for clean workflow organization
2. **Intelligent conversation node**: LLM-driven multi-step collection (more natural than sequential)
3. **Multi-provider LLM support**: Groq (primary) → Gemini → OpenAI → Anthropic → Rule-based fallback
4. **SessionManager routing**: Manual dispatch based on state (not graph routing)
5. **State-driven workflow**: SchedulerState dict is single source of truth
6. **Service-based architecture**: Nodes delegate to business logic services (patient_service, scheduling_service, etc.)
7. **Tools layer**: 5 core tools for low-level operations (booking, reminders, patient lookup, etc.)
8. **Fallback chain**: Graceful degradation if LLM APIs unavailable

---

## Services Inventory (8 Active)

1. **llm_service.py** - Multi-provider LLM orchestration
2. **patient_service.py** - Patient lookup & database operations
3. **scheduling_service.py** - Doctor availability & slot booking
4. **form_distribution_service.py** - Form creation & email distribution
5. **email_service.py** - SMTP email sending with retry logic
6. **reminder_service.py** - Email & SMS reminder scheduling
7. **report_service.py** - Excel report generation & admin reporting
8. **excel_exporter.py** - Appointment data export to Excel

---

## Known Gaps (As of May 14, 2026)

- ⚠️ Form distribution UI integration (forms created, but UI display incomplete)
- ⚠️ Demo packaging for submission (core code ready, packaging in progress)
- ⚠️ Full SMTP configuration for email reminders (code ready, needs setup)
- ⚠️ Admin dashboard (not yet implemented)

---

**Generated**: May 14, 2026  
**Last Status Check**: 70% Complete  
**Next Submission**: Sept 6, 2026
