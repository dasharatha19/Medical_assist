"""Tools layer initialization and registry"""
from .patient_lookup_tool import patient_lookup_tool
from .schedule_checker_tool import schedule_checker_tool
from .booking_tool import booking_tool
from .notification_tool import notification_tool
from .reminder_tool import reminder_tool


class ToolRegistry:
    """Registry for all available tools
    
    Provides convenient access to all scheduling tools
    Each tool is a simple wrapper around a service
    """
    patient_lookup = patient_lookup_tool
    schedule_checker = schedule_checker_tool
    booking = booking_tool
    notification = notification_tool
    reminder = reminder_tool


# Global tool registry instance
tools = ToolRegistry()
