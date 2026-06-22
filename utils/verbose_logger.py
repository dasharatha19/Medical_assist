"""
MediBook Verbose Logger — CrewAI-style terminal traces.
Shows every node, tool call, LLM decision, and state change in real time.
"""

import logging
from datetime import datetime


# ── Colored terminal output ───────────────────────────────────────────────────
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    ORANGE = "\033[33m"


class VerboseLogger:
    """CrewAI-style verbose logger for MediBook."""

    def __init__(self, name: str = "MediBook"):
        self.name = name
        self.logger = logging.getLogger(name)

    def _ts(self) -> str:
        return datetime.now().strftime("%H:%M:%S")

    def node_start(self, node_name: str, user_input: str = ""):
        print(f"\n{Colors.BOLD}{Colors.MAGENTA}" f"{'='*60}{Colors.RESET}")
        print(
            f"{Colors.BOLD}{Colors.MAGENTA}"
            f"🔷 NODE STARTED: {node_name.upper()}{Colors.RESET}"
            f"  [{self._ts()}]"
        )
        if user_input:
            print(f"{Colors.CYAN}   💬 User Input : {user_input}{Colors.RESET}")
        print(f"{Colors.MAGENTA}{'='*60}{Colors.RESET}")

    def node_end(self, node_name: str, response: str = ""):
        print(f"{Colors.GREEN}✅ NODE COMPLETE: {node_name}{Colors.RESET}" f"  [{self._ts()}]")
        if response:
            preview = response[:120].replace("\n", " ")
            print(f"{Colors.GREEN}   🤖 Response   : {preview}...{Colors.RESET}")
        print(f"{Colors.MAGENTA}{'-'*60}{Colors.RESET}\n")

    def tool_call(self, tool_name: str, params: dict = None):
        print(f"{Colors.YELLOW}🔧 TOOL CALLED  : {tool_name}{Colors.RESET}" f"  [{self._ts()}]")
        if params:
            for k, v in params.items():
                print(f"{Colors.YELLOW}   ├─ {k}: {v}{Colors.RESET}")

    def tool_result(self, tool_name: str, result, success: bool = True):
        icon = "✅" if success else "❌"
        color = Colors.GREEN if success else Colors.RED
        print(f"{color}{icon} TOOL RESULT    : {tool_name}{Colors.RESET}" f"  [{self._ts()}]")
        if isinstance(result, list):
            for item in result[:5]:
                name = item.get("name", str(item)) if isinstance(item, dict) else str(item)
                print(f"{color}   ├─ {name}{Colors.RESET}")
        elif isinstance(result, dict):
            for k, v in list(result.items())[:5]:
                print(f"{color}   ├─ {k}: {v}{Colors.RESET}")
        else:
            print(f"{color}   └─ {str(result)[:100]}{Colors.RESET}")

    def llm_call(self, provider: str, model: str, phase: str):
        print(
            f"{Colors.BLUE}🧠 LLM CALL     : {provider} / {model}{Colors.RESET}" f"  [{self._ts()}]"
        )
        print(f"{Colors.BLUE}   ├─ Phase      : {phase}{Colors.RESET}")

    def llm_result(self, intent: str, extracted: dict, phase: str):
        print(
            f"{Colors.BLUE}🧠 LLM DECISION : intent={intent} | phase={phase}{Colors.RESET}"
            f"  [{self._ts()}]"
        )
        filled = {k: v for k, v in extracted.items() if v is not None}
        if filled:
            print(f"{Colors.BLUE}   └─ Extracted  : {filled}{Colors.RESET}")

    def state_update(self, field: str, value: str, action: str = "SET"):
        color = Colors.GREEN if action == "SET" else Colors.ORANGE
        print(f"{color}📝 STATE {action:<6} : {field} = {value}{Colors.RESET}" f"  [{self._ts()}]")

    def state_summary(self, state: dict):
        print(f"{Colors.CYAN}📊 STATE SUMMARY:{Colors.RESET}  [{self._ts()}]")
        fields = [
            ("patient_name", "👤 Name"),
            ("patient_dob", "🗓️  DOB"),
            ("patient_phone", "📞 Phone"),
            ("patient_email", "📧 Email"),
            ("preferred_doctor", "🩺 Doctor"),
            ("appointment_date", "📅 Date"),
            ("selected_time", "⏰ Time"),
            ("insurance_carrier", "🏥 Insurance"),
        ]
        for key, label in fields:
            val = state.get(key)
            color = Colors.GREEN if val else Colors.RED
            tick = "✅" if val else "❌"
            print(
                f"   {tick} {Colors.CYAN}{label:<14}{Colors.RESET}"
                f"{color}{val or 'missing'}{Colors.RESET}"
            )

    def missing_fields(self, missing: list):
        if missing:
            print(
                f"{Colors.ORANGE}⚠️  MISSING FIELDS: "
                f"{', '.join(missing)}{Colors.RESET}  [{self._ts()}]"
            )
        else:
            print(
                f"{Colors.GREEN}✅ ALL FIELDS COLLECTED — ready to confirm!"
                f"{Colors.RESET}  [{self._ts()}]"
            )

    def booking_event(self, event: str, details: dict = None):
        print(
            f"{Colors.GREEN}{Colors.BOLD}🎉 BOOKING EVENT: {event}{Colors.RESET}"
            f"  [{self._ts()}]"
        )
        if details:
            for k, v in details.items():
                print(f"{Colors.GREEN}   ├─ {k}: {v}{Colors.RESET}")

    def error(self, where: str, msg: str):
        print(f"{Colors.RED}❌ ERROR in {where}: {msg}{Colors.RESET}" f"  [{self._ts()}]")

    def warning(self, msg: str):
        print(f"{Colors.ORANGE}⚠️  WARNING: {msg}{Colors.RESET}" f"  [{self._ts()}]")

    def doctor_change(self, old: str, new: str):
        print(
            f"{Colors.ORANGE}🔄 DOCTOR CHANGE: {old or 'None'} → {new}{Colors.RESET}"
            f"  [{self._ts()}]"
        )

    def phase_change(self, old: str, new: str):
        print(f"{Colors.MAGENTA}🔀 PHASE CHANGE : {old} → {new}{Colors.RESET}" f"  [{self._ts()}]")


# ── Singleton ─────────────────────────────────────────────────────────────────
verbose = VerboseLogger("MediBook")
