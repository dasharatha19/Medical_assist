"""
LangGraph Scheduling Graph — with interrupt() for chat UI
"""
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt
from agents.state import SchedulerState
from agents.nodes import (
    greeting_node,
    patient_lookup_node,
    scheduling_node,
    insurance_node,
    confirmation_node,
    reminder_node,
    form_distribution_node
)


def create_scheduling_graph():
    graph = StateGraph(SchedulerState)

    graph.add_node("greeting",          greeting_node)
    graph.add_node("patient_lookup",    patient_lookup_node)
    graph.add_node("scheduling",        scheduling_node)
    graph.add_node("insurance",         insurance_node)
    graph.add_node("confirmation",      confirmation_node)
    graph.add_node("reminders",         reminder_node)
    graph.add_node("form_distribution", form_distribution_node)

    graph.add_edge("greeting",       "patient_lookup")
    graph.add_edge("patient_lookup", "scheduling")

    def should_retry_scheduling(state):
        error = state.get("error_message", "")
        retry = state.get("retry_count", 0)
        if error and "no slots" in error.lower() and retry < 3:
            return "scheduling"
        return "insurance"

    graph.add_conditional_edges(
        "scheduling",
        should_retry_scheduling,
        {"scheduling": "scheduling", "insurance": "insurance"}
    )

    graph.add_edge("insurance", "confirmation")

    def should_proceed_to_reminders(state):
        if state.get("booking_confirmed", False):
            return "reminders"
        return END

    graph.add_conditional_edges(
        "confirmation",
        should_proceed_to_reminders,
        {"reminders": "reminders", END: END}
    )

    graph.add_edge("reminders",         "form_distribution")
    graph.add_edge("form_distribution", END)

    graph.set_entry_point("greeting")

    checkpointer = MemorySaver()
    return graph.compile(
        checkpointer=checkpointer,
        interrupt_before=["patient_lookup", "scheduling", 
                        "insurance", "confirmation",
                        "reminders", "form_distribution"]
    )