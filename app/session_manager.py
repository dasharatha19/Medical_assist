"""
Session Manager — Manual routing version.
Calls the correct node directly based on state, no interrupt_after needed.
"""
import uuid
from agents import create_scheduling_graph
from typing import List, Dict, Tuple, Optional
from agents.state import SchedulerState
from agents.nodes.greeting_node import greeting_node
from agents.nodes.patient_lookup_node import patient_lookup_node
from agents.nodes.scheduling_node import scheduling_node
from agents.nodes.insurance_node import insurance_node
from agents.nodes.confirmation_node import confirmation_node
from agents.nodes.reminder_node import reminder_node
from agents.nodes.form_distribution_node import form_distribution_node
from agents.nodes.scheduling_node import scheduling_node
from agents.nodes.insurance_node import insurance_node
from agents.nodes.confirmation_node import confirmation_node
from agents.nodes.reminder_node import reminder_node
import traceback
from agents.nodes.form_distribution_node import form_distribution_node
class SessionManager:

    def __init__(self):
        self.conversation_history: List[Dict[str, str]] = []
        self.agent_state = None
        self.workflow_complete: bool = False
        self.greeting_shown: bool = False
        self.thread_id = str(uuid.uuid4())
        self.config = {"configurable": {"thread_id": self.thread_id}}  # ✅ ADD THIS
        self.agent_graph = create_scheduling_graph()  
        

        # ── Routing logic ──────────────────────────────────────────────────────────
    def _get_current_node(self):
        """Decide which node to call based on state."""
        if not self.agent_state:
            return patient_lookup_node

        current_step = self.agent_state.get("current_step", "")
        collecting_step = self.agent_state.get("collecting_step", "")

        # Stay in patient_lookup until all fields collected
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

        return patient_lookup_node
    # ── Public API ─────────────────────────────────────────────────────────────

    def add_message(self, role: str, content: str) -> None:
        if content.strip():
            self.conversation_history.append({
                "role": role,
                "content": content.strip()
            })

    def get_conversation_history(self) -> List[Dict[str, str]]:
        return self.conversation_history

    def show_greeting_if_needed(self) -> None:
        if not self.greeting_shown and not self.conversation_history:
            self.add_message("assistant", (
                "Hi! 👋 I'm **MediBook**, your AI appointment assistant.\n\n"
                "I'll guide you step by step through scheduling your appointment.\n\n"
                "👋 To get started, please enter your **full name**."
            ))
            self.greeting_shown = True

    def get_state_summary(self) -> Dict:
        if not self.agent_state:
            return {"current_step": "greeting"}
        s = self.agent_state
        return {
            "patient_name":         s.get("patient_name", ""),
            "patient_id":           s.get("patient_id", ""),
            "patient_type":         s.get("patient_type", ""),
            "appointment_date":     s.get("appointment_date", ""),
            "selected_time":        s.get("selected_time", ""),
            "preferred_doctor":     s.get("preferred_doctor", ""),
            "appointment_id":       s.get("appointment_id", ""),
            "appointment_duration": s.get("appointment_duration", 0),
            "insurance_carrier":    s.get("insurance_carrier", ""),
            "booking_confirmed":    s.get("booking_confirmed", False),
            "booking_success":      s.get("booking_success", False),
            "current_step":         s.get("current_step", ""),
            "workflow_complete":    s.get("workflow_complete", False),
            "error_message":        s.get("error_message", ""),
        }

    def reset_conversation(self) -> None:
        self.conversation_history = []
        self.agent_state = None
        self.workflow_complete = False
        self.greeting_shown = False
        self.thread_id = str(uuid.uuid4())

    # ── Core execution ─────────────────────────────────────────────────────────

    def run_agent_step(self, user_input: str) -> Tuple[str, bool]:
        if self.agent_state is None:
            self.agent_state = {}

        # Don't process empty input from user
        if not user_input.strip() and self.agent_state:
            response = self.agent_state.get("response", "")
            return response, self.workflow_complete

        self.agent_state["user_input"] = user_input

        try:
            node_fn = self._get_current_node()
            result = node_fn(self.agent_state)
            self.agent_state.update(result)

            # Auto-trigger lookup without waiting for user input
            if self.agent_state.get("collecting_step") == "lookup":
                self.agent_state["user_input"] = ""
                result2 = patient_lookup_node(self.agent_state)
                self.agent_state.update(result2)

            # Auto-trigger show_doctors without waiting for user input
            if self.agent_state.get("current_step") == "scheduling" and \
            not self.agent_state.get("scheduling_step"):
                self.agent_state["user_input"] = ""
                result3 = scheduling_node(self.agent_state)
                self.agent_state.update(result3)
            
            # Auto-trigger insurance first question (only on fresh entry)
            if self.agent_state.get("current_step") == "insurance" and \
               not self.agent_state.get("insurance_step"):
                self.agent_state["user_input"] = ""
                result4 = insurance_node(self.agent_state)
                self.agent_state.update(result4)
            
            # Auto-trigger confirmation summary (only on fresh entry)
            if self.agent_state.get("current_step") == "confirmation" and \
               not self.agent_state.get("confirmation_step"):
                self.agent_state["user_input"] = ""
                result5 = confirmation_node(self.agent_state)
                self.agent_state.update(result5)
            
            # Auto-trigger reminders after confirmation
            if self.agent_state.get("current_step") == "reminders" and \
               self.agent_state.get("booking_confirmed") and \
               not self.agent_state.get("booking_success"):
                self.agent_state["user_input"] = ""
                result6 = reminder_node(self.agent_state)
                self.agent_state.update(result6)
            
            # Auto-trigger form distribution
            if self.agent_state.get("current_step") == "form_distribution" and \
               not self.agent_state.get("form_distribution_status"):
                self.agent_state["user_input"] = ""
                result7 = form_distribution_node(self.agent_state)
                self.agent_state.update(result7)

            self.workflow_complete = self.agent_state.get("workflow_complete", False)
            response = self.agent_state.get("response", "").strip()

            if not response:
                step = self.agent_state.get("collecting_step", "")
                insurance_step = self.agent_state.get("insurance_step", "")
                fallbacks = {
                    "phone": "📞 Please enter your **phone number**:",
                    "email": "📧 Please enter your **email address**:",
                    "dob":   "📅 What is your **date of birth**? (YYYY-MM-DD)",
                    "name":  "👤 Please enter your **full name**:",
                }
                insurance_fallbacks = {
                    "collect_member_id": "💳 Please enter your **Member ID**:",
                    "collect_group_id":  "🔢 Please enter your **Group ID**:",
                    "collect_other_carrier": "✏️ Please type your **insurance carrier name**:",
                }
                if step in fallbacks:
                    response = fallbacks[step]
                elif insurance_step in insurance_fallbacks:
                    response = insurance_fallbacks[insurance_step]
                else:
                    response = ""
        except Exception as e:
            error_msg = f"❌ Error: {e}\n```\n{traceback.format_exc()}\n```"
            return error_msg, False

        return response, self.workflow_complete