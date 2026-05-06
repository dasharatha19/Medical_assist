"""
Schedule Checker Tool
Simple wrapper that uses SchedulingService
Provides: get doctors, check availability
"""
import sys; sys.path.insert(0, '..')
from services import scheduling_service


class ScheduleCheckerTool:
    """Tool for checking doctor availability"""
    
    def get_doctors(self) -> list:
        """
        Get list of all available doctors
        Calls SchedulingService.get_available_doctors()
        
        Returns:
            list of doctor dicts with name, specialization, location, hours
        """
        return scheduling_service.get_available_doctors()
    
    def check_availability(self, doctor: str, date: str, duration: int) -> dict:
        """
        Check available appointment slots for a doctor
        Calls SchedulingService.check_doctor_availability()
        
        Args:
            doctor: Doctor name
            date: Appointment date (YYYY-MM-DD)
            duration: Appointment duration in minutes (30 or 60)
        
        Returns:
            dict with available slots and doctor info
        """
        return scheduling_service.check_doctor_availability(doctor, date, duration)


# Global tool instance
schedule_checker_tool = ScheduleCheckerTool()
