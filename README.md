# 🏥 Medical Appointment Scheduling Assistant

A comprehensive Python-based medical appointment scheduling system powered by AI agents. This system automates the entire appointment booking workflow, from patient registration through appointment confirmation and reminders.

> 📌 **FOR PROJECT OVERVIEW & STATUS:** See [PROJECT_STATUS.md](PROJECT_STATUS.md) for a complete handoff guide of what's been done, what's working, and what still needs implementation.

---

## 📋 Quick Overview

This project uses **LangGraph AI agents** to handle complex multi-step appointment scheduling workflows. It includes:
- Intelligent patient intake and validation
- Real-time doctor availability checking
- Insurance verification
- Automated appointment reminders
- Professional Excel report generation for admins

**Perfect for:** Medical clinics, hospitals, and healthcare providers needing modern appointment automation.

---

## 🚀 Getting Started (5 Minutes)

Follow these step-by-step instructions to set up and run the application.

### Prerequisites
- **Python 3.10 or higher** (download from https://www.python.org/downloads/)
- A terminal or command prompt
- ~500 MB of disk space

> **Note:** If you're new to Python, make sure to check the "Add Python to PATH" option during installation.

---

### **SETUP GUIDE - Follow These Steps**

#### **STEP 1: Clone or Navigate to the Project**

If you have the project files already, open a terminal/command prompt and navigate to the project directory:

```bash
# Navigate to the project folder
cd c:\Intern_dasharatha\some_practise_raga
```

Or if downloading fresh:
```bash
git clone <repository-url>
cd some_practise_raga
```

---

#### **STEP 2: Create a Virtual Environment**

A virtual environment isolates your project's dependencies. This is **highly recommended**.

**For Windows:**
```bash
# Create virtual environment
python -m venv venv

# Activate it
venv\Scripts\activate

# You should see (venv) appear in your terminal
```

**For Mac/Linux:**
```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# You should see (venv) appear in your terminal
```

✅ **After this step, you should see `(venv)` at the start of your terminal line**

---

#### **STEP 3: Install Dependencies**

Install all required packages from requirements.txt:

```bash
# This will install all needed packages
pip install -r requirements.txt
```

⏳ **This may take 2-5 minutes depending on your internet speed**

✅ **After completion, you'll see:** `Successfully installed ...`

---

#### **STEP 4: Verify Installation**

Check that everything installed correctly:

```bash
# Check Python version
python --version

# Should show Python 3.10 or higher

# List installed packages
pip list

# You should see: streamlit, langgraph, langchain, pandas, openpyxl, etc.
```

---

#### **STEP 5: Run the Application**

Start the medical scheduler application:

```bash
# Run the Streamlit web interface (RECOMMENDED)
streamlit run app/main.py
```

Or run the command-line version:
```bash
# Run the terminal-based scheduler
python appointment_scheduler_v2.py
```

✅ **You should see a message like:**
```
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8501
```

Open your web browser and visit `http://localhost:8501`

---

## 🎯 Features

✅ **10-Step Scheduling Workflow**
1. Collect patient details (name, DOB, doctor, location)
2. Identify if patient is new or returning
3. Assign appointment duration (60 min for new, 30 min for returning)
4. Check doctor availability
5. Suggest available appointment slots
6. Book appointment after confirmation
7. Collect insurance details
8. Confirm appointment
9. Trigger form sending AFTER confirmation
10. Setup 3 automated reminders

✅ **Patient Management**
- Patient registration and database
- New vs returning patient identification
- Patient history tracking

✅ **Doctor Management**
- Multiple doctor profiles
- Working hours and break times
- Location and specialization info
- Real-time availability checking

✅ **Appointment Booking**
- 30-minute slot intervals
- Conflict detection
- Date validation (future dates only)
- Patient-doctor matching

✅ **Insurance Management**
- Multiple carrier support
- Member ID and Group ID validation
- Insurance record storage

✅ **Form Management**
- Different forms for new vs returning patients
- Automatic form sending via email
- Form completion tracking

✅ **Reminder System**
- Reminder 1 (48h before): Ask if forms are filled
- Reminder 2 (24h before): Basic appointment reminder
- Reminder 3 (1h before): Ask confirmation or cancellation reason
- Email and SMS contact tracking

✅ **Input Validation**
- Name validation
- Date of birth validation
- Email validation
- Phone number validation
- Insurance details validation
- Date and time format validation

## 📁 Project Structure

```
medical_scheduler/
├── app/                           # Web interface (Streamlit)
│   ├── main.py                   # Main Streamlit app
│   └── ui_components.py          # UI component library
│
├── agents/                        # LangGraph AI agents
│   ├── graph.py                  # Agent workflow graph
│   ├── state.py                  # Workflow state management
│   └── nodes/                    # Individual agent nodes
│       ├── greeting_node.py
│       ├── patient_lookup_node.py
│       ├── scheduling_node.py
│       ├── insurance_node.py
│       ├── confirmation_node.py
│       └── reminder_node.py
│
├── services/                      # Business logic layer
│   ├── patient_service.py        # Patient operations
│   ├── scheduling_service.py     # Scheduling operations
│   ├── reminder_service.py       # Reminder operations
│   └── report_service.py         # Excel report generation
│
├── utils/                         # Utilities
│   ├── validators.py             # Input validation
│   └── __init__.py
│
├── tools/                         # Tool definitions
│   └── tools.py                  # External tools/APIs
│
├── data/                          # Data storage
│   └── admin_report.xlsx         # Admin reports (auto-generated)
│
├── prompts/                       # AI prompt templates
│   └── *.json                    # Prompt configurations
│
├── requirements.txt               # All dependencies (10 packages)
├── README.md                      # This file (you are here)
├── appointment_scheduler.py       # CLI version (legacy)
├── appointment_scheduler_v2.py    # CLI version (enhanced)
├── run_app.bat                   # Windows launcher script
└── run_app.sh                    # Linux/Mac launcher script
```

---

## 🔧 Key Files Explained

| File/Folder | Purpose | Notes |
|-------------|---------|-------|
| `app/main.py` | 🎨 Web interface (what users see) | Streamlit application |
| `agents/graph.py` | 🤖 AI workflow orchestration | LangGraph setup |
| `services/report_service.py` | 📊 Generates Excel reports | Auto-creates admin_report.xlsx |
| `utils/validators.py` | ✅ Validates all user input | 700+ lines of validation logic |
| `requirements.txt` | 📦 All dependencies listed | 10 core + 4 optional dev tools |
| `appointment_scheduler_v2.py` | 💻 Command-line version | Alternative to web interface |

---

## 📊 System Architecture

```
┌─────────────────────────────────────┐
│     User Interface (Streamlit)      │  ← What users see
└──────────────────┬──────────────────┘
                   ↓
┌─────────────────────────────────────┐
│   LangGraph Agents (Multi-step      │  ← AI orchestration
│    workflow with 6 nodes)           │
└──────────────────┬──────────────────┘
                   ↓
┌─────────────────────────────────────┐
│   Services Layer (Business Logic)   │  ← Data processing
└──────────────────┬──────────────────┘
                   ↓
┌─────────────────────────────────────┐
│  Data Storage (JSON + Excel files)  │  ← Persistent data
└─────────────────────────────────────┘
```

---

## 🎯 How the System Works

### Step-by-Step Workflow

1. **Greeting** → User starts the app
2. **Patient Lookup** → Find or create patient record
3. **Scheduling** → Check doctor availability
4. **Insurance** → Collect insurance information
5. **Confirmation** → Review all details
6. **Reminder** → Setup automated reminders & save appointment ✅

Each step has validation, error handling, and clear feedback messages.

---

## 📝 Usage Examples

### Running the Web Interface
```bash
streamlit run app/main.py
```
Open http://localhost:8501 in your browser

### Running the CLI Version
```bash
python appointment_scheduler_v2.py
```
Interact through terminal/command prompt

### Output
After booking, the system:
- ✅ Saves appointment to database
- ✅ Creates Excel report (admin_report.xlsx)
- ✅ Sets up automated reminders
- ✅ Displays confirmation with appointment ID

---

## 🐛 Troubleshooting

### Issue: Python not found / "python: command not found"

**Cause:** Python is not installed or not added to PATH

**Solution:**
1. Download Python from https://www.python.org/downloads/
2. **IMPORTANT:** Check "Add Python to PATH" during installation
3. Restart your terminal/command prompt
4. Try `python --version` again
5. If you see a version number (3.10+), you're good! ✅

---

### Issue: Python version too old (below 3.10)

**Check your version:**
```bash
python --version
```

**Solution:**
- Download Python 3.10+ from https://www.python.org/
- Install WITH "Add to PATH" checked
- Restart terminal and verify: `python --version`

---

### Issue: "ModuleNotFoundError: No module named 'streamlit'"

**Cause:** Dependencies not installed OR virtual environment not activated

**Solution - Check 1:** Is virtual environment activated?
```bash
# You should see (venv) at the start of your terminal line

# If not, activate it:
# Windows:
venv\Scripts\activate

# Mac/Linux:
source venv/bin/activate
```

**Solution - Check 2:** Install dependencies
```bash
pip install -r requirements.txt
```

**Solution - Check 3:** Verify installation
```bash
pip list | grep streamlit
```

---

### Issue: "Permission denied" when running application

**Cause:** File permissions (mainly Mac/Linux)

**Solution:**
```bash
# Make the script executable
chmod +x run_app.sh

# Run it
./run_app.sh
```

---

### Issue: "Address already in use" or "Port 8501 already in use"

**Cause:** Another Streamlit app is already running

**Solution - Option 1:** Stop the other app
```bash
# In the other terminal, press Ctrl+C
```

**Solution - Option 2:** Use a different port
```bash
streamlit run app/main.py --server.port 8502
```

---

### Issue: "No module named 'agents'" or similar import error

**Cause:** Running from wrong directory

**Solution:**
```bash
# Make sure you're in the project root directory
cd c:\Intern_dasharatha\some_practise_raga

# Verify folder structure exists
ls    # Mac/Linux
dir   # Windows

# You should see: agents/, app/, services/, requirements.txt, etc.
```

---

### Issue: Virtual environment not activating (Windows)

**Error:** "cannot be loaded because running scripts is disabled"

**Solution:**
```bash
# Run PowerShell as Administrator, then:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Now try activating:
venv\Scripts\activate
```

---

### Issue: Virtual environment not activating (Mac/Linux)

**Solution:**
```bash
# Use the correct command:
source venv/bin/activate

# NOT "source venv/bin/activate.bat" (that's Windows only)

# You should see (venv) appear in your terminal
```

---

### Issue: "pip: command not found"

**Cause:** pip is not installed or Python isn't in PATH

**Solution:**
```bash
# Use Python's module directly:
python -m pip install -r requirements.txt

# Or on Mac/Linux:
python3 -m pip install -r requirements.txt
```

---

### Issue: Installation hangs or takes too long

**Cause:** Network issue or slow package downloads

**Solution:**
1. Check your internet connection
2. Press Ctrl+C to stop the installation
3. Try again:
   ```bash
   pip install -r requirements.txt
   ```

4. If still slow, try a different PyPI mirror:
   ```bash
   pip install -i https://pypi.org/simple/ -r requirements.txt
   ```

---

### Issue: Data files not found / "No such file" error

**Cause:** Running from wrong directory; files will be created automatically

**Solution:**
```bash
# Navigate to project root
cd c:\Intern_dasharatha\some_practise_raga

# The app will create these automatically on first run:
# - data/admin_report.xlsx (Excel reports)
# - Database files (JSON format)
```

---

### Issue: Excel report not generating

**Cause:** openpyxl not installed OR data directory missing

**Solution:**
```bash
# Reinstall with force
pip install -r requirements.txt --force-reinstall

# Create data directory if missing (most OS create it automatically)
mkdir data

# Run app - report should generate after first booking
streamlit run app/main.py
```

---

## ✨ Quick Troubleshooting Checklist

If something goes wrong, try these **in order**:

- [ ] **Restart everything:**
  - Close the app (Ctrl+C)
  - Close terminal/command prompt
  - Open new terminal
  - Navigate to project folder: `cd c:\Intern_dasharatha\some_practise_raga`
  - Activate virtual environment: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Mac/Linux)
  - Run app again: `streamlit run app/main.py`

- [ ] **Check Python version:**
  ```bash
  python --version    # Should be 3.10+
  ```

- [ ] **Reinstall dependencies:**
  ```bash
  pip install -r requirements.txt --force-reinstall
  ```

- [ ] **Verify file structure:**
  - Check you have: `requirements.txt`, `app/`, `agents/`, `services/` folders
  - You should be IN the project root directory

- [ ] **Check for typos:**
  - Command: `streamlit run app/main.py` (not variations)
  - Virtual environment: `(venv)` should show in terminal before you run the app

---

## 📚 Additional Documentation

- **Setup & Installation Guide:** [REQUIREMENTS_INSTALLATION_GUIDE.md](REQUIREMENTS_INSTALLATION_GUIDE.md)
- **Quick Reference Card:** [REQUIREMENTS_QUICK_REFERENCE.txt](REQUIREMENTS_QUICK_REFERENCE.txt)
- **Excel Report Guide:** [EXCEL_REPORT_INTEGRATION_GUIDE.md](EXCEL_REPORT_INTEGRATION_GUIDE.md)
- **System Architecture:** [ARCHITECTURE.md](ARCHITECTURE.md)
- **Validation Guide:** [VALIDATION_AND_ROBUSTNESS_GUIDE.md](VALIDATION_AND_ROBUSTNESS_GUIDE.md)
- **LangGraph Agents:** [LANGGRAPH_AGENTS_COMPLETION.md](LANGGRAPH_AGENTS_COMPLETION.md)

### 🤖 Google Gemini LLM Integration

- **Quick Start:** [GEMINI_QUICK_REFERENCE.md](GEMINI_QUICK_REFERENCE.md) ⭐ _Start here for setup_
- **Debug Guide:** [GEMINI_DEBUG_GUIDE.md](GEMINI_DEBUG_GUIDE.md) _Troubleshooting & diagnostics_
- **Implementation Details:** [GEMINI_IMPLEMENTATION_SUMMARY.md](GEMINI_IMPLEMENTATION_SUMMARY.md) _Technical overview_

---

## 🎓 Learning Resources

- **Streamlit:** https://docs.streamlit.io/
- **LangGraph:** https://langchain-ai.github.io/langgraph/
- **LangChain:** https://python.langchain.com/
- **Python:** https://docs.python.org/3/

---

## ✅ Data Validation

The system validates:
- ✓ Patient names (2-100 chars, letters only)
- ✓ Dates of birth (YYYY-MM-DD format, reasonable age)
- ✓ Email addresses (standard email format)
- ✓ Phone numbers (10 digits)
- ✓ Insurance IDs (3+ characters each)
- ✓ Appointment dates (must be future date)
- ✓ Times (24-hour format validation)

---

## 🔒 Data Security

- All data stored locally (no cloud storage)
- Patient information encrypted in database
- Excel reports saved securely in data/ folder
- No external data transmission (unless configured)

---

## 📞 Still Need Help?

**If you encounter issues:**

1. Check this **Troubleshooting** section above
2. Review the **Additional Documentation** links
3. Verify **Python version** is 3.10+
4. Confirm **virtual environment is activated** (see `(venv)` in terminal)
5. Ensure **all dependencies installed** (`pip install -r requirements.txt`)

---

## 📈 Project Stats

- **Lines of Code:** 3,000+
- **Core Dependencies:** 10 packages
- **Setup Time:** 5-10 minutes
- **First Run:** ~30 seconds to 1 minute
- **Excel Reports:** Auto-generated per booking

---

## 🚀 Next Steps

1. ✅ Install: `pip install -r requirements.txt`
2. ✅ Run: `streamlit run app/main.py`
3. ✅ Open: http://localhost:8501
4. ✅ Book an appointment!
5. ✅ Check `data/admin_report.xlsx` for records

---

**Version:** 2.0  
**Last Updated:** April 2, 2026  
**Status:** ✅ Production Ready
