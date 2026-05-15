"""
LangGraph Scheduling Graph — properly wired with LangSmith tracing.
"""
import os
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from agents.state import SchedulerState
from agents.nodes.conversation_node import conversation_node
from agents.nodes.booking_node import booking_node
from agents.nodes.reminder_node import reminder_node
from agents.nodes.form_distribution_node import form_distribution_node

# ── LangSmith auto-connects via env vars ──────────────────────────────────────
# Set these in your .env:
# LANGCHAIN_TRACING_V2=true
# LANGCHAIN_API_KEY=your_key
# LANGCHAIN_PROJECT=medibook-agent
# No extra code needed — LangGraph traces automatically when env vars are set


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

    graph.add_node("conversation",      conversation_node)
    graph.add_node("booking",           booking_node)
    graph.add_node("reminders",         reminder_node)
    graph.add_node("form_distribution", form_distribution_node)

    graph.set_entry_point("conversation")

    graph.add_conditional_edges(
        "conversation",
        route_after_conversation,
        {
            "conversation": "conversation",
            "booking":      "booking",
            END:            END
        }
    )

    graph.add_conditional_edges(
        "booking",
        route_after_booking,
        {
            "reminders": "reminders",
            END:         END
        }
    )

    graph.add_edge("reminders",         "form_distribution")
    graph.add_edge("form_distribution", END)

    graph.set_entry_point("conversation")

    # No MemorySaver — state managed by SessionManager
    return graph.compile()