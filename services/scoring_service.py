"""
Scoring service for the detective game.

Handles point calculations, duplicate-score prevention,
and detective rank assignment.
"""

POINTS_CLUE = 5
POINTS_INTERROGATION = 5
POINTS_CONTRADICTION = 20
POINTS_CORRECT_ACCUSATION = 100
POINTS_WRONG_ACCUSATION = -50

RANKS = [
    (190, "🏆 Master Detective"),
    (150, "⭐ Senior Detective"),
    (100, "🕵️‍♂️ Detective"),
    (50, "🕵️ Junior Detective"),
    (0, "🔰 Rookie"),
]


def get_rank(score: int) -> str:
    """
    Return the detective rank for a given score.

    Args:
        score: The player's current score.

    Returns:
        A string with the rank emoji and title.
    """
    for threshold, rank in RANKS:
        if score >= threshold:
            return rank
    return "🔰 Rookie"


def calculate_max_score(num_clues: int, num_suspects: int, num_contradictions: int) -> int:
    """
    Calculate the maximum possible score for a given mystery.

    Args:
        num_clues: Number of clues in the mystery.
        num_suspects: Number of suspects.
        num_contradictions: Number of contradictions.

    Returns:
        Maximum achievable score.
    """
    return (
        (num_clues * POINTS_CLUE)
        + (num_suspects * POINTS_INTERROGATION)
        + (num_contradictions * POINTS_CONTRADICTION)
        + POINTS_CORRECT_ACCUSATION
    )
