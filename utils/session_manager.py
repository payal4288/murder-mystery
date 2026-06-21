"""
Session state manager for Streamlit.

All mutations to st.session_state go through this module,
keeping state management centralised and predictable.
"""

import streamlit as st
from models.game_state import get_default_game_state


def init_session() -> None:
    """
    Initialise session state with defaults if not already set.
    Call this at the top of app.py on every rerun.
    """
    if "game_state" not in st.session_state:
        st.session_state.game_state = get_default_game_state()
    if "is_offline_mode" not in st.session_state:
        st.session_state.is_offline_mode = False
    if "use_offline_preference" not in st.session_state:
        st.session_state.use_offline_preference = False


def reset_session() -> None:
    """Reset all game state for a new game."""
    st.session_state.game_state = get_default_game_state()


def get_state() -> dict:
    """Get the current game state dictionary."""
    return st.session_state.game_state


def set_mystery(mystery) -> None:
    """
    Store a validated Mystery object and transition to investigating phase.

    Args:
        mystery: A validated Mystery Pydantic model instance.
    """
    state = get_state()
    state["mystery"] = mystery
    state["game_phase"] = "investigating"


def set_phase(phase: str) -> None:
    """
    Set the current game phase.

    Args:
        phase: One of 'not_started', 'generating', 'investigating', 'case_closed'.
    """
    get_state()["game_phase"] = phase


def get_phase() -> str:
    """Get the current game phase string."""
    return get_state()["game_phase"]


def get_mystery():
    """Get the current Mystery object, or None."""
    return get_state()["mystery"]


def get_score() -> int:
    """Get the current score."""
    return get_state()["score"]


def add_score(points: int, description: str) -> None:
    """
    Add points to the score and log the action.

    Args:
        points: Number of points (can be negative).
        description: Human-readable description of why points were awarded.
    """
    state = get_state()
    state["score"] += points
    state["score_log"].append((description, points))


def reveal_clue(clue_id: str) -> bool:
    """
    Mark a clue as revealed.

    Args:
        clue_id: The clue's unique ID.

    Returns:
        True if this was a new reveal (first time), False if already revealed.
    """
    state = get_state()
    if clue_id not in state["revealed_clues"]:
        state["revealed_clues"].add(clue_id)
        return True
    return False


def interrogate_suspect(suspect_id: str) -> bool:
    """
    Mark a suspect as interrogated.

    Args:
        suspect_id: The suspect's unique ID.

    Returns:
        True if this was the first interrogation, False if already done.
    """
    state = get_state()
    if suspect_id not in state["interrogated_suspects"]:
        state["interrogated_suspects"].add(suspect_id)
        return True
    return False


def discover_contradiction(contradiction_id: str) -> bool:
    """
    Mark a contradiction as discovered.

    Args:
        contradiction_id: The contradiction's unique ID.

    Returns:
        True if this was a new discovery, False if already found.
    """
    state = get_state()
    if contradiction_id not in state["discovered_contradictions"]:
        state["discovered_contradictions"].add(contradiction_id)
        return True
    return False


def submit_accusation(suspect_id: str) -> None:
    """
    Record the player's accusation.

    Args:
        suspect_id: The ID of the suspect being accused.
    """
    state = get_state()
    state["accusation_made"] = True
    state["accused_suspect_id"] = suspect_id
    state["case_closed"] = True
    state["game_phase"] = "case_closed"


def add_note(note: str) -> None:
    """Append an investigation note."""
    get_state()["investigation_notes"].append(note)


def get_progress() -> float:
    """
    Calculate investigation progress as a float between 0.0 and 1.0.

    Progress is based on:
    - Clues revealed vs total
    - Contradictions found vs total
    - Suspects interrogated vs total
    """
    state = get_state()
    mystery = state["mystery"]
    if mystery is None:
        return 0.0

    total_items = (
        len(mystery.clues)
        + len(mystery.contradictions)
        + len(mystery.suspects)
    )
    found_items = (
        len(state["revealed_clues"])
        + len(state["discovered_contradictions"])
        + len(state["interrogated_suspects"])
    )

    if total_items == 0:
        return 0.0

    return min(found_items / total_items, 1.0)
