"""
Email Service Layer
Handles email delivery with SMTP support and retry logic

Features:
- SMTP email sending (Gmail, SendGrid, etc.)
- Email template rendering
- Retry logic with exponential backoff
- Delivery status tracking
- HTML and plain text support
"""

import logging
import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


class EmailConfig:
    """Email service configuration"""

    def __init__(self):
        """Initialize email configuration from environment or defaults"""
        # Email provider settings
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", 587))
        self.sender_email = os.getenv("SENDER_EMAIL", "noreply@medical-scheduler.com")
        self.sender_name = os.getenv("SENDER_NAME", "Medical Appointment Scheduler")
        self.sender_password = os.getenv("SENDER_PASSWORD", "")

        # Retry settings
        self.max_retries = int(os.getenv("EMAIL_MAX_RETRIES", 3))
        self.retry_delay_seconds = int(os.getenv("EMAIL_RETRY_DELAY", 5))

        # Feature flags
        self.use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
        self.test_mode = os.getenv("EMAIL_TEST_MODE", "false").lower() == "true"


class EmailService:
    """Service for sending emails with retry logic and tracking"""

    def __init__(self, config: EmailConfig | None = None):
        """
        Initialize email service

        Args:
            config: EmailConfig instance (uses defaults if None)
        """
        self.config = config or EmailConfig()
        self.delivery_log = {}
        logger.info(f"EmailService initialized with SMTP server: {self.config.smtp_server}")

    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html_body: str | None = None,
        attachments: dict | None = None,
    ) -> tuple[bool, str]:
        """
        Send email with retry logic

        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Plain text email body
            html_body: HTML email body (optional, sends both text and HTML)
            attachments: Dict of filename -> file content (optional)

        Returns:
            Tuple[bool, str]: (success, message)
        """
        if not self._validate_email(to_email):
            error_msg = f"Invalid email address: {to_email}"
            logger.warning(error_msg)
            return False, error_msg

        # Test mode: skip actual sending
        if self.config.test_mode:
            return self._handle_test_mode(to_email, subject, body)

        # Attempt to send with retries
        for attempt in range(self.config.max_retries):
            success, message = self._send_email_attempt(
                to_email, subject, body, html_body, attachments
            )

            if success:
                # Log successful delivery
                self.delivery_log[to_email] = {
                    "sent_at": datetime.now().isoformat(),
                    "status": "delivered",
                    "attempts": attempt + 1,
                    "subject": subject,
                }
                logger.info(f"Email sent successfully to {to_email} (attempt {attempt + 1})")
                return True, message

            # Log failed attempt
            logger.warning(
                f"Email failed for {to_email} (attempt {attempt + 1}/{self.config.max_retries}): {message}"
            )

            if attempt < self.config.max_retries - 1:
                # Wait before retry
                import time

                delay = self.config.retry_delay_seconds * (2**attempt)  # Exponential backoff
                logger.info(f"Retrying in {delay} seconds...")
                time.sleep(delay)

        # All retries failed
        error_msg = f"Failed to send email after {self.config.max_retries} attempts"
        self.delivery_log[to_email] = {
            "sent_at": datetime.now().isoformat(),
            "status": "failed",
            "attempts": self.config.max_retries,
            "subject": subject,
        }
        logger.error(error_msg)
        return False, error_msg

    def _send_email_attempt(
        self,
        to_email: str,
        subject: str,
        body: str,
        html_body: str | None,
        attachments: dict | None,
    ) -> tuple[bool, str]:
        """
        Single email sending attempt

        Args:
            to_email: Recipient email
            subject: Email subject
            body: Plain text body
            html_body: HTML body (optional)
            attachments: File attachments (optional)

        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.config.sender_name} <{self.config.sender_email}>"
            message["To"] = to_email

            # Attach plain text
            message.attach(MIMEText(body, "plain"))

            # Attach HTML if provided
            if html_body:
                message.attach(MIMEText(html_body, "html"))

            # Attach files if provided
            if attachments:
                for filename, content in attachments.items():
                    from email import encoders
                    from email.mime.base import MIMEBase

                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(content)
                    encoders.encode_base64(part)
                    part.add_header("Content-Disposition", f"attachment; filename= {filename}")
                    message.attach(part)

            # Send email
            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                if self.config.use_tls:
                    server.starttls()

                # Authenticate if password provided
                if self.config.sender_password:
                    server.login(self.config.sender_email, self.config.sender_password)

                server.send_message(message)

            return True, f"Email sent successfully to {to_email}"

        except smtplib.SMTPAuthenticationError as e:
            return False, f"SMTP authentication failed: {str(e)}"
        except smtplib.SMTPException as e:
            return False, f"SMTP error: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"

    def _validate_email(self, email: str) -> bool:
        """
        Validate email format

        Args:
            email: Email address to validate

        Returns:
            bool: True if valid format
        """
        import re

        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(pattern, email) is not None

    def _handle_test_mode(self, to_email: str, subject: str, body: str) -> tuple[bool, str]:
        """
        Handle test mode (print instead of sending)

        Args:
            to_email: Recipient email
            subject: Email subject
            body: Email body

        Returns:
            Tuple[bool, str]: (success, message)
        """
        print(f"\n{'='*70}")
        print(f"📧 EMAIL TEST MODE - Email would be sent to: {to_email}")
        print(f"{'='*70}")
        print(f"Subject: {subject}")
        print(f"Body:\n{body}")
        print(f"{'='*70}\n")

        logger.info(f"Test mode: Email would be sent to {to_email}")
        return True, f"Test mode: Email would be sent to {to_email}"

    def get_delivery_status(self, to_email: str) -> dict | None:
        """
        Get delivery status for an email address

        Args:
            to_email: Email address to check

        Returns:
            Dict with delivery info or None if not found
        """
        return self.delivery_log.get(to_email)

    def get_delivery_log(self) -> dict:
        """
        Get complete delivery log

        Returns:
            Dict with all email delivery records
        """
        return self.delivery_log.copy()


# Global email service instance
_email_service: EmailService | None = None


def get_email_service() -> EmailService:
    """
    Get or create global email service instance

    Returns:
        EmailService instance
    """
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service


def send_email(
    to_email: str, subject: str, body: str, html_body: str | None = None
) -> tuple[bool, str]:
    """
    Convenience function to send email using global service

    Args:
        to_email: Recipient email
        subject: Email subject
        body: Email body
        html_body: HTML body (optional)

    Returns:
        Tuple[bool, str]: (success, message)
    """
    service = get_email_service()
    return service.send_email(to_email, subject, body, html_body)
