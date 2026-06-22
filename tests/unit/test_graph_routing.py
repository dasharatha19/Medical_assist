"""
tests/unit/test_graph_routing.py
Unit tests for LangGraph routing logic — no LLM calls.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from langgraph.graph import END

from agents.graph import route_after_booking, route_after_conversation


class TestRouteAfterConversation:
    def test_routes_to_end_when_workflow_complete(self):
        state = {"workflow_complete": True}
        result = route_after_conversation(state)
        assert result == END

    def test_routes_to_booking_when_confirmed_not_succeeded(self):
        state = {
            "workflow_complete": False,
            "booking_confirmed": True,
            "booking_success": False,
        }
        result = route_after_conversation(state)
        assert result == "booking"

    def test_routes_to_conversation_by_default(self):
        state = {}
        result = route_after_conversation(state)
        assert result == "conversation"

    def test_does_not_rebook_when_already_succeeded(self):
        state = {
            "workflow_complete": False,
            "booking_confirmed": True,
            "booking_success": True,
        }
        result = route_after_conversation(state)
        # Should NOT go to booking again
        assert result != "booking"


class TestRouteAfterBooking:
    def test_routes_to_reminders_on_success(self):
        state = {"booking_success": True}
        result = route_after_booking(state)
        assert result == "reminders"

    def test_routes_to_end_on_failure(self):
        state = {"booking_success": False}
        result = route_after_booking(state)
        assert result == END

    def test_routes_to_end_on_empty_state(self):
        state = {}
        result = route_after_booking(state)
        assert result == END


class TestSchedulerState:
    def test_state_is_typeddict(self):
        from agents.state import SchedulerState

        # Should be instantiable as a dict
        state: SchedulerState = {
            "patient_name": "Jane Doe",
            "session_id": "test-session-001",
        }
        assert state["patient_name"] == "Jane Doe"

    def test_state_allows_partial_fields(self):
        from agents.state import SchedulerState

        # total=False means no required fields
        state: SchedulerState = {}
        assert isinstance(state, dict)

    def test_graph_compiles_without_error(self):
        from agents.graph import create_scheduling_graph

        graph = create_scheduling_graph()
        assert graph is not None
