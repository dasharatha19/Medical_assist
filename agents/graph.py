"""LangGraph Scheduling Graph — Intelligent 4-node version."""
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from agents.state import SchedulerState
from agents.nodes import (
    conversation_node,
    booking_node,
    reminder_node,
    form_distribution_node
)


def create_scheduling_graph():
    graph = StateGraph(SchedulerState)

    graph.add_node("conversation",       conversation_node)
    graph.add_node("booking",            booking_node)
    graph.add_node("reminders",          reminder_node)
    graph.add_node("form_distribution",  form_distribution_node)

    def route_after_conversation(state):
        if state.get("booking_confirmed") and not state.get("booking_success"):
            return "booking"
        if state.get("workflow_complete"):
            return END
        return "conversation"  # stay in conversation

    graph.add_conditional_edges(
        "conversation",
        route_after_conversation,
        {
            "conversation": "conversation",
            "booking": "booking",
            END: END
        }
    )

    graph.add_edge("booking",           "reminders")
    graph.add_edge("reminders",         "form_distribution")
    graph.add_edge("form_distribution", END)

    graph.set_entry_point("conversation")

    checkpointer = MemorySaver()
    return graph.compile(checkpointer=checkpointer)