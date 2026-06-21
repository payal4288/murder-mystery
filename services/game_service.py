"""
Game service — orchestrates game flow.

Coordinates between Gemini AI, session state, validation,
and scoring to manage the full lifecycle of a case.
"""

import logging

from services.gemini_service import generate_mystery, generate_mock_mystery, GeminiServiceError
from services.scoring_service import (
    POINTS_CLUE,
    POINTS_INTERROGATION,
    POINTS_CONTRADICTION,
    POINTS_CORRECT_ACCUSATION,
    POINTS_WRONG_ACCUSATION,
)
from utils import session_manager as sm

logger = logging.getLogger(__name__)


def start_new_case(theme: str | None = None, use_offline: bool = False) -> str | None:
    """
    Generate a new mystery case and initialise game state.

    Args:
        theme: Optional custom theme or setting string.
        use_offline: Whether to bypass Gemini and use a pre-written local mystery.

    Returns:
        None on success, or an error message string on failure.
    """
    import streamlit as st
    sm.reset_session()
    sm.set_phase("generating")

    # Save user preference in session state
    st.session_state.use_offline_preference = use_offline

    try:
        if use_offline:
            mystery = generate_mock_mystery(theme)
            st.session_state.is_offline_mode = True
        else:
            try:
                mystery = generate_mystery(theme)
                st.session_state.is_offline_mode = False
            except Exception as e:
                logger.warning("Failed to generate case using Gemini AI. Falling back to offline mode. Error: %s", e)
                mystery = generate_mock_mystery(theme)
                st.session_state.is_offline_mode = True

        sm.set_mystery(mystery)
        sm.add_note("📋 Case file opened. Investigation begins.")
        if st.session_state.get("is_offline_mode", False):
            sm.add_note("⚠️ Running in Offline Mode (local case loaded due to API settings or rate limits).")

        logger.info("New case started: victim=%s, scene=%s, offline=%s",
                    mystery.victim_name, mystery.crime_scene, st.session_state.get("is_offline_mode", False))
        return None  # Success
    except Exception as e:
        sm.set_phase("not_started")
        logger.error("Unexpected error starting case: %s", e)
        return "Something went wrong generating your case. Please try again."


def reveal_clue(clue_id: str) -> None:
    """
    Reveal a clue and award points if it's the first time.

    Args:
        clue_id: The unique ID of the clue to reveal.
    """
    is_new = sm.reveal_clue(clue_id)
    if is_new:
        sm.add_score(POINTS_CLUE, f"Examined clue: {clue_id}")

        # Find the clue title for the note
        mystery = sm.get_mystery()
        if mystery:
            clue = next((c for c in mystery.clues if c.id == clue_id), None)
            if clue:
                sm.add_note(f"🔍 Examined evidence: {clue.title}")


def interrogate_suspect(suspect_id: str) -> None:
    """
    Interrogate a suspect and award points if first time.

    Args:
        suspect_id: The unique ID of the suspect.
    """
    is_new = sm.interrogate_suspect(suspect_id)
    if is_new:
        sm.add_score(POINTS_INTERROGATION, f"Interrogated: {suspect_id}")

        mystery = sm.get_mystery()
        if mystery:
            suspect = next((s for s in mystery.suspects if s.id == suspect_id), None)
            if suspect:
                sm.add_note(f"🗣️ Interrogated {suspect.name} — noted their alibi.")


def check_contradictions() -> list[str]:
    """
    Check if any undiscovered contradictions can be found
    based on the clues that have been revealed.

    A contradiction is discoverable when ALL of its referenced
    clue_ids have been revealed by the player.

    Returns:
        List of newly discovered contradiction IDs.
    """
    state = sm.get_state()
    mystery = state["mystery"]
    if mystery is None:
        return []

    revealed = state["revealed_clues"]
    already_found = state["discovered_contradictions"]
    newly_found = []

    for contradiction in mystery.contradictions:
        if contradiction.id in already_found:
            continue

        # Check if all required clues have been revealed
        required_clues = set(contradiction.clue_ids)
        if required_clues.issubset(revealed):
            is_new = sm.discover_contradiction(contradiction.id)
            if is_new:
                sm.add_score(POINTS_CONTRADICTION, f"Found contradiction: {contradiction.id}")
                sm.add_note(f"⚡ Contradiction discovered: {contradiction.description}")
                newly_found.append(contradiction.id)

    return newly_found


def submit_accusation(suspect_id: str) -> bool:
    """
    Submit the player's accusation and evaluate it.

    Args:
        suspect_id: The ID of the suspect being accused.

    Returns:
        True if the accusation was correct, False otherwise.
    """
    mystery = sm.get_mystery()
    if mystery is None:
        return False

    sm.submit_accusation(suspect_id)
    is_correct = suspect_id == mystery.murderer_id

    if is_correct:
        sm.add_score(POINTS_CORRECT_ACCUSATION, "Correct accusation!")
        sm.add_note("✅ Correct! You identified the murderer!")
    else:
        sm.add_score(POINTS_WRONG_ACCUSATION, "Wrong accusation")
        # Find who the player accused
        accused = next((s for s in mystery.suspects if s.id == suspect_id), None)
        murderer = next((s for s in mystery.suspects if s.id == mystery.murderer_id), None)
        accused_name = accused.name if accused else "Unknown"
        murderer_name = murderer.name if murderer else "Unknown"
        sm.add_note(
            f"❌ Wrong! You accused {accused_name}, "
            f"but the murderer was {murderer_name}."
        )

    return is_correct
