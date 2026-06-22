"""
LangGraph Scheduling Graph — properly wired with LangSmith tracing.
"""

from langgraph.graph import END, StateGraph

from agents.nodes.booking_node import booking_node
from agents.nodes.conversation_node import conversation_node
from agents.nodes.form_distribution_node import form_distribution_node
from agents.nodes.reminder_node import reminder_node
from agents.state import SchedulerState


def route_after_conversation(state: SchedulerState) -> str:
    if state.get("workflow_complete"):
        return END
    if state.get("booking_confirmed") and not state.get("booking_success"):
        return "booking"
    return "conversation"


def route_after_booking(state: SchedulerState) -> str:
    if state.get("booking_success"):
        return "reminders"
    return END


def create_scheduling_graph():
    graph = StateGraph(SchedulerState)

    graph.add_node("conversation", conversation_node)
    graph.add_node("booking", booking_node)
    graph.add_node("reminders", reminder_node)
    graph.add_node("form_distribution", form_distribution_node)

    graph.set_entry_point("conversation")

    graph.add_conditional_edges(
        "conversation",
        route_after_conversation,
        {"conversation": "conversation", "booking": "booking", END: END},
    )

    graph.add_conditional_edges(
        "booking", route_after_booking, {"reminders": "reminders", END: END}
    )

    graph.add_edge("reminders", "form_distribution")
    graph.add_edge("form_distribution", END)

    graph.set_entry_point("conversation")

    # No MemorySaver — state managed by SessionManager
    return graph.compile()
