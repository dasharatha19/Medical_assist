"""
Report Service Layer
Handles generation and management of Excel reports for admin review
Encapsulates all reporting business logic and Excel operations

Features:
- Append-only Excel workbooks (no overwriting)
- Structured appointment data with formatting
- Safe handling of missing data
- Timestamp tracking for all records
- Professional report formatting
"""

import os
from datetime import datetime
from typing import Dict, Optional, List
from pathlib import Path

try:
    from openpyxl import Workbook, load_workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False


class ReportException(Exception):
    """Custom exception for report operations"""
    pass


class ExcelReportGenerator:
    """
    Generates and maintains Excel reports for appointment bookings
    
    Report Structure:
    - Row 1: Column headers
    - Rows 2+: Appointment records with formatting
    
    Columns:
    1. Record ID (auto-incremented)
    2. Booking Date
    3. Patient Name
    4. Date of Birth
    5. Patient Type
    6. Doctor Name
    7. Appointment Date
    8. Appointment Time
    9. Duration (minutes)
    10. Insurance Carrier
    11. Member ID
    12. Group ID
    13. Status
    14. Appointment ID
    15. Notes
    """
    
    # Column definitions for the report
    COLUMNS = [
        'Record ID',
        'Booking Date',
        'Patient Name',
        'Date of Birth',
        'Patient Type',
        'Doctor Name',
        'Appointment Date',
        'Appointment Time',
        'Duration (min)',
        'Insurance Carrier',
        'Member ID',
        'Group ID',
        'Status',
        'Appointment ID',
        'Notes'
    ]
    
    # Default report location
    DEFAULT_REPORT_PATH = 'data/admin_report.xlsx'
    
    def __init__(self, report_path: str = None):
        """
        Initialize the Excel report generator
        
        Args:
            report_path: Path to Excel file. Uses DEFAULT_REPORT_PATH if not provided
        
        Raises:
            ReportException: If openpyxl is not installed
        """
        if not OPENPYXL_AVAILABLE:
            raise ReportException(
                "openpyxl is required for Excel report generation. "
                "Install it with: pip install openpyxl"
            )
        
        self.report_path = report_path or self.DEFAULT_REPORT_PATH
        self._ensure_data_directory()
    
    def _ensure_data_directory(self) -> None:
        """Create data directory if it doesn't exist"""
        data_dir = os.path.dirname(self.report_path)
        if data_dir and not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)
    
    def _load_or_create_workbook(self) -> Workbook:
        """
        Load existing workbook or create new one
        
        Returns:
            Workbook: Loaded or newly created workbook
        """
        if os.path.exists(self.report_path):
            # Load existing workbook
            wb = load_workbook(self.report_path)
            ws = wb.active
            return wb
        else:
            # Create new workbook with headers
            wb = Workbook()
            ws = wb.active
            ws.title = "Appointments"
            self._add_headers(ws)
            return wb
    
    def _add_headers(self, worksheet) -> None:
        """
        Add header row with formatting to worksheet
        
        Args:
            worksheet: Active worksheet to add headers to
        """
        # Add column headers
        for col_idx, column_name in enumerate(self.COLUMNS, start=1):
            cell = worksheet.cell(row=1, column=col_idx)
            cell.value = column_name
            
            # Format header cells
            cell.font = Font(
                bold=True,
                color="FFFFFF"  # White text
            )
            cell.fill = PatternFill(
                start_color="366092",  # Dark blue
                end_color="366092",
                fill_type="solid"
            )
            cell.alignment = Alignment(
                horizontal="center",
                vertical="center",
                wrap_text=True
            )
    
    def _get_next_record_id(self, worksheet) -> int:
        """
        Get the next record ID for a new appointment
        
        Args:
            worksheet: Active worksheet
        
        Returns:
            int: Next sequential record ID
        """
        max_row = worksheet.max_row
        
        # Skip header row
        if max_row < 2:
            return 1
        
        try:
            # Get last record ID
            last_id = worksheet.cell(row=max_row, column=1).value
            if isinstance(last_id, int):
                return last_id + 1
        except:
            pass
        
        return max_row - 1  # max_row - 1 (excluding header)
    
    def _format_data_row(self, worksheet, row_idx: int) -> None:
        """
        Apply formatting to a data row
        
        Args:
            worksheet: Active worksheet
            row_idx: Row index to format
        """
        for col_idx in range(1, len(self.COLUMNS) + 1):
            cell = worksheet.cell(row=row_idx, column=col_idx)
            
            # Alternate row colors for readability
            if row_idx % 2 == 0:
                cell.fill = PatternFill(
                    start_color="E8E8E8",
                    end_color="E8E8E8",
                    fill_type="solid"
                )
            
            # Add borders
            thin_border = Border(
                left=Side(style='thin'),
                right=Side(style='thin'),
                top=Side(style='thin'),
                bottom=Side(style='thin')
            )
            cell.border = thin_border
            
            # Center align most columns (except names)
            if col_idx not in [1, 3, 6, 10, 11, 15]:  # Name/text columns
                cell.alignment = Alignment(horizontal="center")
            else:
                cell.alignment = Alignment(horizontal="left")
    
    def _format_date_cell(self, cell, value) -> None:
        """
        Format date cells with consistent date display
        
        Args:
            cell: Cell to format
            value: Date value to set
        """
        cell.value = value
        cell.number_format = 'YYYY-MM-DD'
        cell.alignment = Alignment(horizontal="center")
    
    def _format_time_cell(self, cell, value) -> None:
        """
        Format time cells with consistent time display
        
        Args:
            cell: Cell to format
            value: Time value to set
        """
        cell.value = value
        cell.alignment = Alignment(horizontal="center")
    
    def add_appointment_record(self, appointment_data: Dict) -> bool:
        """
        Add a new appointment record to the report
        
        Args:
            appointment_data: Dictionary with keys:
                - patient_name (str): Full name
                - patient_dob (str): Date of birth (YYYY-MM-DD)
                - patient_type (str): 'new' or 'returning'
                - preferred_doctor (str): Doctor name
                - appointment_date (str): Appointment date (YYYY-MM-DD)
                - selected_time (str): Appointment time (HH:MM)
                - appointment_duration (int): Duration in minutes
                - insurance_carrier (str): Insurance company name
                - insurance_member_id (str): Member ID
                - insurance_group_id (str): Group ID
                - booking_confirmed (bool): Booking status
                - appointment_id (str): Appointment ID
                - notes (str, optional): Additional notes
        
        Returns:
            bool: True if record added successfully, False otherwise
        
        Raises:
            ReportException: If record data is invalid or write fails
        """
        if not appointment_data:
            raise ReportException("Empty appointment data provided")
        
        try:
            # Load or create workbook
            wb = self._load_or_create_workbook()
            ws = wb.active
            
            # Get next record ID and row
            record_id = self._get_next_record_id(ws)
            next_row = ws.max_row + 1
            
            # Prepare values with safe defaults for missing data
            values = [
                record_id,
                self._get_safe_value(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ""),
                self._get_safe_value(appointment_data.get('patient_name'), "N/A"),
                self._get_safe_value(appointment_data.get('patient_dob'), "N/A"),
                self._get_safe_value(appointment_data.get('patient_type'), "N/A"),
                self._get_safe_value(appointment_data.get('preferred_doctor'), "N/A"),
                self._get_safe_value(appointment_data.get('appointment_date'), "N/A"),
                self._get_safe_value(appointment_data.get('selected_time'), "N/A"),
                self._get_safe_value(appointment_data.get('appointment_duration'), 0),
                self._get_safe_value(appointment_data.get('insurance_carrier'), "None"),
                self._get_safe_value(appointment_data.get('insurance_member_id'), ""),
                self._get_safe_value(appointment_data.get('insurance_group_id'), ""),
                self._get_status(appointment_data.get('booking_confirmed')),
                self._get_safe_value(appointment_data.get('appointment_id'), "N/A"),
                self._get_safe_value(appointment_data.get('notes'), "")
            ]
            
            # Add values to cells
            for col_idx, value in enumerate(values, start=1):
                cell = ws.cell(row=next_row, column=col_idx)
                cell.value = value
            
            # Apply formatting to the row
            self._format_data_row(ws, next_row)
            
            # Adjust column widths for readability
            self._adjust_column_widths(ws)
            
            # Save workbook
            wb.save(self.report_path)
            
            return True
        
        except Exception as e:
            raise ReportException(f"Failed to add appointment record: {str(e)}")
    
    def _get_safe_value(self, value, default=""):
        """
        Safely get value with fallback to default
        
        Args:
            value: Value to check
            default: Default value if None or empty
        
        Returns:
            Safe value or default
        """
        if value is None or value == "":
            return default
        return value
    
    def _get_status(self, booking_confirmed: bool) -> str:
        """
        Convert booking_confirmed boolean to readable status
        
        Args:
            booking_confirmed: Whether booking is confirmed
        
        Returns:
            str: 'Confirmed' or 'Cancelled'
        """
        return "Confirmed" if booking_confirmed else "Cancelled"
    
    def _adjust_column_widths(self, worksheet) -> None:
        """
        Adjust column widths based on content
        
        Args:
            worksheet: Active worksheet
        """
        # Define optimal widths for each column
        column_widths = {
            1: 10,   # Record ID
            2: 20,   # Booking Date
            3: 20,   # Patient Name
            4: 14,   # DOB
            5: 14,   # Patient Type
            6: 18,   # Doctor
            7: 14,   # Appointment Date
            8: 14,   # Time
            9: 12,   # Duration
            10: 18,  # Insurance Carrier
            11: 12,  # Member ID
            12: 12,  # Group ID
            13: 12,  # Status
            14: 18,  # Appointment ID
            15: 25   # Notes
        }
        
        for col_idx, width in column_widths.items():
            worksheet.column_dimensions[get_column_letter(col_idx)].width = width
    
    def get_report_path(self) -> str:
        """
        Get the full path to the report file
        
        Returns:
            str: Absolute path to report Excel file
        """
        return os.path.abspath(self.report_path)
    
    def get_record_count(self) -> int:
        """
        Get the total number of appointment records in the report
        
        Returns:
            int: Number of records (excluding header)
        """
        if not os.path.exists(self.report_path):
            return 0
        
        try:
            wb = load_workbook(self.report_path)
            ws = wb.active
            return max(0, ws.max_row - 1)  # Subtract 1 for header
        except:
            return 0
    
    def get_report_summary(self) -> Dict:
        """
        Get summary statistics of the report
        
        Returns:
            dict: Report statistics {
                'total_records': int,
                'confirmed_appointments': int,
                'cancelled_appointments': int,
                'report_path': str,
                'last_updated': str
            }
        """
        if not os.path.exists(self.report_path):
            return {
                'total_records': 0,
                'confirmed_appointments': 0,
                'cancelled_appointments': 0,
                'report_path': self.get_report_path(),
                'last_updated': 'Never'
            }
        
        try:
            wb = load_workbook(self.report_path)
            ws = wb.active
            
            total_records = max(0, ws.max_row - 1)
            confirmed_count = 0
            cancelled_count = 0
            
            # Count confirmed and cancelled from Status column (column 13)
            for row_idx in range(2, ws.max_row + 1):
                status_cell = ws.cell(row=row_idx, column=13)
                if status_cell.value == "Confirmed":
                    confirmed_count += 1
                elif status_cell.value == "Cancelled":
                    cancelled_count += 1
            
            # Get file modification time
            file_stats = os.stat(self.report_path)
            last_modified = datetime.fromtimestamp(file_stats.st_mtime)
            last_updated = last_modified.strftime("%Y-%m-%d %H:%M:%S")
            
            return {
                'total_records': total_records,
                'confirmed_appointments': confirmed_count,
                'cancelled_appointments': cancelled_count,
                'report_path': self.get_report_path(),
                'last_updated': last_updated
            }
        
        except Exception as e:
            return {
                'total_records': 0,
                'confirmed_appointments': 0,
                'cancelled_appointments': 0,
                'error': str(e),
                'report_path': self.get_report_path()
            }


class ReportService:
    """
    High-level service for report operations
    Provides clean interface to appointment reporting
    """
    
    def __init__(self, report_path: str = None):
        """
        Initialize report service
        
        Args:
            report_path: Optional custom path for Excel reports
        """
        self.generator = ExcelReportGenerator(report_path)
        
    def record_appointment(self, state) -> bool:
            # Extract data from state — supports both dict and object
            if isinstance(state, dict):
                get = lambda k, d=None: state.get(k, d)
            else:
                get = lambda k, d=None: getattr(state, k, d)

            appointment_data = {
                'patient_name':         get('patient_name'),
                'patient_dob':          get('patient_dob'),
                'patient_type':         get('patient_type'),
                'preferred_doctor':     get('preferred_doctor'),
                'appointment_date':     get('appointment_date'),
                'selected_time':        get('selected_time'),
                'appointment_duration': get('appointment_duration'),
                'insurance_carrier':    get('insurance_carrier') or "None",
                'insurance_member_id':  get('insurance_member_id'),
                'insurance_group_id':   get('insurance_group_id'),
                'booking_confirmed':    get('booking_confirmed'),
                'appointment_id':       get('appointment_id'),
                'notes': get('error_message') if not get('booking_success') else ""
            }

            return self.generator.add_appointment_record(appointment_data)
    
    def get_summary(self) -> Dict:
        """
        Get report summary statistics
        
        Returns:
            dict: Report statistics and summary info
        """
        return self.generator.get_report_summary()
    
    def get_report_location(self) -> str:
        """
        Get the location of the report file
        
        Returns:
            str: Full path to report
        """
        return self.generator.get_report_path()
    
    def get_record_count(self) -> int:
        """
        Get number of records in the report
        
        Returns:
            int: Total appointment records
        """
        return self.generator.get_record_count()


# Convenience function for quick report generation
def create_report_service(report_path: str = None) -> ReportService:
    """
    Factory function to create a report service instance
    
    Args:
        report_path: Optional custom path for Excel reports
    
    Returns:
        ReportService: Initialized report service
    """
    return ReportService(report_path)
