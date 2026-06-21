"""
Validator for Gemini-generated mystery JSON.

Performs Pydantic schema validation plus additional
consistency checks to ensure the mystery is playable.
"""

import logging
from models.mystery import Mystery

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when mystery validation fails with a list of errors."""

    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__(f"Validation failed with {len(errors)} error(s): {'; '.join(errors)}")


def validate_mystery(data: dict) -> Mystery:
    """
    Validate a raw dictionary against the Mystery schema.

    Performs:
    1. Pydantic model parsing (type checks, field presence)
    2. Consistency checks (ID references, murderer validity, etc.)

    Args:
        data: Raw dictionary parsed from Gemini's JSON response.

    Returns:
        A validated Mystery instance.

    Raises:
        ValidationError: If any validation checks fail.
    """
    errors: list[str] = []

    # --- Step 1: Pydantic parsing ---
    try:
        mystery = Mystery.model_validate(data)
    except Exception as e:
        error_messages = []
        if hasattr(e, "errors"):
            for err in e.errors():
                loc = " -> ".join(str(x) for x in err.get("loc", []))
                msg = err.get("msg", str(err))
                error_messages.append(f"[{loc}] {msg}")
        else:
            error_messages.append(str(e))
        raise ValidationError(error_messages) from e

    # --- Step 2: Consistency checks ---
    suspect_ids = {s.id for s in mystery.suspects}
    clue_ids = {c.id for c in mystery.clues}

    # Check suspect count
    if len(mystery.suspects) != 3:
        errors.append(
            f"Expected exactly 3 suspects, got {len(mystery.suspects)}"
        )

    # Check for duplicate suspect IDs
    if len(suspect_ids) != len(mystery.suspects):
        errors.append("Duplicate suspect IDs detected")

    # Check for duplicate clue IDs
    if len(clue_ids) != len(mystery.clues):
        errors.append("Duplicate clue IDs detected")

    # Check murderer_id references a valid suspect
    if mystery.murderer_id not in suspect_ids:
        errors.append(
            f"murderer_id '{mystery.murderer_id}' does not match any suspect ID. "
            f"Valid IDs: {suspect_ids}"
        )

    # Check that exactly one suspect is marked as murderer
    murderers = [s for s in mystery.suspects if s.is_murderer]
    if len(murderers) == 0:
        errors.append("No suspect has is_murderer=true")
    elif len(murderers) > 1:
        errors.append(
            f"Multiple suspects marked as murderer: "
            f"{[s.id for s in murderers]}"
        )

    # Check murderer flag matches murderer_id
    if len(murderers) == 1 and murderers[0].id != mystery.murderer_id:
        errors.append(
            f"Suspect with is_murderer=true ({murderers[0].id}) "
            f"does not match murderer_id ({mystery.murderer_id})"
        )

    # Check contradiction references
    for contradiction in mystery.contradictions:
        # Clue IDs must exist
        for clue_id in contradiction.clue_ids:
            if clue_id not in clue_ids:
                errors.append(
                    f"Contradiction '{contradiction.id}' references "
                    f"non-existent clue '{clue_id}'"
                )

        # Suspect ID must exist
        if contradiction.suspect_id not in suspect_ids:
            errors.append(
                f"Contradiction '{contradiction.id}' references "
                f"non-existent suspect '{contradiction.suspect_id}'"
            )

    # Check clue related_suspect_id references
    for clue in mystery.clues:
        if clue.related_suspect_id and clue.related_suspect_id not in suspect_ids:
            errors.append(
                f"Clue '{clue.id}' references non-existent suspect "
                f"'{clue.related_suspect_id}'"
            )

    # Check we have at least some clues and contradictions
    if len(mystery.clues) == 0:
        errors.append("No clues generated")

    if len(mystery.contradictions) == 0:
        errors.append("No contradictions generated")

    # If any errors, raise
    if errors:
        logger.warning("Mystery validation failed: %s", errors)
        raise ValidationError(errors)

    logger.info("Mystery validated successfully")
    return mystery
