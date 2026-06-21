"""
Game state definition.

Provides default state values and the structure used
in Streamlit session state to track game progress.
"""


def get_default_game_state() -> dict:
    """
    Returns a fresh game state dictionary with all default values.
    Used when initialising session state or resetting for a new game.
    """
    return {
        "mystery": None,             # Mystery object (Pydantic model) or None
        "score": 0,                   # Current detective score
        "revealed_clues": set(),      # Set of clue IDs the player has viewed
        "discovered_contradictions": set(),  # Set of contradiction IDs found
        "interrogated_suspects": set(),      # Set of suspect IDs interrogated
        "accusation_made": False,     # Whether accusation has been submitted
        "accused_suspect_id": None,   # Who was accused (suspect ID)
        "case_closed": False,         # Whether the game is over
        "investigation_notes": [],    # List of note strings
        "game_phase": "not_started",  # not_started | generating | investigating | case_closed
        "score_log": [],              # List of (action_description, points) tuples
    }
