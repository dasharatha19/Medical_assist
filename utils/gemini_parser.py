"""
Gemini LLM Parser
Leverages Google Gemini API for natural language understanding and field extraction

Features:
- Parse free-form user input into structured fields
- Extract name, DOB, phone, email, doctor preference, insurance info
- Graceful error handling and fallback support
- Production-ready with safe import and initialization
- Logging and monitoring

Dependencies:
- google-generativeai>=0.7.0 (optional - falls back to rule-based parsing if missing)
"""
import json
import logging
import os
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

# Safe import with graceful fallback
try:
    import google.generativeai as genai
    from google.generativeai.generative_models import GenerativeModel
    from google.generativeai.client import configure
    GENAI_AVAILABLE = True
except ImportError:
    genai = None
    GenerativeModel = None
    configure = None
    GENAI_AVAILABLE = False


logger = logging.getLogger(__name__)


class GeminiParser:
    """
    Natural Language Parser using Google Gemini API
    Extracts structured information from conversational user input
    """
    
    # Extraction template for consistent output
    EXTRACTION_TEMPLATE = """
You are a helpful assistant for a medical appointment scheduling system.
Extract the following information from the user input if available.
Return ONLY valid JSON, nothing else.

Fields to extract (use null if not found):
- name: Patient full name
- date_of_birth: Date of birth in YYYY-MM-DD format
- age: Age if mentioned
- phone: Phone number
- email: Email address
- location: Location/city mentioned
- doctor_preference: Preferred doctor name or specialty
- insurance_provider: Insurance company name
- insurance_id: Insurance member ID
- intent: Primary intent (e.g., "schedule_appointment", "check_availability")

User input: "{user_input}"

Return valid JSON response:
"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini Parser with safe import and configuration handling
        
        Args:
            api_key: Google Gemini API key. If None, uses GEMINI_API_KEY env var
                    If not found, parser will be disabled with graceful fallback
        """
        from utils.config import Config
        
        # Get API key from parameter, environment, or config
        self.api_key = api_key or os.getenv('GEMINI_API_KEY') or Config.GEMINI_API_KEY
        self.model_name = Config.LLM_MODEL
        self.temperature = Config.LLM_TEMPERATURE
        self.max_tokens = Config.LLM_MAX_TOKENS
        self.timeout = Config.LLM_TIMEOUT
        self.enabled = False
        self.model = None
        self.init_error = None
        
        # Check if google-generativeai package is available
        if not GENAI_AVAILABLE:
            error_msg = (
                "google.generativeai package not installed. "
                "Install with: pip install google-generativeai>=0.7.0"
            )
            logger.warning(error_msg)
            self.init_error = error_msg
            self.enabled = False
            return
        
        if not genai:
            error_msg = "google.generativeai import failed unexpectedly"
            logger.error(error_msg)
            self.init_error = error_msg
            self.enabled = False
            return
        
        # Check if required functions/classes are available
        if not GenerativeModel or not configure:
            error_msg = "GenerativeModel or configure not available from google.generativeai"
            logger.error(error_msg)
            self.init_error = error_msg
            self.enabled = False
            return
        
        # Check if API key is configured
        if not self.api_key or not self.api_key.strip():
            warning_msg = (
                "GEMINI_API_KEY not set. LLM parsing will be disabled. "
                "Set GEMINI_API_KEY environment variable or Config.GEMINI_API_KEY to enable. "
                "Fallback to rule-based parsing will be used."
            )
            logger.debug(warning_msg)
            self.init_error = warning_msg
            self.enabled = False
            return
        
        # Try to initialize Gemini model
        try:
            # Configure API key with genai.configure()
            configure(api_key=self.api_key.strip())
            logger.debug(f"Gemini API configured, initializing {self.model_name}")
            
            # Create GenerativeModel instance with configuration
            try:
                self.model = GenerativeModel(
                    model_name=self.model_name,
                    generation_config={
                        'temperature': self.temperature,
                        'max_output_tokens': self.max_tokens,
                    }
                )
                self.enabled = True
                logger.info(f"Gemini Parser initialized successfully with model: {self.model_name}")
            except TypeError as e:
                error_msg = f"Failed to create Gemini model (SDK compatibility issue): {str(e)}"
                logger.error(error_msg)
                self.init_error = error_msg
                self.enabled = False
                self.model = None
            except Exception as e:
                error_msg = f"Failed to create Gemini model: {str(e)}"
                logger.error(error_msg)
                self.init_error = error_msg
                self.enabled = False
                self.model = None
        
        except AttributeError as e:
            error_msg = f"Failed to configure Gemini API (SDK issue): {str(e)}. Using fallback parsing."
            logger.warning(error_msg)
            self.init_error = error_msg
            self.enabled = False
            self.model = None
        except Exception as e:
            error_msg = f"Failed to configure Gemini API: {str(e)}"
            logger.error(error_msg)
            self.init_error = error_msg
            self.enabled = False
            self.model = None
    
    def parse_user_input(self, user_input: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Parse user input using Gemini LLM with comprehensive error handling
        
        Args:
            user_input: User's conversational input
        
        Returns:
            Tuple of (success: bool, parsed_fields: dict)
            - success: True if parsing succeeded, False if failed or parser disabled
            - parsed_fields: Extracted and validated fields, empty dict if parsing failed
            
        Example:
            success, fields = parser.parse_user_input("My name is John Smith, born in 1990")
            if success:
                name = fields.get('name')
                dob = fields.get('date_of_birth')
        """
        # Check if parser is enabled
        if not self.enabled:
            if self.init_error:
                logger.debug(f"Gemini parser disabled during init: {self.init_error}")
            else:
                logger.debug("Gemini parser not enabled, returning empty result")
            return False, {}
        
        # Check if model is properly initialized
        if not self.model:
            error_msg = "Gemini model not available despite parser being marked as enabled"
            logger.error(error_msg)
            self.enabled = False
            return False, {}
        
        # Validate input
        if not user_input or not user_input.strip():
            logger.debug("Empty user input provided")
            return False, {}
        
        user_input = user_input.strip()
        
        try:
            # Build extraction prompt
            prompt = self.EXTRACTION_TEMPLATE.format(user_input=user_input)
            
            logger.debug(f"Calling Gemini API for user input extraction")
            
            # Call Gemini API with error handling
            try:
                response = self.model.generate_content(prompt)
            except TypeError as e:
                logger.error(f"Gemini API type error (likely API configuration issue): {str(e)}")
                return False, {}
            except Exception as e:
                logger.error(f"Gemini API call failed: {str(e).__class__.__name__}: {str(e)}")
                return False, {}
            
            # Validate response
            if not response:
                logger.warning("Gemini returned None response object")
                return False, {}
            
            if not hasattr(response, 'text') or not response.text:
                logger.warning("Gemini response missing text attribute or text is empty")
                return False, {}
            
            # Parse JSON response
            response_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith('```'):
                response_text = response_text.split('```')[1]
            if response_text.startswith('json'):
                response_text = response_text[4:]
            
            response_text = response_text.strip()
            
            if not response_text:
                logger.warning("Gemini response was empty after removing markdown")
                return False, {}
            
            # Parse JSON
            try:
                parsed_fields = json.loads(response_text)
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON from Gemini (line {e.lineno}, col {e.colno}): {e.msg}")
                logger.debug(f"Response text was: {response_text[:200]}...")
                return False, {}
            
            # Validate and clean parsed fields
            cleaned_fields = self._validate_fields(parsed_fields)
            
            extracted_count = len([v for v in cleaned_fields.values() if v is not None])
            logger.info(f"Successfully parsed user input. Extracted {extracted_count} fields: {list(cleaned_fields.keys())}")
            
            return True, cleaned_fields
        
        except Exception as e:
            logger.error(f"Unexpected error in parse_user_input: {str(e).__class__.__name__}: {str(e)}")
            logger.exception("Full traceback:")
            return False, {}
    
    def _validate_fields(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and clean extracted fields
        
        Args:
            fields: Raw extracted fields from Gemini
            
        Returns:
            Cleaned and validated fields
        """
        cleaned = {}
        
        # Name validation
        if fields.get('name') and isinstance(fields['name'], str):
            name = fields['name'].strip()
            if len(name) >= 2:
                cleaned['name'] = name
        
        # DOB validation and formatting
        if fields.get('date_of_birth'):
            dob = self._parse_date(fields['date_of_birth'])
            if dob:
                cleaned['date_of_birth'] = dob
        
        # Age validation
        if fields.get('age'):
            try:
                age = int(fields['age'])
                if 0 < age < 150:
                    cleaned['age'] = age
            except (ValueError, TypeError):
                pass
        
        # Phone validation
        if fields.get('phone'):
            phone = fields['phone'].replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
            if len(phone) >= 10 and phone.isdigit():
                cleaned['phone'] = phone
        
        # Email validation
        if fields.get('email') and isinstance(fields['email'], str):
            email = fields['email'].strip()
            if '@' in email and '.' in email:
                cleaned['email'] = email
        
        # Location (keep as-is if valid)
        if fields.get('location') and isinstance(fields['location'], str):
            location = fields['location'].strip()
            if location:
                cleaned['location'] = location
        
        # Doctor preference
        if fields.get('doctor_preference') and isinstance(fields['doctor_preference'], str):
            doc_pref = fields['doctor_preference'].strip()
            if doc_pref:
                cleaned['doctor_preference'] = doc_pref
        
        # Insurance info
        if fields.get('insurance_provider') and isinstance(fields['insurance_provider'], str):
            provider = fields['insurance_provider'].strip()
            if provider:
                cleaned['insurance_provider'] = provider
        
        if fields.get('insurance_id') and isinstance(fields['insurance_id'], str):
            ins_id = fields['insurance_id'].strip()
            if ins_id:
                cleaned['insurance_id'] = ins_id
        
        # Intent
        if fields.get('intent') and isinstance(fields['intent'], str):
            intent = fields['intent'].strip().lower()
            if intent:
                cleaned['intent'] = intent
        
        return cleaned
    
    def _parse_date(self, date_str: Any) -> Optional[str]:
        """
        Parse date string from various formats to YYYY-MM-DD
        
        Args:
            date_str: Date in various formats
            
        Returns:
            Date in YYYY-MM-DD format or None
        """
        if not isinstance(date_str, str):
            return None
        
        date_str = date_str.strip()
        
        # Try common formats
        formats = [
            '%Y-%m-%d',
            '%Y/%m/%d',
            '%m/%d/%Y',
            '%d/%m/%Y',
            '%m-%d-%Y',
            '%d-%m-%Y',
            '%B %d, %Y',
            '%b %d, %Y',
            '%d %B %Y',
            '%d %b %Y',
        ]
        
        for fmt in formats:
            try:
                parsed = datetime.strptime(date_str, fmt)
                return parsed.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        # If year is provided alone, estimate DOB
        if date_str.isdigit() and len(date_str) == 4:
            try:
                year = int(date_str)
                if 1900 <= year <= 2025:
                    return f"{year}-01-01"
            except ValueError:
                pass
        
        return None
    
    def is_enabled(self) -> bool:
        """Check if Gemini parser is properly enabled"""
        return self.enabled


# Singleton instance
_gemini_parser_instance: Optional[GeminiParser] = None


def get_gemini_parser() -> GeminiParser:
    """
    Get singleton Gemini parser instance
    
    Returns:
        GeminiParser instance
    """
    global _gemini_parser_instance
    if _gemini_parser_instance is None:
        _gemini_parser_instance = GeminiParser()
    return _gemini_parser_instance


def parse_with_gemini(user_input: str) -> Tuple[bool, Dict[str, Any]]:
    """
    Convenience function to parse user input with Gemini
    
    Args:
        user_input: User's conversational input
        
    Returns:
        Tuple of (success, parsed_fields)
    """
    parser = get_gemini_parser()
    return parser.parse_user_input(user_input)
