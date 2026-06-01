"""
Conversation Node — Intelligent AI chatbot node.
Loads static rules from prompts/ folder.
Dynamic context injected at runtime.
"""
import json
import re

from pyarrow.util import doc
from utils.config import Config
import logging
from datetime import datetime, timedelta
import os
from utils.verbose_logger import verbose
from pathlib import Path
from tools import tools
from utils.llm_client import get_llm_client
from utils.validators import (
    PatientDataValidator, ContactValidator,
    SchedulingValidator
)
logger = logging.getLogger(__name__)

# ── Terminal trace logging setup ──────────────────────────────────────────────
import sys
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

PROMPTS_DIR = Path(__file__).parent.parent.parent / "prompts"


def _load_prompt(filename: str) -> str:
    try:
        return (PROMPTS_DIR / filename).read_text(encoding="utf-8").strip()
    except Exception as e:
        logger.warning(f"Could not load prompt {filename}: {e}")
        return ""


def _next_weekdays(n=3) -> list:
    result, d = [], datetime.now().date() + timedelta(days=1)
    while len(result) < n:
        if d.weekday() < 5:
            result.append(str(d))
        d += timedelta(days=1)
    return result


def _resolve_relative_date(text: str) -> str:
    today = datetime.now().date()
    t = text.lower().strip()
    if "tomorrow" in t:
        return str(today + timedelta(days=1))
    if "today" in t:
        return str(today)
    if any(word in t for word in ["asap", "as soon as possible", "urgent", "immediately", "right away", "now"]):
        return str(today)
    days = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]
    for i, day in enumerate(days):
        if day in t:
            delta = (i - today.weekday()) % 7
            if delta == 0:
                delta = 7
            return str(today + timedelta(days=delta))
    return ""

def _build_system_prompt(state: dict, doctors_info: str, slots_block: str) -> str:
    """Assemble full system prompt from files + runtime context."""

    # Load static sections from files
    system_base    = _load_prompt("system_prompt.txt")
    scheduling     = _load_prompt("scheduling_prompt.txt")
    confirmation   = _load_prompt("confirmation_prompt.txt")

    today          = datetime.now().date()
    today_str      = str(today)
    today_weekday  = today.strftime("%A")
    suggested      = ", ".join(_next_weekdays(3))

    # Build collected vs missing
    required = {
        "patient_name":     "full name",
        "patient_dob":      "date of birth",
        "patient_phone":    "phone number",
        "patient_email":    "email address",
        "preferred_doctor": "preferred doctor",
        "appointment_date": "appointment date",
        "selected_time":    "appointment time slot",
    }

    collected_lines = []
    missing_lines   = []
    for field, label in required.items():
        val = state.get(field)
        if val:
            collected_lines.append(f"  ✅ {label}: {val}")
        else:
            missing_lines.append(f"  ❓ {label}")

    carrier = state.get("insurance_carrier", "")
    if not carrier:
        missing_lines.append("  ❓ insurance (say 'no insurance' to skip)")
    elif carrier.lower() not in ["none", "no insurance", "self pay", "out of pocket"]:
        if not state.get("insurance_member_id"):
            missing_lines.append("  ❓ insurance member ID")
        else:
            collected_lines.append(f"  ✅ insurance member ID: {state['insurance_member_id']}")
        if not state.get("insurance_group_id"):
            missing_lines.append("  ❓ insurance group ID")
        else:
            collected_lines.append(f"  ✅ insurance group ID: {state['insurance_group_id']}")

    collected_block = "\n".join(collected_lines) if collected_lines else "  (none yet)"
    missing_block   = "\n".join(missing_lines)   if missing_lines   else "  ✅ All collected!"

    # Patient status
    patient_block = ""
    if state.get("patient_id") and state.get("patient_type"):
        ptype    = state["patient_type"]
        duration = state.get("appointment_duration", 60)
        if ptype == "new":
            patient_block = (
                f"PATIENT STATUS: NEW patient — slot duration {duration} min. "
                f"Inform the user they are a new patient."
            )
        else:
            patient_block = (
                f"PATIENT STATUS: RETURNING patient — slot duration {duration} min. "
                f"Welcome them back."
            )

    return f"""
{system_base}

---
PRIORITY RULE — READ THIS FIRST:
If the user mentions a doctor name AND asks about availability or a specific time,
answer the availability question FIRST, then ask for their name.
Example: "Dr. Sarah Johnson is available at 12:00 PM today! To book that slot, could I get your full name?"
Do NOT ask for name before answering an availability question.

---
TODAY: {today_str} ({today_weekday})
SUGGESTED DATES IF USER IS VAGUE: {suggested}

ALREADY COLLECTED — NEVER ASK FOR THESE AGAIN:
{collected_block}

STILL NEEDED — ask one at a time:
{missing_block}

AVAILABLE DOCTORS:
{doctors_info}

{patient_block}

{slots_block}

---
{scheduling}

---
{confirmation}

---
Respond ONLY with valid JSON:
{{
    "intent": "general_question|book_appointment|provide_info|confirm|cancel|correct_info",
    "extracted": {{
        "patient_name": null,
        "patient_dob": null,
        "patient_phone": null,
        "patient_email": null,
        "preferred_doctor": null,
        "appointment_date": null,
        "selected_time": null,
        "insurance_carrier": null,
        "insurance_member_id": null,
        "insurance_group_id": null,
        "has_insurance": null
    }},
    "response": "Your warm natural reply to the patient",
    "phase": "greeting|collecting|scheduling|insurance|confirming|done",
    "ready_to_book": false
}}

CRITICAL:
- In "extracted", only put fields the user just provided RIGHT NOW. Everything else null.
- NEVER mention a time slot unless it appears in the AVAILABLE SLOTS section above.
- NEVER re-ask for fields in ALREADY COLLECTED.
""".strip()

def conversation_node(state: dict) -> dict:
    user_input = (state.get("user_input") or "").strip()

    verbose.node_start("conversation_node", user_input)
    verbose.state_summary(state)
    # ─────────────────────────────────────────────────────────────────────────


    llm        = get_llm_client()
    suggested  = ", ".join(_next_weekdays(3))

    # ── 1. Pre-resolve relative dates ────────────────────────────────────────
    if user_input:
        resolved = _resolve_relative_date(user_input)
        if resolved:
            valid, _ = SchedulingValidator.validate_appointment_date(resolved)
            if valid and resolved != state.get("appointment_date"):
                state["appointment_date"] = resolved
                state["selected_time"]    = None
                state["available_slots"]  = []
                logger.info(f"Pre-resolved date changed: '{user_input}' → {resolved}")

# ── 1b. Detect booking for someone else ──────────────────────────────────
    third_person_triggers = [
        "my sister", "my brother", "my mother", "my father",
        "my mom", "my dad", "my wife", "my husband", "my child",
        "my son", "my daughter", "my friend", "my uncle", "my aunt",
        "my grandfather", "my grandmother", "my grandma", "my grandpa"
    ]
    inp_lower = user_input.lower()

    # Check if user is ANSWERING the clarification question
    answering_for_someone = (
        state.get("booking_for_person") and
        not state.get("booking_for_someone_else_confirmed") and
        any(x in inp_lower for x in [
            "for my", "for him", "for her", "for them",
            "brother", "sister", "mother", "father", "mom",
            "dad", "wife", "husband", "child", "son", "daughter",
            "friend", "uncle", "aunt", "grandma", "grandpa"
        ]) and
        len(user_input.split()) < 10  # short answer = responding to question
    )

    if answering_for_someone:
        # Mark confirmed — now collect patient's details
        state["booking_for_someone_else_confirmed"] = True
        person_label = state.get("booking_for_person", "them")
        clarification = (
            f"Perfect! I'll book this for your **{person_label}**. "
            f"Could you please tell me your **{person_label}'s full name**?"
        )
        history = state.get("conversation_context", [])
        history.append({"role": "user", "content": user_input})
        history.append({"role": "assistant", "content": clarification})
        state["conversation_context"] = history[-20:]
        state["response"] = clarification
        # Clear patient name so we collect brother's name next
        state["patient_name"] = None
        return state

    # Check if this is the FIRST mention of someone else
    detected_person = next(
        (t for t in third_person_triggers if t in inp_lower), None
    )
    if detected_person and not state.get("booking_for_person"):
        person_label = detected_person.replace("my ", "")
        state["booking_for_person"] = person_label
        state["booking_for_someone_else_confirmed"] = False
        clarification = (
            f"Got it! Just to confirm — are you booking this appointment "
            f"for yourself or for your **{person_label}**?"
        )
        history = state.get("conversation_context", [])
        history.append({"role": "user", "content": user_input})
        history.append({"role": "assistant", "content": clarification})
        state["conversation_context"] = history[-20:]
        state["response"] = clarification
        return state
    
    # ── 2. Load doctors ───────────────────────────────────────────────────────
    try:
        doctors = tools.schedule_checker.get_doctors()
        doctors_info = "\n".join([
            f"- {d['name']} ({d.get('specialization','General')}) "
            f"at {d.get('location','Main Clinic')} | "
            f"Hours: {d.get('hours','9:00-17:00')}"
            for d in doctors
        ]) or "No doctors available."
        state["available_doctors"] = doctors
    except Exception as e:
        logger.warning(f"Could not load doctors: {e}")
        doctors_info = "Doctor information temporarily unavailable."

    verbose.tool_call("get_doctors", {})
    verbose.tool_result("get_doctors", doctors)

    # ── 2b. Pre-match doctor name BEFORE building prompt ─────────────────────
    _just_matched_doctor = False
    available_docs = state.get("available_doctors", [])

    # Check if input is an exact doctor name — allow change even if already set
    _input_is_exact_doctor = any(
        doc['name'].lower() == user_input.lower() or
        doc['name'] == user_input
        for doc in available_docs
    )

    if user_input and (_input_is_exact_doctor or not state.get("preferred_doctor")):
        for doc in available_docs:
            doc_name = doc['name'].lower()
            inp = user_input.lower()
            # Tighter match: full name in input, or all significant parts match
            significant_parts = [p for p in doc_name.split() if len(p) > 3]
            all_parts_match = all(part in inp for part in significant_parts)
            if doc_name in inp or inp in doc_name or all_parts_match:
                old_doc = state.get("preferred_doctor", "")
                if doc['name'] != old_doc:
                    state["preferred_doctor"] = doc['name']
                    if old_doc:  # switching doctors — reset date too
                        state["appointment_date"] = None
                        state["selected_time"]    = None
                        state["available_slots"]  = []
                    else:  # first time selecting doctor — keep date
                        state["selected_time"]   = None
                        state["available_slots"] = []
                    _just_matched_doctor = True
                    logger.info(f"Doctor changed: {old_doc} → {doc['name']}")
                break
        if _just_matched_doctor:
            verbose.doctor_change("", state.get("preferred_doctor",""))

    # ── 2c. Skip patient name extraction if input is a doctor name ────────────
    _input_is_doctor = any(
        doc['name'].lower() in user_input.lower() or
        user_input.lower() in doc['name'].lower()
        for doc in available_docs
    )
    if _input_is_doctor:
        logger.info(f"Input '{user_input}' is doctor name, skipping patient name extraction")


    # ── 3. Build slots block (only from real availability check) ──────────────
    slots_block = ""
    if state.get("available_slots"):
        slots     = state["available_slots"]
        slot_list = "\n".join([f"  {i}. {s}" for i, s in enumerate(slots, 1)])
        slots_block = (
            f"AVAILABLE SLOTS for {state.get('preferred_doctor','')} "
            f"on {state.get('appointment_date','')}:\n{slot_list}\n"
            f"Patient MUST pick one from this list."
        )
    elif state.get("preferred_doctor") and state.get("appointment_date") and not state.get("selected_time"):
        slots_block = (
            "AVAILABLE SLOTS: Not yet checked. "
            "Do NOT mention any specific times. "
            "Tell the user you will check availability."
        )

    # ── 4. Build system prompt ────────────────────────────────────────────────
    system = _build_system_prompt(state, doctors_info, slots_block)

    # ── 5. Build conversation history ─────────────────────────────────────────
    history = state.get("conversation_context", [])
    history.append({"role": "user", "content": user_input})
    history_str = ""
    for msg in history[-10:]:
        role = "Patient" if msg["role"] == "user" else "MediBook"
        history_str += f"{role}: {msg['content']}\n"

    # Build already-collected summary to reinforce system prompt
    collected_reminder = ", ".join([
        f"{k}={state[k]}" for k in [
            "patient_name","patient_dob","patient_phone","patient_email",
            "preferred_doctor","appointment_date","selected_time","insurance_carrier"
        ] if state.get(k)
    ]) or "nothing yet"

    prompt = (
        f"Conversation so far:\n{history_str}\n"
        f"Patient's latest message: {user_input}\n\n"
        f"REMINDER — already confirmed in state (DO NOT ask for these again): {collected_reminder}\n\n"
        f"Respond as MediBook (JSON only):"
)

    verbose.llm_call(
        Config.get_active_provider(),
        Config.get_active_model(),
        state.get("conversation_phase","greeting")
    )

    # ── 6. Call LLM ───────────────────────────────────────────────────────────
    llm_result = None
    if llm.is_enabled():
        llm_result = llm.chat_json(prompt=prompt, system=system)

    if not llm_result:
        llm_result = _rule_based_fallback(state, user_input)
    
    if llm_result:
        verbose.llm_result(
            llm_result.get("intent",""),
            llm_result.get("extracted",{}),
            llm_result.get("phase","")
        )

    # ── 7. Extract fields ─────────────────────────────────────────────────────
    extracted = llm_result.get("extracted", {})
    _update_state_from_extracted(state, extracted)
    
    # ── 7b. Handle correction intent — user wants to change already given info ──
    correction_phrases = [
        "change my name", "wrong name", "fix my name", "update my name",
        "change my dob", "wrong dob", "fix my email", "change my email",
        "change my phone", "wrong number", "that's wrong", "i made a mistake",
        "correct my", "change my date of birth"
    ]
    if any(phrase in user_input.lower() for phrase in correction_phrases):
        # Figure out which field they want to change
        if any(x in user_input.lower() for x in ["name"]):
            state["patient_name"] = None
            llm_result["response"] = "Of course! What is your correct full name?"
            llm_result["intent"]   = "provide_info"
        elif any(x in user_input.lower() for x in ["dob", "date of birth", "birthday"]):
            state["patient_dob"] = None
            llm_result["response"] = "No problem! What is your correct date of birth?"
            llm_result["intent"]   = "provide_info"
        elif any(x in user_input.lower() for x in ["email"]):
            state["patient_email"] = None
            llm_result["response"] = "Sure! What is your correct email address?"
            llm_result["intent"]   = "provide_info"
        elif any(x in user_input.lower() for x in ["phone", "number"]):
            state["patient_phone"] = None
            llm_result["response"] = "Sure! What is your correct phone number?"
            llm_result["intent"]   = "provide_info"
        elif any(x in user_input.lower() for x in ["doctor"]):
            state["preferred_doctor"] = None
            state["available_slots"]  = []
            state["selected_time"]    = None
            llm_result["response"] = "No problem! Which doctor would you like to see instead?"
            llm_result["intent"]   = "provide_info"
        elif any(x in user_input.lower() for x in ["date", "day", "time", "slot"]):
            state["appointment_date"] = None
            state["available_slots"]  = []
            state["selected_time"]    = None
            llm_result["response"] = "Sure! What date would you prefer?"
            llm_result["intent"]   = "provide_info"
        # Update history and return
        history.append({"role": "assistant", "content": llm_result["response"]})
        state["conversation_context"] = history[-20:]
        state["response"] = llm_result["response"]
        return state

    # ── 7c. Handle cancellation intent ───────────────────────────────────────────
    if llm_result.get("intent") == "cancel":
        # Save whatever we have to DB with cancelled status
        try:
            from database.db import save_appointment
            import uuid
            if not state.get("appointment_id"):
                state["appointment_id"] = f"APT{uuid.uuid4().hex[:6].upper()}"
            state["booking_confirmed"] = False
            state["booking_success"]   = False
            state["status"]            = "cancelled"
            save_appointment(state)
            logger.info(f"Cancelled booking saved: {state['appointment_id']}")
        except Exception as e:
            logger.warning(f"Could not save cancelled booking: {e}")

        state["workflow_complete"]    = True
        state["conversation_phase"]  = "done"
        state["response"] = (
            "I've cancelled your appointment. 🙏\n\n"
            "Your information has been saved for future reference — "
            "you can rebook anytime and we'll have your details ready.\n\n"
            "Is there anything else I can help you with?"
        )
        # Update history and return immediately
        history.append({"role": "assistant", "content": state["response"]})
        state["conversation_context"] = history[-20:]
        return state

    # ── 8. Patient lookup ─────────────────────────────────────────────────────
    if state.get("patient_name") and state.get("patient_dob") and not state.get("patient_id"):
        try:
            lookup = tools.patient_lookup.lookup(
                state["patient_name"], state["patient_dob"]
            )
            state["patient_id"]           = lookup.get("patient_id", "NEW")
            state["patient_type"]         = lookup.get("status", "new")
            state["appointment_duration"] = lookup.get("duration_minutes", 60)
            ptype = state["patient_type"]
            dur   = state["appointment_duration"]
            note  = (
                f"\n\n_(You're a **new patient** — your consultation will be {dur} minutes.)_"
                if ptype == "new"
                else f"\n\n_(Welcome back! Your consultation will be {dur} minutes.)_"
            )
            llm_result["response"] = llm_result.get("response", "") + note
        except Exception as e:
            logger.warning(f"Patient lookup failed: {e}")
            state["patient_id"]           = "NEW"
            state["patient_type"]         = "new"
            state["appointment_duration"] = 60

    # ── 9. Availability check ─────────────────────────────────────────────────
    if (state.get("preferred_doctor") and
            state.get("appointment_date") and
            not state.get("available_slots")):
        try:
            avail = tools.schedule_checker.check_availability(
                state["preferred_doctor"],
                state["appointment_date"],
                state.get("appointment_duration", 60)
            )
            if avail.get("available"):
                    slots = avail.get("slots", [])
                    wh    = avail.get("working_hours", "")
                    state["available_slots"] = slots
                    slot_list = "\n".join([f"{i}. {s}" for i, s in enumerate(slots, 1)])

                    preferred_time = state.get("selected_time") or ""
                    time_match = next((s for s in slots if preferred_time in s or s in preferred_time), None) if preferred_time else None

                    if time_match:
                        # REPLACE LLM response entirely
                        llm_result["response"] = (
                            f"✅ Great news! **{state['preferred_doctor']}** has your preferred time "
                            f"**{time_match}** available on {state['appointment_date']}!\n\n"
                            f"Other available slots (hours: {wh}):\n{slot_list}\n\n"
                            f"Would you like to book {time_match}, or pick a different slot?"
                        )
                        state["selected_time"] = time_match
                    else:
                        if preferred_time:
                            # REPLACE LLM response entirely
                            llm_result["response"] = (
                                f"⚠️ **{preferred_time}** is not available for {state['preferred_doctor']} "
                                f"on {state['appointment_date']}.\n\n"
                                f"⏰ **Available slots** (hours: {wh}):\n{slot_list}\n\n"
                                f"Would you like to book one of these slots instead?"
                            )
                        else:
                            # REPLACE LLM response entirely
                            llm_result["response"] = (
                                f"⏰ **Available slots for {state['preferred_doctor']} "
                                f"on {state['appointment_date']}** (hours: {wh}):\n"
                                f"{slot_list}\n\n"
                                f"Would you like to book one of these slots?"
                            )
            else:
                err = avail.get("error", "No slots available")
                llm_result["response"] += (
                    f"\n\n⚠️ {err} for {state['preferred_doctor']} on {state['appointment_date']}. "
                    f"Would you like to try a different date or another doctor? "
                    f"Suggested dates: {suggested}"
                )
                state["appointment_date"] = None
                state["available_slots"]  = []
        except Exception as e:
            logger.warning(f"Availability check failed: {e}")

    # ── 10. Validate selected_time is a real slot ─────────────────────────────
    if state.get("selected_time") and state.get("available_slots"):
        slots = state["available_slots"]
        sel   = state["selected_time"]
        if sel not in slots:
            matched = next((s for s in slots if sel in s or s in sel), None)
            if matched:
                state["selected_time"] = matched
            else:
                state["selected_time"] = None
                slot_list = "\n".join([f"{i}. {s}" for i, s in enumerate(slots, 1)])
                llm_result["response"] = (
                    f"That time isn't available. Please pick from:\n{slot_list}"
                )

    # ── 11. Phase + booking check ─────────────────────────────────────────────
    # If user is confirming, don't block on selected_time — show slots instead
    confirm_intent = any(
        phrase in user_input.lower() for phrase in [
            "yes", "confirm", "book it", "go ahead", "sure",
            "ya", "yep", "ok", "okay", "please book",
            "can confirm", "u can confirm", "acn confirm"
        ]
    )
    core_fields = [
        "patient_name","patient_dob","patient_phone","patient_email",
        "preferred_doctor","appointment_date","selected_time"
    ]
    # If confirming but no slot yet — trigger availability check first
    if confirm_intent and not state.get("selected_time") and state.get("preferred_doctor") and state.get("appointment_date"):
        state["available_slots"] = []  # force re-fetch
    missing_after = [f for f in core_fields if not state.get(f)]

    carrier = state.get("insurance_carrier", "")
    if carrier and carrier.lower() not in ["none","no insurance","self pay","out of pocket",""]:
        if not state.get("insurance_member_id"):
            missing_after.append("insurance_member_id")
        if not state.get("insurance_group_id"):
            missing_after.append("insurance_group_id")

    all_collected = len(missing_after) == 0

    new_phase = llm_result.get("phase", state.get("conversation_phase","greeting"))
    state["conversation_phase"] = new_phase
    state["intent"]             = llm_result.get("intent","")
    state["missing_fields"]     = missing_after

    # Also detect confirmation from user input directly
    confirm_phrases = [
        "yes", "confirm", "book it", "go ahead", "sure",
        "ya", "yep", "ok", "okay", "please book", "do it",
        "can confirm", "u can confirm", "acn confirm"
    ]
    user_confirming = any(
        phrase in user_input.lower() for phrase in confirm_phrases
    ) and state.get("conversation_phase") in ["confirming", "collecting", "scheduling"]

    if (llm_result.get("ready_to_book") or user_confirming) and all_collected:
        state["booking_confirmed"] = True
        state["current_step"]      = "reminders"
        state["conversation_phase"]= "done"
    elif all_collected and new_phase not in ["confirming","done"]:
        state["conversation_phase"] = "confirming"

    # ── 12. Update history + response ────────────────────────────────────────
    if _just_matched_doctor:
        if state.get("patient_name"):
            override = (
                f"Great choice! You've selected **{state['preferred_doctor']}**. "
                f"What date would you like for your appointment?"
            )
        else:
            override = (
                f"Great choice! You've selected **{state['preferred_doctor']}**. "
                f"Now, could you please tell me your **full name**?"
            )
        state["response"]           = override
        state["conversation_phase"] = "collecting"
        history.append({"role": "assistant", "content": override})
    else:
        state["response"] = llm_result.get("response", "I'm here to help!")
        history.append({"role": "assistant", "content": state["response"]})

    state["conversation_context"] = history[-20:]

    verbose.missing_fields(state.get("missing_fields", []))
    verbose.node_end("conversation_node", state.get("response",""))
    # ─────────────────────────────────────────────────────────────────────────

    return state


def _update_state_from_extracted(state: dict, extracted: dict) -> None:
    if extracted.get("patient_name") and not state.get("patient_name"):
        raw_name = extracted["patient_name"]
        junk_patterns = [
            "ri8", "lol", "haha", "ok", "yes", "no", "already",
            "said", "told", "know", "remember", "right", "correct"
        ]
        is_junk = (
            len(raw_name.strip()) < 2 or
            any(p in raw_name.lower() for p in junk_patterns) or
            not any(c.isalpha() for c in raw_name)
        )
        if not is_junk:
            valid, result = PatientDataValidator.validate_name(raw_name)
            if valid:
                state["patient_name"] = result

    if extracted.get("patient_dob") and not state.get("patient_dob"):
        from datetime import datetime
        raw_dob = extracted["patient_dob"]
        # Try multiple date formats
        dob_formats = [
            "%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y",
            "%d %b %Y", "%dth %b %Y", "%dst %b %Y",
            "%dnd %b %Y", "%drd %b %Y",
            "%B %d, %Y", "%d %B %Y",
            "%dth %B %Y", "%dst %B %Y",
            "%dnd %B %Y", "%drd %B %Y"
        ]
        parsed_dob = None
        # Clean ordinal suffixes
        clean_dob = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', raw_dob, flags=re.IGNORECASE)
        for fmt in dob_formats:
            try:
                parsed_dob = datetime.strptime(clean_dob.strip(), fmt).strftime("%Y-%m-%d")
                break
            except ValueError:
                continue
        if parsed_dob:
            state["patient_dob"] = parsed_dob
            logger.info(f"DOB parsed: '{raw_dob}' → {parsed_dob}")

    if extracted.get("patient_phone") and not state.get("patient_phone"):
        raw_phone = extracted["patient_phone"]
        # Strip all non-digits
        digits_only = re.sub(r'\D', '', raw_phone)
        if len(digits_only) >= 10:
            state["patient_phone"] = digits_only[-10:]  # take last 10 digits
            logger.info(f"Phone stored: {state['patient_phone']}")

    if extracted.get("patient_email") and not state.get("patient_email"):
        valid, result = ContactValidator.validate_email(extracted["patient_email"])
        if valid: state["patient_email"] = result

    if extracted.get("preferred_doctor"):
        new_doc = extracted["preferred_doctor"]
        old_doc = state.get("preferred_doctor", "")
        # Block preference text from being saved as doctor name
        fake_doctor_phrases = [
            "female", "male", "lady", "woman", "man",
            "young", "old", "senior", "specialist",
            "doctor", "physician", "any", "nearest"
        ]
        is_fake = any(p in new_doc.lower() for p in fake_doctor_phrases)
        # Also verify it matches an actual doctor in available_doctors
        available = state.get("available_doctors", [])
        is_real_doctor = any(
            d['name'].lower() == new_doc.lower() or
            new_doc.lower() in d['name'].lower()
            for d in available
        ) if available else True  # if no list yet, allow through

        if not is_fake and is_real_doctor and new_doc != old_doc:
            state["preferred_doctor"] = new_doc
            state["appointment_date"] = None
            state["selected_time"]    = None
            state["available_slots"]  = []
            logger.info(f"Doctor changed: {old_doc} → {new_doc}")

    if extracted.get("appointment_date") and not state.get("appointment_date"):
        valid, _ = SchedulingValidator.validate_appointment_date(extracted["appointment_date"])
        if valid: state["appointment_date"] = extracted["appointment_date"]

    if extracted.get("selected_time") and not state.get("selected_time"):
        available = state.get("available_slots", [])
        if available:
            matched = next((s for s in available if
                        extracted["selected_time"] in s or s in extracted["selected_time"]), None)
            if matched:
                state["selected_time"] = matched

    if extracted.get("insurance_carrier") and not state.get("insurance_carrier"):
        state["insurance_carrier"] = extracted["insurance_carrier"]

    if extracted.get("insurance_member_id") and not state.get("insurance_member_id"):
        state["insurance_member_id"] = extracted["insurance_member_id"]

    if extracted.get("insurance_group_id") and not state.get("insurance_group_id"):
        state["insurance_group_id"] = extracted["insurance_group_id"]

    if extracted.get("has_insurance") is False and not state.get("insurance_carrier"):
        state["insurance_carrier"]   = "None"
        state["insurance_member_id"] = ""
        state["insurance_group_id"]  = ""


def _rule_based_fallback(state: dict, user_input: str) -> dict:
    try:
        from utils.nl_parser import NLParser
        extracted = {}
        name  = NLParser.extract_name(user_input)
        if name:  extracted["patient_name"] = name
        dob   = NLParser.extract_dob(user_input)
        if dob:   extracted["patient_dob"]  = dob
        phone = NLParser.extract_phone(user_input)
        if phone: extracted["patient_phone"] = phone
        email = NLParser.extract_email(user_input)
        if email: extracted["patient_email"] = email
    except Exception:
        extracted = {}

    missing = [f for f in [
        "patient_name","patient_dob","patient_phone",
        "patient_email","preferred_doctor","appointment_date","selected_time"
    ] if not state.get(f)]

    response = (
        f"Could you share your {missing[0].replace('_',' ')}?"
        if missing else
        "I have all your details! Shall I confirm your appointment? (yes/no)"
    )
    return {
        "intent": "provide_info",
        "extracted": extracted,
        "response": response,
        "phase": state.get("conversation_phase","collecting"),
        "ready_to_book": False
    }