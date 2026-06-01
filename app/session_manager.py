"""
Session Manager — Intelligent 4-node version, LangGraph-powered.
"""
import uuid
import traceback
from typing import List, Dict, Tuple, Optional
from agents.nodes.booking_node import booking_node
from agents.nodes.reminder_node import reminder_node
from agents.nodes.form_distribution_node import form_distribution_node
from database.db import initialize_database


class SessionManager:

    def __init__(self):
        initialize_database()
        self.conversation_history: List[Dict[str, str]] = []
        self.agent_state = None
        self.workflow_complete: bool = False
        self.greeting_shown: bool = False
        self.thread_id = str(uuid.uuid4())
        self._graph = None  # LangGraph instance

    def _get_graph(self):
        """Lazy-load graph once."""
        if self._graph is None:
            from agents.graph import create_scheduling_graph
            self._graph = create_scheduling_graph()
        return self._graph

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
                "Hi! 👋 I'm **MediBook**, your AI appointment scheduling assistant.\n\n"
                "I can help you book an appointment, answer questions about our "
                "doctors, or check availability.\n\n"
                "📌 **Please note:** Any information you share during this "
                "conversation is saved securely, even if you cancel mid-booking. "
                "This helps us serve you better next time.\n\n"
                "How can I help you today?"
            ))
            self.greeting_shown = True

    def get_state_summary(self) -> Dict:
        if not self.agent_state:
            return {"current_step": "greeting"}
        s = self.agent_state
        current_step = s.get("current_step", "")
        if not current_step:
            if not s.get("patient_name"):
                current_step = "greeting"
            elif not s.get("preferred_doctor"):
                current_step = "patient_lookup"
            elif not s.get("selected_time"):
                current_step = "scheduling"
            elif not s.get("insurance_carrier"):
                current_step = "insurance"
            elif not s.get("booking_confirmed"):
                current_step = "confirmation"
            else:
                current_step = "reminders"
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
            "current_step":         current_step,
            "workflow_complete":    s.get("workflow_complete", False),
            "error_message":        s.get("error_message", ""),
        }

    def reset_conversation(self) -> None:
        self.conversation_history = []
        self.agent_state = None
        self.workflow_complete = False
        self.greeting_shown = False
        self.thread_id = str(uuid.uuid4())
        self._graph = None  # reset graph too

    def run_agent_step(self, user_input: str) -> Tuple[str, bool]:
        if self.agent_state is None:
            self.agent_state = {}

        if not user_input.strip() and self.agent_state:
            return self.agent_state.get("response", ""), self.workflow_complete

        self.agent_state["user_input"] = user_input
        self.agent_state["session_id"] = self.thread_id  # inject session isolation key

        try:
            # ── Determine which node to run based on state ────────────────────
            from agents.nodes.conversation_node import conversation_node
            from agents.nodes.booking_node import booking_node
            from agents.nodes.reminder_node import reminder_node
            from agents.nodes.form_distribution_node import form_distribution_node

            # Route to correct node
            if (self.agent_state.get("booking_confirmed") and
                    not self.agent_state.get("booking_success")):
                node_fn = booking_node
            elif (self.agent_state.get("current_step") == "reminders" and
                not self.agent_state.get("reminders_setup")):
                node_fn = reminder_node
            elif (self.agent_state.get("current_step") == "form_distribution" and
                not self.agent_state.get("form_distribution_status")):
                node_fn = form_distribution_node
            else:
                node_fn = conversation_node

            # ── Run the node ──────────────────────────────────────────────────
            result = node_fn(self.agent_state)
            self.agent_state.update(result)

            # ── Auto-chain booking → reminders → forms ────────────────────────
            if (self.agent_state.get("booking_confirmed") and
                    not self.agent_state.get("booking_success")):
                result2 = booking_node(self.agent_state)
                self.agent_state.update(result2)

            if (self.agent_state.get("current_step") == "reminders" and
                    self.agent_state.get("booking_success") and
                    not self.agent_state.get("reminders_setup")):
                self.agent_state["user_input"] = ""
                result3 = reminder_node(self.agent_state)
                self.agent_state.update(result3)

            if (self.agent_state.get("current_step") == "form_distribution" and
                    not self.agent_state.get("form_distribution_status")):
                self.agent_state["user_input"] = ""
                result4 = form_distribution_node(self.agent_state)
                self.agent_state.update(result4)

            self.workflow_complete = self.agent_state.get("workflow_complete", False)
            response = self.agent_state.get("response", "").strip()

            if not response:
                response = "I'm here to help! How can I assist you?"

        except Exception as e:
            error_msg = (
                f"❌ Error: {e}\n"
                f"```\n{traceback.format_exc()}\n```"
            )
            return error_msg, False

        return response, self.workflow_complete