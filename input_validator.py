"""
Input Validation Module
Validates patient inputs and appointment details
"""
import re
from datetime import datetime
from typing import Tuple, Dict

class InputValidator:
    """Validates user inputs"""
    
    @staticmethod
    def validate_name(name: str) -> Tuple[bool, str]:
        """Validate patient name"""
        name = name.strip()
        if not name:
            return False, "Name cannot be empty"
        if len(name) < 2:
            return False, "Name must be at least 2 characters"
        if len(name) > 100:
            return False, "Name must not exceed 100 characters"
        if not all(c.isalpha() or c.isspace() for c in name):
            return False, "Name can only contain letters and spaces"
        return True, name
    
    @staticmethod
    def validate_dob(dob: str) -> Tuple[bool, str]:
        """Validate date of birth (format: YYYY-MM-DD)"""
        dob = dob.strip()
        try:
            dob_obj = datetime.strptime(dob, "%Y-%m-%d")
            today = datetime.now()
            
            if dob_obj > today:
                return False, "Date of birth cannot be in the future"
            
            age = today.year - dob_obj.year
            if age > 150:
                return False, "Invalid date of birth"
            if age < 0:
                return False, "Date of birth cannot be in the future"
            
            return True, dob
        except ValueError:
            return False, "Invalid date format. Use YYYY-MM-DD (e.g., 1990-05-15)"
    
    @staticmethod
    def validate_email(email: str) -> Tuple[bool, str]:
        """Validate email address"""
        email = email.strip()
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if re.match(pattern, email):
            return True, email
        return False, "Invalid email format"
    
    @staticmethod
    def validate_phone(phone: str) -> Tuple[bool, str]:
        """Validate phone number (10 digits)"""
        phone = phone.strip()
        phone_digits = re.sub(r'\D', '', phone)
        if len(phone_digits) == 10:
            return True, phone_digits
        return False, "Phone number must be 10 digits"
    
    @staticmethod
    def validate_appointment_date(date_str: str) -> Tuple[bool, str]:
        """Validate appointment date (format: YYYY-MM-DD)"""
        date_str = date_str.strip()
        try:
            apt_date = datetime.strptime(date_str, "%Y-%m-%d")
            if apt_date.date() >= datetime.now().date():
                return True, date_str
            return False, "Appointment date must be in the future"
        except ValueError:
            return False, "Invalid date format. Use YYYY-MM-DD"
    
    @staticmethod
    def validate_appointment_time(time_str: str) -> Tuple[bool, str]:
        """Validate appointment time (format: HH:MM, 24-hour format)"""
        time_str = time_str.strip()
        try:
            datetime.strptime(time_str, "%H:%M")
            return True, time_str
        except ValueError:
            return False, "Invalid time format. Use HH:MM (24-hour format, e.g., 14:30)"
    
    @staticmethod
    def validate_insurance_carrier(carrier: str, valid_carriers: list) -> Tuple[bool, str]:
        """Validate insurance carrier"""
        carrier = carrier.strip()
        if carrier in valid_carriers:
            return True, carrier
        return False, f"Invalid carrier. Valid carriers: {', '.join(valid_carriers)}"
    
    @staticmethod
    def validate_member_id(member_id: str) -> Tuple[bool, str]:
        """Validate insurance member ID"""
        member_id = member_id.strip()
        if len(member_id) >= 3:
            return True, member_id
        return False, "Member ID must be at least 3 characters"
    
    @staticmethod
    def validate_group_id(group_id: str) -> Tuple[bool, str]:
        """Validate insurance group ID"""
        group_id = group_id.strip()
        if len(group_id) >= 2:
            return True, group_id
        return False, "Group ID must be at least 2 characters"
    
    @staticmethod
    def get_yes_no_input(prompt: str) -> bool:
        """Get yes/no input from user"""
        while True:
            response = input(prompt + " (yes/no): ").strip().lower()
            if response in ['yes', 'y', '1']:
                return True
            elif response in ['no', 'n', '0']:
                return False
            else:
                print("Please enter 'yes' or 'no'")
