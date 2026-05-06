"""Services layer initialization"""
from .patient_service import PatientService
from .scheduling_service import SchedulingService
from .reminder_service import ReminderService
from .report_service import ReportService, create_report_service

# Create service instances
patient_service = PatientService()
scheduling_service = SchedulingService()
reminder_service = ReminderService()
report_service = create_report_service()

# Export for use in other modules
__all__ = [
    'PatientService',
    'SchedulingService',
    'ReminderService',
    'ReportService',
    'create_report_service',
    'patient_service',
    'scheduling_service',
    'reminder_service',
    'report_service'
]
