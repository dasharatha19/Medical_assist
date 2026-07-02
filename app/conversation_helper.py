"""
Conversation Helper Module
Utilities for managing chat flow and extracting meaningful messages from agent output
Provides functions to improve conversation quality and readability
"""

import re


def extract_agent_prompts(output: str) -> list[str]:
    """
    Extract user-facing questions/prompts from agent output
    Filters out debug messages and system info

    Looks for lines that end with ':' or contain typical question indicators

    Args:
        output: Raw agent output containing mixed messages

    Returns:
        List of user-facing prompts extracted from the output
    """
    if not output:
        return []

    prompts = []
    lines = output.split("\n")

    for line in lines:
        stripped = line.strip()

        # Skip empty lines and debug output
        if not stripped or stripped.startswith("❌") or stripped.startswith("✅"):
            continue

        # Lines ending with ':' are typically prompts/questions
        if stripped.endswith(":"):
            # Clean up the prompt
            prompt = stripped.rstrip(":").strip()
            if prompt:
                prompts.append(prompt)

        # Lines with question marks
        elif "?" in stripped:
            prompts.append(stripped)

    return prompts


def get_next_question(output: str) -> str | None:
    """
    Extract the next question/prompt the agent is asking
    Returns the most relevant user-facing question

    Args:
        output: Agent output that may contain multiple messages

    Returns:
        The next question to ask the user, or None if no question found
    """
    prompts = extract_agent_prompts(output)

    if prompts:
        # Return the last/most recent prompt
        return prompts[-1]

    return None


def is_greeting_response(output: str) -> bool:
    """
    Check if output contains a greeting response
    Useful for determining if agent just greeted the user

    Args:
        output: Agent output

    Returns:
        True if output appears to be a greeting
    """
    if not output:
        return False

    greeting_keywords = [
        "welcome",
        "hello",
        "hi",
        "greetings",
        "thank you",
        "pleased to help",
        "get started",
    ]

    output_lower = output.lower()
    return any(keyword in output_lower for keyword in greeting_keywords)


def clean_output_for_display(output: str) -> str:
    """
    Clean agent output for display in chat interface
    Removes debug markers, extra symbols, and formats nicely

    Args:
        output: Raw agent output

    Returns:
        Cleaned output suitable for displaying to user
    """
    if not output:
        return ""

    lines = []

    for line in output.split("\n"):
        # Remove leading/trailing whitespace
        clean_line = line.strip()

        # Skip debug output lines
        if clean_line.startswith("❌"):
            continue

        # Remove redundant checkmarks and arrows
        if clean_line.startswith("✅"):
            # Convert checkmark format to readable text
            message = clean_line[2:].strip()
            clean_line = f"✓ {message}"

        if clean_line:
            lines.append(clean_line)

    # Join lines and clean up multiple spaces
    result = "\n".join(lines)
    result = re.sub(r" +", " ", result)  # Remove multiple spaces

    return result.strip()


def extract_state_from_output(output: str) -> dict:
    """
    Extract state information from agent output
    Looks for patterns indicating state changes or collected information

    Args:
        output: Agent output that may contain state information

    Returns:
        Dictionary with extracted state information
    """
    state_info = {}

    # Look for name patterns
    name_match = re.search(r"(?:name|Name|NAME)[:\s]+([A-Za-z\s]+?)(?:\n|$)", output)
    if name_match:
        state_info["name"] = name_match.group(1).strip()

    # Look for date patterns
    date_match = re.search(r"(?:date|Date)[:\s]+([0-9/-]+)", output)
    if date_match:
        state_info["date"] = date_match.group(1).strip()

    # Look for doctor patterns
    doctor_match = re.search(r"(?:doctor|Doctor)[:\s]+([A-Za-z\s]+?)(?:\n|$)", output)
    if doctor_match:
        state_info["doctor"] = doctor_match.group(1).strip()

    return state_info


def format_conversation_context(
    user_message: str, agent_response: str
) -> tuple[str, str]:
    """
    Format user message and agent response for display
    Ensures proper formatting and readability

    Args:
        user_message: The user's input message
        agent_response: The agent's response output

    Returns:
        Tuple of (formatted_user_message, formatted_agent_response)
    """
    # Format user message
    formatted_user = user_message.strip()

    # Format agent response
    formatted_agent = clean_output_for_display(agent_response)

    return formatted_user, formatted_agent


def should_display_response(output: str) -> bool:
    """
    Determine if agent output should be displayed to user
    Filters out empty or debug-only output

    Args:
        output: Agent output to check

    Returns:
        True if output should be displayed to user
    """
    if not output or not output.strip():
        return False

    # Check if output has actual content (not just debug symbols)
    content = output.strip()

    # If only symbols/checkmarks, don't display
    if all(c in "✅❌⚠️\n" for c in content):
        return False

    return True


def extract_conversation_state(messages: list[dict]) -> dict:
    """
    Extract workflow state from conversation history
    Analyzes messages to determine current workflow position and context

    Args:
        messages: List of conversation messages (user/assistant pairs)

    Returns:
        Dictionary with conversation state analysis
    """
    state = {
        "user_message_count": 0,
        "assistant_message_count": 0,
        "last_user_message": None,
        "last_assistant_message": None,
        "conversation_started": False,
    }

    for message in messages:
        role = message.get("role", "")
        content = message.get("content", "")

        if role == "user":
            state["user_message_count"] += 1
            state["last_user_message"] = content
        elif role == "assistant":
            state["assistant_message_count"] += 1
            state["last_assistant_message"] = content

    # Conversation has started if there are messages beyond just the greeting
    state["conversation_started"] = state["user_message_count"] > 0

    return state
