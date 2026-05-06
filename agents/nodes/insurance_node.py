"""
Insurance Node - Chat UI Compatible Version
No print() or input() calls. Everything goes through state.get("response").
Uses state.get("insurance_step") to track progress across turns.
"""
import logging
from agents.state import SchedulerState
from tools import tools
from utils import (
    get_prompt_text_safe,
    format_prompt,
    InsuranceValidator,
    ConfirmationValidator
)

logger = logging.getLogger(__name__)


def insurance_node(state: SchedulerState) -> SchedulerState:

    max_retries = 3
    user_input = (state.get("user_input") or "").strip()

    # Cancellation check
    if user_input.lower() in ['cancel', 'quit', 'exit']:
        state["workflow_complete"] =True
        state["error_message"] ="Insurance collection cancelled"
        state["response"] ="❌ Cancelled. Click **New Conversation** to restart."
        return state

    # Initialize on first entry to this node
    if not state.get("insurance_step"):
        state["insurance_step"] ="ask_coverage"
        state["carrier_retry"] =0
        state["member_retry"] =0
        state["group_retry"] =0

    # =========================================================================
    # STEP 1: ASK IF THEY HAVE INSURANCE
    # =========================================================================
    if state.get("insurance_step") == "ask_coverage":
        state["insurance_step"] ="collect_coverage_answer"
        state["response"] =(
            get_prompt_text_safe('insurance_prompt', 'INSURANCE_QUESTION',
                                 default='🏥 Do you have health insurance? *(yes/no)*')
        )
        return state

    # =========================================================================
    # STEP 2: HANDLE YES/NO ANSWER
    # =========================================================================
    if state.get("insurance_step") == "collect_coverage_answer":
        is_valid, is_yes = ConfirmationValidator.validate_yes_no_response(user_input)

        if not is_valid:
            state["response"] =(
                "⚠️ Please answer **yes** or **no**.\n\n"
                "🏥 Do you have health insurance?"
            )
            return state

        if not is_yes:
            # No insurance — skip to confirmation
            state["insurance_valid"] =False
            state["insurance_carrier"] ="None"
            state["insurance_member_id"] =""
            state["insurance_group_id"] =""
            state["insurance_step"] ="done"
            state["current_step"] ="confirmation"
            state["response"] =(
                get_prompt_text_safe('insurance_prompt', 'NO_INSURANCE',
                                     default='✅ Noted — no insurance coverage. Moving to confirmation...')
            )
            return state

        # Has insurance — fetch carriers
        try:
            carriers = tools.notification.get_valid_carriers()
        except Exception as e:
            state["workflow_complete"] =True
            state["error_message"] =f"Could not fetch carriers: {str(e)}"
            state["response"] =f"❌ Could not fetch insurance carriers: {str(e)}"
            return state

        if not carriers:
            state["workflow_complete"] =True
            state["error_message"] ="No insurance carriers available"
            state["response"] ="❌ No insurance carriers available right now."
            return state

        # Store carriers in state for next turn
        state["available_carriers"] =carriers
        carrier_list = "\n".join([
            f"  {i}. {c}" for i, c in enumerate(carriers, 1)
        ])

        state["insurance_step"] ="select_carrier"
        state["carrier_retry"] =0
        state["response"] =(
            "🏥 **Available Insurance Carriers:**\n\n"
            f"{carrier_list}\n\n"
            "Please enter the **number** of your insurance carrier:"
        )
        return state

    # =========================================================================
    # STEP 3: COLLECT CARRIER SELECTION
    # =========================================================================
    if state.get("insurance_step") == "select_carrier":
        carriers = state.get("available_carriers") or []

        try:
            choice = int(user_input)
            if 1 <= choice <= len(carriers):
                state["insurance_carrier"] =carriers[choice - 1]
                state["insurance_step"] ="collect_member_id"
                state["member_retry"] =0
                logger.info(f"Carrier selected: {state.get("insurance_carrier")}")
                state["response"] =(
                    f"✅ Selected: **{state.get("insurance_carrier")}**\n\n"
                    + get_prompt_text_safe('insurance_prompt', 'MEMBER_ID',
                                          default='💳 Please enter your **Member ID**:')
                )
                return state
            else:
                raise ValueError("out of range")
        except ValueError:
            state["carrier_retry"] = state.get("carrier_retry", 0) + 1
            remaining = max_retries - state.get("carrier_retry")
            if remaining <= 0:
                state["workflow_complete"] =True
                state["error_message"] ="Too many invalid carrier selections"
                state["response"] ="❌ Too many invalid attempts. Click **New Conversation** to restart."
                return state
            state["response"] =(
                f"⚠️ Invalid selection. Enter a number between 1 and {len(carriers)}. "
                f"({remaining} attempt(s) left)"
            )
            return state

    # =========================================================================
    # STEP 4: COLLECT MEMBER ID
    # =========================================================================
    if state.get("insurance_step") == "collect_member_id":
        valid, result = InsuranceValidator.validate_member_id(user_input)

        if valid:
            state["insurance_member_id"] =result
            state["insurance_step"] ="collect_group_id"
            state["group_retry"] =0
            logger.info(f"Member ID collected: {result}")
            state["response"] =(
                get_prompt_text_safe('insurance_prompt', 'GROUP_ID',
                                     default='🔢 Please enter your **Group ID**:')
            )
            return state
        else:
            state["member_retry"] = state.get("member_retry", 0) + 1
            remaining = max_retries - state.get("member_retry")
            if remaining <= 0:
                state["workflow_complete"] =True
                state["error_message"] ="Too many invalid member ID entries"
                state["response"] ="❌ Too many invalid attempts. Click **New Conversation** to restart."
                return state
            state["response"] =(
                f"⚠️ Invalid Member ID: {result}\n\n"
                f"Please try again. ({remaining} attempt(s) left)"
            )
            return state

    # =========================================================================
    # STEP 5: COLLECT GROUP ID
    # =========================================================================
    if state.get("insurance_step") == "collect_group_id":
        if not user_input:
            state["response"] ="⚠️ Group ID is required. Please enter your **Group ID**:"
            return state

        valid, result = InsuranceValidator.validate_group_id(user_input)

        if valid:
            state["insurance_group_id"] =result
            logger.info(f"Group ID collected: {result}")
            # Validate all fields together
            state["insurance_step"] ="validate"
            # Fall through to validate immediately

        else:
            state["group_retry"] = state.get("group_retry", 0) + 1
            remaining = max_retries - state.get("group_retry")
            if remaining <= 0:
                state["workflow_complete"] =True
                state["error_message"] ="Too many invalid group ID entries"
                state["response"] ="❌ Too many invalid attempts. Click **New Conversation** to restart."
                return state
            state["response"] =(
                f"⚠️ Invalid Group ID: {result}\n\n"
                f"Please try again. ({remaining} attempt(s) left)"
            )
            return state

    # =========================================================================
    # STEP 6: VALIDATE ALL FIELDS + TOOL CHECK
    # =========================================================================
    if state.get("insurance_step") == "validate":
        carriers = state.get("available_carriers") or []
        all_valid, validation_results = InsuranceValidator.validate_all_insurance_fields(
            state.get("insurance_carrier"),
            state.get("insurance_member_id"),
            state.get("insurance_group_id"),
            carriers
        )

        if not all_valid:
            error_details = "\n".join(validation_results.get('errors', ['Unknown error']))
            state["insurance_valid"] =False
            state["error_message"] ="Insurance validation failed"
            state["insurance_step"] ="done"
            state["current_step"] ="confirmation"
            state["response"] =(
                f"⚠️ Insurance validation failed:\n{error_details}\n\n"
                "Proceeding to confirmation with unverified insurance."
            )
            return state

        # Call notification tool
        try:
            result = tools.notification.collect_insurance({
                'carrier': state.get("insurance_carrier"),
                'member_id': state.get("insurance_member_id"),
                'group_id': state.get("insurance_group_id")
            })

            if result.get('valid', False):
                state["insurance_valid"] =True
                state["insurance_step"] ="done"
                state["current_step"] ="confirmation"
                state["response"] =(
                    "✅ **Insurance Verified!**\n\n"
                    f"**Carrier:** {state.get("insurance_carrier")}\n"
                    f"**Member ID:** {state.get("insurance_member_id")}\n"
                    f"**Group ID:** {state.get("insurance_group_id")}\n\n"
                    "Moving to appointment confirmation... 📋"
                )
                return state
            else:
                validation_error = result.get('message', 'Verification failed')
                state["insurance_valid"] =False
                state["error_message"] =validation_error
                state["insurance_step"] ="done"
                state["current_step"] ="confirmation"
                state["response"] =(
                    f"⚠️ Insurance could not be verified: {validation_error}\n\n"
                    "Proceeding to confirmation anyway."
                )
                return state

        except Exception as e:
            logger.error(f"Insurance tool error: {e}")
            state["insurance_valid"] =False
            state["insurance_step"] ="done"
            state["current_step"] ="confirmation"
            state["response"] =(
                f"⚠️ Could not verify insurance: {str(e)}\n\n"
                "Proceeding to confirmation anyway."
            )
            return state

    # Fallback
    logger.error(f"Unknown insurance_step: {state.get("insurance_step")}")
    state["response"] ="⚠️ Something went wrong. Please click **New Conversation** to restart."
    state["workflow_complete"] =True
    return state