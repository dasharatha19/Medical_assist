"""
Greeting Node — prints nothing to stdout.
The UI shows its own greeting. This node just initialises state.
"""
from agents.state import SchedulerState


def greeting_node(state: SchedulerState) -> SchedulerState:
    """
    Runs ONCE at workflow start. 
    Prints nothing — the SessionManager handles the greeting message.
    Immediately routes to patient_lookup which asks for the name.
    """
    state["current_step"] ="patient_lookup"
    state["error_message"] =""
    return state