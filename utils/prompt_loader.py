"""
Prompt Loader Utility
Purpose: Dynamically load and manage prompts from the prompts/ folder
Features: Load full prompts or specific sections with variable interpolation
"""

import logging
from pathlib import Path

# Configure logging for prompt warnings
logger = logging.getLogger(__name__)


class PromptLoader:
    """
    Centralized prompt loading system for the medical scheduling agent.

    Enables:
    - Loading prompt files dynamically
    - Extracting specific sections from prompts
    - Variable interpolation in prompts
    - Consistent prompt management across all nodes
    """

    def __init__(self, prompts_dir: str = None):
        """
        Initialize the prompt loader.

        Args:
            prompts_dir: Path to prompts folder.
                        If None, uses 'prompts/' relative to this file.
        """
        if prompts_dir is None:
            # Get the directory where this file is located (utils/)
            current_dir = Path(__file__).parent.parent
            prompts_dir = current_dir / "prompts"

        self.prompts_dir = Path(prompts_dir)
        self._cache: dict[str, str] = {}  # Cache loaded prompts

        if not self.prompts_dir.exists():
            raise FileNotFoundError(f"Prompts directory not found: {self.prompts_dir}")

    def load_prompt(self, name: str) -> str:
        """
        Load entire prompt file by name.

        Args:
            name: Prompt name (e.g., 'system_prompt', 'scheduling_prompt')

        Returns:
            Full prompt file content as string

        Example:
            prompt = loader.load_prompt('system_prompt')
        """
        # Check cache first
        if name in self._cache:
            return self._cache[name]

        prompt_file = self.prompts_dir / f"{name}.txt"

        if not prompt_file.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_file}")

        with open(prompt_file, encoding="utf-8") as f:
            content = f.read()

        # Cache for quick access
        self._cache[name] = content
        return content

    def get_section(self, prompt_name: str, section: str) -> str:
        """
        Extract a specific section from a prompt file.

        Sections are marked with [SECTION: NAME] or similar tags.

        Args:
            prompt_name: Name of prompt file (e.g., 'extraction_prompt')
            section: Section name (e.g., 'HEADER', 'DOCTOR_SELECTION')

        Returns:
            Content of the specified section

        Example:
            prompt = loader.get_section('extraction_prompt', 'HEADER')
        """
        full_prompt = self.load_prompt(prompt_name)

        # Parse sections between tags like [SECTION: NAME] or [MESSAGE: NAME]
        section_marker = f"[SECTION: {section}]"

        if section_marker not in full_prompt:
            # Try alternative markers
            for prefix in [
                "[PROMPT:",
                "[FEEDBACK:",
                "[ERROR:",
                "[STATUS:",
                "[MESSAGE:",
                "[NOTE:",
                "[DISPLAY:",
                "[WARNING:",
            ]:
                alt_marker = f"{prefix} {section}]"
                if alt_marker in full_prompt:
                    section_marker = alt_marker
                    break
            else:
                raise ValueError(f"Section '{section}' not found in {prompt_name}")

        # Extract content after marker until next section or end
        start_idx = full_prompt.find(section_marker) + len(section_marker)

        # Find next section marker
        next_section = full_prompt.find("\n[", start_idx)
        if next_section == -1:
            end_idx = len(full_prompt)
        else:
            end_idx = next_section

        content = full_prompt[start_idx:end_idx].strip()
        return content

    def get_prompt_text(self, prompt_name: str, item_name: str) -> str:
        """
        Get a single prompt text by prompt_name and item_name.

        Useful for getting specific prompts like user input prompts.
        Handles [PROMPT: NAME], [FEEDBACK: NAME], [ERROR: NAME], etc.

        Args:
            prompt_name: Name of prompt file
            item_name: Item to retrieve (e.g., 'NAME', 'EMAIL', 'CONFIRMATION_QUESTION')

        Returns:
            The prompt or feedback text

        Example:
            email_prompt = loader.get_prompt_text('extraction_prompt', 'EMAIL')
            # Returns: "Email address: "
        """
        full_prompt = self.load_prompt(prompt_name)

        # Try different prefixes
        for prefix in [
            "[PROMPT:",
            "[FEEDBACK:",
            "[ERROR:",
            "[STATUS:",
            "[MESSAGE:",
            "[NOTE:",
            "[WARNING:",
            "[SUCCESS:",
            "[DISPLAY:",
        ]:
            marker = f"{prefix} {item_name}]"

            if marker in full_prompt:
                start_idx = full_prompt.find(marker) + len(marker)
                # Find end of line
                end_idx = full_prompt.find("\n", start_idx)
                if end_idx == -1:
                    end_idx = len(full_prompt)

                content = full_prompt[start_idx:end_idx].strip()
                return content

        raise ValueError(f"Item '{item_name}' not found in {prompt_name}")

    def get_section_safe(self, prompt_name: str, section: str, default: str | None = None) -> str:
        """
        Safely get a section from a prompt, with fallback to default.

        Does not raise exception if section is missing. Instead logs a warning
        and returns the provided default text.

        Args:
            prompt_name: Name of prompt file (e.g., 'extraction_prompt')
            section: Section name (e.g., 'HEADER', 'PATIENT_INFO_HEADER')
            default: Default text to return if section not found.
                    If None, uses a simple generated prompt.

        Returns:
            Section content or default text

        Example:
            header = get_section_safe('extraction_prompt', 'PATIENT_INFO_HEADER',
                                     default='Please enter your information:')
        """
        try:
            return self.get_section(prompt_name, section)
        except (ValueError, FileNotFoundError) as e:
            # Log the warning but don't crash
            logger.warning(
                f"Missing prompt section: '{section}' in '{prompt_name}'. "
                f"Using fallback. Error: {str(e)}"
            )

            # Return sensible defaults if not provided
            if default is not None:
                return default

            # Generate a reasonable default based on section name
            section_lower = section.lower()
            if "header" in section_lower:
                return "─" * 70
            elif "cancelled" in section_lower or "cancel" in section_lower:
                return "Workflow cancelled by user."
            elif "error" in section_lower:
                return "An error occurred. Please try again."
            else:
                return ""

    def get_prompt_text_safe(
        self, prompt_name: str, item_name: str, default: str | None = None
    ) -> str:
        """
        Safely get a prompt text, with fallback to default.

        Does not raise exception if item is missing. Instead logs a warning
        and returns the provided default text.

        Args:
            prompt_name: Name of prompt file (e.g., 'extraction_prompt')
            item_name: Item to retrieve (e.g., 'NAME', 'EMAIL')
            default: Default text to return if item not found.
                    If None, generates reasonable default.

        Returns:
            Prompt text or default

        Example:
            prompt = get_prompt_text_safe('extraction_prompt', 'NAME',
                                         default='Please enter your name: ')
        """
        try:
            return self.get_prompt_text(prompt_name, item_name)
        except (ValueError, FileNotFoundError) as e:
            # Log the warning but don't crash
            logger.warning(
                f"Missing prompt item: '{item_name}' in '{prompt_name}'. "
                f"Using fallback. Error: {str(e)}"
            )

            # Return sensible defaults if not provided
            if default is not None:
                return default

            # Generate reasonable defaults based on item name
            item_lower = item_name.lower()
            defaults = {
                "name": "Please enter your full name: ",
                "dob": "Please enter your date of birth (YYYY-MM-DD): ",
                "email": "Please enter your email address: ",
                "phone": "Please enter your phone number: ",
                "confirmation": "Do you want to proceed? (yes/no): ",
                "error": "An error occurred. ",
                "success": "Success! ",
                "processing": "Processing... ",
                "cancelled": "Operation cancelled.",
                "lookup_processing": "Looking up your information... ",
                "lookup_error": "Could not look up information: {error_message}",
                "lookup_cancelled": "Lookup cancelled.",
                "patient_found": "Welcome back, patient {patient_id}! ",
                "patient_new": "Registered as new patient. ",
                "patient_info_header": "─ Patient Information ─",
                "contact_header": "─ Contact Information ─",
                "contact_cancelled": "Contact information cancelled.",
                "contact_confirmed": "Contact information saved.",
            }

            # Try to find a matching default
            for key, value in defaults.items():
                if key == item_lower or key in item_lower:
                    return value

            # Generic fallback
            return f"{item_name}: "

    def format_prompt(self, prompt_text: str, **kwargs) -> str:
        """
        Format a prompt with variable substitution.

        Args:
            prompt_text: Prompt text with placeholders like {variable_name}
            **kwargs: Variables to substitute

        Returns:
            Formatted prompt text

        Example:
            prompt = loader.get_prompt_text('extraction_prompt', 'PATIENT_FOUND')
            # Returns: "✓ Welcome back! Your patient ID: {patient_id}..."
            formatted = loader.format_prompt(prompt, patient_id="P123", appointment_count=5)
        """
        return prompt_text.format(**kwargs)

    def get_header(self, prompt_name: str) -> str:
        """
        Get the section header (visual separator + title).

        Args:
            prompt_name: Prompt file name

        Returns:
            Formatted header text

        Example:
            header = loader.get_header('scheduling_prompt')
        """
        try:
            return self.get_section(prompt_name, "HEADER")
        except ValueError:
            return "-" * 70

    def print_header(self, prompt_name: str) -> None:
        """
        Convenience method to print a section header directly.

        Args:
            prompt_name: Prompt file name
        """
        header = self.get_header(prompt_name)
        print(header)

    def list_available_prompts(self) -> list:
        """
        List all available prompt files.

        Returns:
            List of prompt names (without .txt extension)
        """
        if not self.prompts_dir.exists():
            return []

        prompts = [f.stem for f in self.prompts_dir.glob("*.txt")]
        return sorted(prompts)

    def clear_cache(self) -> None:
        """Clear the prompt cache to force reload from disk."""
        self._cache.clear()


# Create a global instance for convenient access
_default_loader = None


def get_loader(prompts_dir: str = None) -> PromptLoader:
    """
    Get the default prompt loader instance.

    Args:
        prompts_dir: Optional path to prompts folder

    Returns:
        PromptLoader instance

    Example:
        from utils.prompt_loader import get_loader
        loader = get_loader()
        prompt = loader.load_prompt('system_prompt')
    """
    global _default_loader
    if _default_loader is None:
        _default_loader = PromptLoader(prompts_dir)
    return _default_loader


# Convenience functions for direct access
def load_prompt(name: str) -> str:
    """Shorthand: Load entire prompt file."""
    return get_loader().load_prompt(name)


def get_prompt_text(prompt_name: str, item_name: str) -> str:
    """Shorthand: Get specific prompt text."""
    return get_loader().get_prompt_text(prompt_name, item_name)


def get_prompt_text_safe(prompt_name: str, item_name: str, default: str | None = None) -> str:
    """Shorthand: Get specific prompt text with safe fallback."""
    return get_loader().get_prompt_text_safe(prompt_name, item_name, default)


def format_prompt(prompt_text: str, **kwargs) -> str:
    """Shorthand: Format prompt with variables."""
    return get_loader().format_prompt(prompt_text, **kwargs)


def get_section(prompt_name: str, section: str) -> str:
    """Shorthand: Get specific section from prompt."""
    return get_loader().get_section(prompt_name, section)


def get_section_safe(prompt_name: str, section: str, default: str | None = None) -> str:
    """Shorthand: Get specific section from prompt with safe fallback."""
    return get_loader().get_section_safe(prompt_name, section, default)
