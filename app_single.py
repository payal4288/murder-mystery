"""
🔍 Murder Mystery Detective — AI-Powered Investigation Game

Self-contained single-file Streamlit application.
Contains all data models, prompt templates, validation logic, AI/offline services,
scoring, session management, custom CSS styles, and UI components.
"""

import streamlit as st
import os
import logging
import json
import random
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration — must be first Streamlit call
st.set_page_config(
    page_title="🔍 Murder Mystery Detective",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════════════════════
#  CUSTOM CSS STYLE SHEET
# ═══════════════════════════════════════════════════════════════
CUSTOM_CSS = """
/* ===== Murder Mystery Detective — Custom CSS ===== */

/* Google Font import */
@import url('https://fonts.googleapis.com/css2?family=Special+Elite&family=Inter:wght@300;400;500;600;700&display=swap');

/* ===== Root Variables ===== */
:root {
    --crimson: #E63946;
    --crimson-dark: #C62828;
    --crimson-glow: rgba(230, 57, 70, 0.3);
    --navy: #1A1A2E;
    --navy-light: #16213E;
    --navy-lighter: #1F2B47;
    --gold: #F0C040;
    --gold-dim: rgba(240, 192, 64, 0.2);
    --text-primary: #E0E0E0;
    --text-muted: #8899AA;
    --success: #2ECC71;
    --danger: #E74C3C;
    --card-border: rgba(230, 57, 70, 0.2);
    --card-bg: rgba(22, 33, 62, 0.7);
    --font-display: 'Special Elite', cursive;
    --font-body: 'Inter', sans-serif;
}

/* ===== Global ===== */
.main .block-container {
    padding-top: 2rem;
    max-width: 1100px;
}

h1, h2, h3 {
    font-family: var(--font-display) !important;
    letter-spacing: 0.5px;
}

/* ===== Welcome Screen ===== */
.welcome-container {
    text-align: center;
    padding: 4rem 2rem;
    animation: fadeInUp 0.8s ease-out;
}

.welcome-container h1 {
    font-size: 3rem;
    color: var(--crimson);
    text-shadow: 0 0 30px var(--crimson-glow);
    margin-bottom: 0.5rem;
}

.welcome-container .subtitle {
    font-family: var(--font-body);
    color: var(--text-muted);
    font-size: 1.1rem;
    margin-bottom: 2rem;
}

/* ===== Case File Header ===== */
.case-header {
    background: linear-gradient(135deg, var(--navy-light), var(--navy-lighter));
    border: 1px solid var(--card-border);
    border-left: 4px solid var(--crimson);
    border-radius: 8px;
    padding: 1.5rem 2rem;
    margin-bottom: 1.5rem;
    animation: fadeInUp 0.6s ease-out;
}

.case-header h2 {
    color: var(--crimson);
    margin-bottom: 0.5rem;
    font-size: 1.5rem;
}

.case-header p {
    color: var(--text-primary);
    line-height: 1.7;
    font-family: var(--font-body);
}

/* ===== Suspect Cards ===== */
.suspect-card {
    background: linear-gradient(145deg, var(--navy-light), rgba(31, 43, 71, 0.6));
    border: 1px solid var(--card-border);
    border-radius: 12px;
    padding: 1.5rem;
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
    min-height: 280px;
}

.suspect-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, var(--crimson), transparent);
}

.suspect-card:hover {
    border-color: var(--crimson);
    box-shadow: 0 4px 20px var(--crimson-glow);
    transform: translateY(-2px);
}

.suspect-card .suspect-name {
    font-family: var(--font-display);
    font-size: 1.3rem;
    color: var(--crimson);
    margin-bottom: 0.3rem;
}

.suspect-card .suspect-occupation {
    font-family: var(--font-body);
    color: var(--gold);
    font-size: 0.85rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 0.8rem;
}

.suspect-card .suspect-detail {
    font-family: var(--font-body);
    color: var(--text-muted);
    font-size: 0.9rem;
    line-height: 1.5;
    margin-bottom: 0.5rem;
}

.suspect-card .suspect-detail strong {
    color: var(--text-primary);
}

/* ===== Clue Cards ===== */
.clue-card {
    background: var(--card-bg);
    border: 1px solid rgba(240, 192, 64, 0.15);
    border-radius: 8px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.8rem;
    transition: all 0.3s ease;
    cursor: pointer;
}

.clue-card:hover {
    border-color: var(--gold);
    box-shadow: 0 2px 12px var(--gold-dim);
}

.clue-card .clue-title {
    font-family: var(--font-display);
    color: var(--gold);
    font-size: 1.05rem;
    margin-bottom: 0.3rem;
}

.clue-card .clue-type {
    font-family: var(--font-body);
    color: var(--text-muted);
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-bottom: 0.5rem;
}

.clue-card .clue-desc {
    font-family: var(--font-body);
    color: var(--text-primary);
    font-size: 0.9rem;
    line-height: 1.6;
}

/* ===== Contradiction Alert ===== */
.contradiction-found {
    background: linear-gradient(135deg, rgba(230, 57, 70, 0.1), rgba(230, 57, 70, 0.05));
    border: 1px solid var(--crimson);
    border-radius: 8px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.8rem;
    animation: pulseGlow 2s ease-in-out infinite;
}

.contradiction-found .contradiction-title {
    color: var(--crimson);
    font-family: var(--font-display);
    font-size: 1rem;
    margin-bottom: 0.3rem;
}

.contradiction-found .contradiction-desc {
    color: var(--text-primary);
    font-family: var(--font-body);
    font-size: 0.88rem;
    line-height: 1.5;
}

/* ===== Score Display ===== */
.score-badge {
    background: linear-gradient(135deg, var(--gold-dim), transparent);
    border: 1px solid rgba(240, 192, 64, 0.3);
    border-radius: 8px;
    padding: 0.8rem 1rem;
    text-align: center;
}

.score-badge .score-value {
    font-family: var(--font-display);
    font-size: 2rem;
    color: var(--gold);
}

.score-badge .score-label {
    font-family: var(--font-body);
    color: var(--text-muted);
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 1px;
}

/* ===== Case Closed Screen ===== */
.case-closed-banner {
    text-align: center;
    padding: 2rem;
    margin-bottom: 1.5rem;
    border-radius: 12px;
    animation: fadeInUp 0.8s ease-out;
}

.case-closed-banner.correct {
    background: linear-gradient(135deg, rgba(46, 204, 113, 0.15), rgba(46, 204, 113, 0.05));
    border: 2px solid var(--success);
}

.case-closed-banner.wrong {
    background: linear-gradient(135deg, rgba(231, 76, 60, 0.15), rgba(231, 76, 60, 0.05));
    border: 2px solid var(--danger);
}

.case-closed-banner h2 {
    font-size: 2rem;
    margin-bottom: 0.5rem;
}

/* ===== Section Divider ===== */
.section-divider {
    border: none;
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--card-border), transparent);
    margin: 2rem 0;
}

/* ===== Sidebar Enhancements ===== */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0F1123, #16213E) !important;
}

section[data-testid="stSidebar"] .stMarkdown h1 {
    font-family: var(--font-display) !important;
    color: var(--crimson) !important;
    font-size: 1.4rem !important;
    text-align: center;
    text-shadow: 0 0 20px var(--crimson-glow);
}

/* ===== Animations ===== */
@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes pulseGlow {
    0%, 100% {
        box-shadow: 0 0 5px var(--crimson-glow);
    }
    50% {
        box-shadow: 0 0 20px var(--crimson-glow);
    }
}

@keyframes typewriter {
    from { width: 0; }
    to { width: 100%; }
}

/* ===== Button Overrides ===== */
.stButton > button {
    font-family: var(--font-body) !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    transition: all 0.3s ease !important;
    letter-spacing: 0.5px !important;
}

.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 15px var(--crimson-glow) !important;
}

/* ===== Expander Overrides ===== */
.streamlit-expanderHeader {
    font-family: var(--font-display) !important;
    font-size: 1rem !important;
}

/* ===== Progress Bar ===== */
.stProgress > div > div > div {
    background: linear-gradient(90deg, var(--crimson), var(--gold)) !important;
}

/* ===== Metric Override ===== */
div[data-testid="stMetric"] {
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 8px;
    padding: 0.8rem 1rem;
}

div[data-testid="stMetric"] label {
    font-family: var(--font-body) !important;
    color: var(--text-muted) !important;
}

div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
    font-family: var(--font-display) !important;
    color: var(--gold) !important;
}
"""
st.markdown(f"<style>{CUSTOM_CSS}</style>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
#  DATA MODELS (from models/mystery.py & models/game_state.py)
# ═══════════════════════════════════════════════════════════════

class Suspect(BaseModel):
    """Represents a suspect in the murder mystery."""
    id: str = Field(..., description="Unique identifier, e.g. 'suspect_1'")
    name: str = Field(..., description="Full name of the suspect")
    occupation: str = Field(..., description="Job title or role")
    relationship: str = Field(..., description="Relationship to the victim")
    motive: str = Field(..., description="Why they might have committed the crime")
    alibi: str = Field(..., description="Their claimed whereabouts at time of crime")
    is_murderer: bool = Field(
        default=False,
        description="True only for the guilty party"
    )


class Clue(BaseModel):
    """Represents a piece of evidence in the investigation."""
    id: str = Field(..., description="Unique identifier, e.g. 'clue_1'")
    title: str = Field(..., description="Short label for the clue")
    description: str = Field(..., description="Detailed narrative description")
    type: str = Field(
        ...,
        description="Category: fingerprint, witness, footage, document, physical, digital"
    )
    related_suspect_id: Optional[str] = Field(
        default=None,
        description="Links clue to a suspect if applicable"
    )

    @field_validator("type")
    @classmethod
    def validate_clue_type(cls, v: str) -> str:
        allowed = {
            "fingerprint", "witness", "footage", "document",
            "physical", "digital", "testimonial", "forensic",
            "receipt", "phone_record", "other"
        }
        # Be lenient — normalise and accept if close enough
        normalised = v.lower().strip().replace(" ", "_")
        if normalised not in allowed:
            return "other"
        return normalised


class Contradiction(BaseModel):
    """Represents a hidden contradiction between alibis, clues, or statements."""
    id: str = Field(..., description="Unique identifier")
    description: str = Field(..., description="What the contradiction is")
    clue_ids: list[str] = Field(
        ...,
        description="Which clues are involved in this contradiction"
    )
    suspect_id: str = Field(
        ...,
        description="Which suspect's story is undermined"
    )
    hint: str = Field(
        ...,
        description="A subtle hint to help the player find it"
    )


class Mystery(BaseModel):
    """
    Complete murder mystery case generated by Gemini AI.
    This is the top-level model validated against the AI response.
    """
    victim_name: str = Field(..., description="Name of the victim")
    victim_occupation: str = Field(..., description="Victim's profession")
    victim_backstory: str = Field(..., description="2-3 sentence backstory")
    crime_scene: str = Field(..., description="Location name")
    crime_scene_description: str = Field(
        ...,
        description="Atmospheric description of the scene"
    )
    time_of_death: str = Field(..., description="Approximate time of death")
    cause_of_death: str = Field(..., description="How the victim died")
    initial_report: str = Field(
        ...,
        description="Opening narrative the detective reads"
    )
    suspects: list[Suspect] = Field(
        ...,
        description="Exactly 3 suspects"
    )
    clues: list[Clue] = Field(
        ...,
        description="5-8 investigation clues"
    )
    contradictions: list[Contradiction] = Field(
        ...,
        description="2-4 hidden contradictions"
    )
    murderer_id: str = Field(
        ...,
        description="ID of the guilty suspect"
    )
    solution_narrative: str = Field(
        ...,
        description="Full explanation of how and why the murder happened"
    )

    @field_validator("suspects")
    @classmethod
    def validate_suspect_count(cls, v: list[Suspect]) -> list[Suspect]:
        if len(v) < 2:
            raise ValueError(f"Need at least 2 suspects, got {len(v)}")
        if len(v) > 6:
            raise ValueError(f"Too many suspects ({len(v)}), max is 6")
        return v

    @field_validator("clues")
    @classmethod
    def validate_clue_count(cls, v: list[Clue]) -> list[Clue]:
        if len(v) < 1:
            raise ValueError("Must have at least 1 clue")
        return v

    @field_validator("contradictions")
    @classmethod
    def validate_contradiction_count(cls, v: list[Contradiction]) -> list[Contradiction]:
        if len(v) < 1:
            raise ValueError("Must have at least 1 contradiction")
        return v


def get_default_game_state() -> dict:
    """Returns a fresh game state dictionary with all default values."""
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


# ═══════════════════════════════════════════════════════════════
#  VALIDATION LOGIC (from utils/validator.py)
# ═══════════════════════════════════════════════════════════════

class ValidationError(Exception):
    """Raised when mystery validation fails with a list of errors."""
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__(f"Validation failed with {len(errors)} error(s): {'; '.join(errors)}")


def validate_mystery(data: dict) -> Mystery:
    """
    Validate a raw dictionary against the Mystery schema.
    Performs Pydantic model parsing and consistency checks.
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
        errors.append(f"Expected exactly 3 suspects, got {len(mystery.suspects)}")

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
        errors.append(f"Multiple suspects marked as murderer: {[s.id for s in murderers]}")

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


# ═══════════════════════════════════════════════════════════════
#  PROMPT TEMPLATES (from prompts/mystery_prompts.py)
# ═══════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """You are a world-class murder mystery author and game designer. 
Your job is to create a self-contained, immersive murder mystery case for a detective game.

RULES:
1. Return ONLY valid JSON matching the schema provided — no markdown, no code fences, no extra text.
2. Generate exactly 3 suspects. One of them MUST be the murderer.
3. The murderer's alibi must contain a subtle flaw that can be discovered through the clues.
4. Generate between 5 and 8 clues of mixed types (physical, digital, testimonial, forensic, etc.).
5. Generate between 2 and 4 contradictions. Each contradiction must reference specific clue IDs and a suspect ID.
6. All IDs must be consistent: suspect_1, suspect_2, suspect_3 for suspects; clue_1, clue_2, ... for clues; contradiction_1, contradiction_2, ... for contradictions.
7. The murderer_id must match one of the suspect IDs, and that suspect's is_murderer field must be true. All other suspects must have is_murderer as false.
8. The solution_narrative must explain the full chain of evidence leading to the murderer.
9. Keep the tone atmospheric and engaging — PG-13 detective fiction. No graphic violence.
10. Every alibi, clue, and contradiction must be internally consistent with each other.
11. Create diverse, creative cases — avoid repeating common tropes."""

GENERATION_PROMPT = """Generate a complete, unique murder mystery case. Return ONLY valid JSON.

JSON SCHEMA:
{
  "victim_name": "string (full name)",
  "victim_occupation": "string (profession like Businessman, Professor, Artist, Journalist, Doctor, etc.)",
  "victim_backstory": "string (2-3 sentences about the victim's life)",
  "crime_scene": "string (location name like Ravenwood Manor, Grand Continental Hotel, etc.)",
  "crime_scene_description": "string (atmospheric 3-4 sentence description of the scene)",
  "time_of_death": "string (approximate time, e.g. 'Between 10:30 PM and 11:15 PM')",
  "cause_of_death": "string (how the victim died)",
  "initial_report": "string (opening narrative paragraph — what the detective sees when arriving, 4-5 sentences)",
  "suspects": [
    {
      "id": "suspect_1",
      "name": "string (full name)",
      "occupation": "string",
      "relationship": "string (relationship to victim)",
      "motive": "string (2-3 sentences explaining their motive)",
      "alibi": "string (3-4 sentences — their claimed whereabouts. The MURDERER's alibi must have a subtle flaw.)",
      "is_murderer": false
    }
  ],
  "clues": [
    {
      "id": "clue_1",
      "title": "string (short label like 'Broken Window Latch')",
      "description": "string (2-3 sentence detailed description of the clue and what it suggests)",
      "type": "string (one of: fingerprint, witness, footage, document, physical, digital, testimonial, forensic)",
      "related_suspect_id": "string or null (suspect ID this clue relates to, if any)"
    }
  ],
  "contradictions": [
    {
      "id": "contradiction_1",
      "description": "string (2-3 sentences explaining the contradiction)",
      "clue_ids": ["clue_X", "clue_Y"],
      "suspect_id": "suspect_X",
      "hint": "string (a subtle 1-sentence hint for the player)"
    }
  ],
  "murderer_id": "suspect_X",
  "solution_narrative": "string (4-6 sentence detailed explanation of the crime — motive, method, how the evidence points to the murderer)"
}

IMPORTANT:
- Generate EXACTLY 3 suspects (suspect_1, suspect_2, suspect_3)
- Generate 5-8 clues (clue_1 through clue_N)  
- Generate 2-4 contradictions (contradiction_1 through contradiction_N)
- Include at least one red herring clue pointing to an innocent suspect
- Make sure contradictions reference valid clue IDs and suspect IDs from your generated data
- The murderer's is_murderer must be true; all others must be false

THEME SEED: {theme_seed}

Generate the mystery now. Return ONLY the JSON object."""

RETRY_PROMPT = """Your previous response had validation errors. Please fix them and return corrected JSON.

ERRORS FOUND:
{errors}

PREVIOUS RESPONSE:
{previous_response}

Fix ALL the listed errors and return the complete, corrected JSON object. Return ONLY valid JSON — no markdown, no explanation."""


# ═══════════════════════════════════════════════════════════════
#  AI SERVICE & MOCK DATA (from services/gemini_service.py)
# ═══════════════════════════════════════════════════════════════

THEME_SEEDS = [
    "art forgery", "family inheritance", "corporate espionage",
    "academic rivalry", "hidden affair", "stolen jewels",
    "political scandal", "blackmail scheme", "poisoned cocktail",
    "disappeared manuscript", "revenge plot", "underground auction",
    "music industry betrayal", "archaeological discovery",
    "theatre production sabotage", "culinary competition",
    "luxury yacht gathering", "charity gala deception",
    "tech startup fraud", "vintage wine collection",
]

MAX_RETRIES = 2


class GeminiServiceError(Exception):
    """Raised when Gemini service encounters an unrecoverable error."""
    pass


def _get_client() -> genai.Client:
    """Load the API key and create a Gemini client."""
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key or api_key == "your_gemini_api_key_here":
        raise GeminiServiceError(
            "GEMINI_API_KEY is not set. Please add your API key to the .env file."
        )

    return genai.Client(api_key=api_key)


def _extract_json(text: str) -> dict:
    """Extract a JSON object from Gemini's response text."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        first_newline = cleaned.index("\n")
        cleaned = cleaned[first_newline + 1:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise GeminiServiceError(f"Failed to parse JSON from Gemini response: {e}") from e


def generate_mystery(theme: str | None = None) -> Mystery:
    """Generate a complete mystery using Gemini AI."""
    try:
        client = _get_client()
    except GeminiServiceError:
        raise
    except Exception as e:
        raise GeminiServiceError(f"Failed to configure Gemini client: {e}") from e

    # Pick a random theme seed for diversity if not provided
    if not theme:
        theme = random.choice(THEME_SEEDS)
    prompt = GENERATION_PROMPT.replace("{theme_seed}", theme)

    logger.info("Generating mystery with theme: %s", theme)

    previous_response = None
    last_errors = None

    for attempt in range(1 + MAX_RETRIES):
        try:
            if attempt == 0:
                current_prompt = prompt
            else:
                logger.info("Retry attempt %d/%d", attempt, MAX_RETRIES)
                current_prompt = RETRY_PROMPT.format(
                    errors="\n".join(f"- {e}" for e in last_errors),
                    previous_response=previous_response or "N/A",
                )

            response = client.models.generate_content(
                model="gemini-flash-latest",
                contents=current_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.9,
                    max_output_tokens=8192,
                    response_mime_type="application/json",
                    response_schema=Mystery,
                ),
            )

            raw_text = response.text
            previous_response = raw_text

            # Parse JSON
            data = _extract_json(raw_text)

            # Validate
            mystery = validate_mystery(data)
            logger.info("Mystery generated successfully on attempt %d", attempt + 1)
            return mystery

        except ValidationError as e:
            last_errors = e.errors
            logger.warning(
                "Validation failed on attempt %d: %s",
                attempt + 1,
                e.errors,
            )
            continue

        except GeminiServiceError as e:
            err_msg = str(e)
            if "rate limit" in err_msg or "taking too long" in err_msg or "not set" in err_msg:
                raise
            
            last_errors = [err_msg]
            logger.warning(
                "Gemini service error on attempt %d: %s",
                attempt + 1,
                err_msg,
            )
            continue

        except Exception as e:
            error_msg = str(e)
            if "ResourceExhausted" in error_msg or "429" in error_msg:
                raise GeminiServiceError(
                    "API rate limit reached. Please wait a moment and try again."
                ) from e
            elif "DeadlineExceeded" in error_msg or "timeout" in error_msg.lower():
                raise GeminiServiceError(
                    "The AI server is taking too long. Please try again."
                ) from e
            else:
                last_errors = [f"Unexpected error: {error_msg}"]
                logger.warning(
                    "Attempt %d failed with unexpected exception: %s",
                    attempt + 1,
                    error_msg,
                )
                continue

    # All retries exhausted
    raise GeminiServiceError(
        "Failed to generate a valid mystery after multiple attempts. "
        "Please try starting a new case."
    )


# Offline/Mock Mysteries
MOCK_MYSTERIES = [
    {
        "victim_name": "Arthur Pendelton",
        "victim_occupation": "Art Collector & Critic",
        "victim_backstory": "Arthur Pendelton was found dead in his private study. He was known for exposing forged artwork and was hosting a private viewing of his latest acquisition, 'The Whispering Muse'.",
        "crime_scene": "Pendelton Manor Gallery Room",
        "crime_scene_description": "A grand room filled with classical paintings. Arthur was found slumped over his desk next to a shattered display case that once held 'The Whispering Muse'.",
        "time_of_death": "10:30 PM",
        "cause_of_death": "Blunt force trauma to the back of the skull",
        "initial_report": "At 11:00 PM, the butler discovered Arthur Pendelton's body in the private gallery. 'The Whispering Muse' was missing, replaced with a crude duplicate. The room showed signs of a struggle, and a heavy marble bust was found nearby with blood on the base. Three guests were present at the mansion during the estimated time of death.",
        "suspects": [
            {
                "id": "suspect_1",
                "name": "Julian Vance",
                "occupation": "Art Appraiser",
                "relationship": "Arthur's business partner",
                "motive": "Arthur recently discovered Julian had been validating forged paintings for years and threatened to ruin his career.",
                "alibi": "I was in the library downstairs reading from 10:00 PM to 11:00 PM. I never went uppercase to the gallery. You can ask the butler, he brought me a cup of chamomile tea in the library at 10:45 PM.",
                "is_murderer": True
            },
            {
                "id": "suspect_2",
                "name": "Clara Sterling",
                "occupation": "Professional Artist",
                "relationship": "Disgruntled client",
                "motive": "Clara claims Arthur stole her finest painting and passed it off as a historical masterwork, ruining her chance at recognition.",
                "alibi": "I was in the conservatory smoking a cigarette from 10:15 PM until the body was found. I needed some air because Arthur and I had a heated argument earlier about my contracts.",
                "is_murderer": False
            },
            {
                "id": "suspect_3",
                "name": "Richard Pendelton",
                "occupation": "Arthur's Nephew",
                "relationship": "Sole heir to the estate",
                "motive": "Richard is deeply in debt to local loan sharks and stood to inherit Arthur's entire fortune upon his death.",
                "alibi": "I was feeling unwell, so I retired to my guest room on the second floor at 9:45 PM. I slept right through the entire evening until the police sirens woke me up.",
                "is_murderer": False
            }
        ],
        "clues": [
            {
                "id": "clue_1",
                "title": "Library Tea Cup",
                "description": "A porcelain tea cup found cold and untouched on the library table.",
                "type": "physical",
                "related_suspect_id": "suspect_1"
            },
            {
                "id": "clue_2",
                "title": "Muddy Footprints",
                "description": "Fresh muddy footprints of size 10 shoes leading from the conservatory back doors into the main hallway.",
                "type": "physical",
                "related_suspect_id": "suspect_2"
            },
            {
                "id": "clue_3",
                "title": "Broken Glasses",
                "description": "A pair of wire-rimmed reading glasses found under the gallery desk. Julian Vance wears identical wire-rimmed glasses.",
                "type": "physical",
                "related_suspect_id": "suspect_1"
            },
            {
                "id": "clue_4",
                "title": "Torn Canvas Scrap",
                "description": "A scrap of canvas caught on the gallery door latch. The canvas fibers are fresh paint, smelling of linseed oil, matching Clara's paints.",
                "type": "physical",
                "related_suspect_id": "suspect_2"
            },
            {
                "id": "clue_5",
                "title": "Text Messages",
                "description": "Text messages on Richard's phone sent at 10:35 PM, showing him actively messaging his creditor, saying: 'It is done. I will have the funds tomorrow.'",
                "type": "digital",
                "related_suspect_id": "suspect_3"
            },
            {
                "id": "clue_6",
                "title": "Butler's Statement",
                "description": "The butler's written statement: 'I tried to take Julian Vance his tea at 10:45 PM, but the library was empty. I left the cup on the table.'",
                "type": "witness",
                "related_suspect_id": "suspect_1"
            }
        ],
        "contradictions": [
            {
                "id": "julian_alibi_tea",
                "description": "Julian claimed he was in the library receiving tea from the butler at 10:45 PM, but the cold, untouched tea cup and the butler's statement prove Julian was not in the library when the butler arrived.",
                "clue_ids": ["clue_1", "clue_6"],
                "suspect_id": "suspect_1",
                "hint": "Look closely at Julian's alibi about the library tea, the tea cup, and what the butler actually did."
            },
            {
                "id": "richard_alibi_sleep",
                "description": "Richard claimed he retired to bed at 9:45 PM and slept through the night, but his phone activity shows he was sending active text messages at 10:35 PM.",
                "clue_ids": ["clue_5"],
                "suspect_id": "suspect_3",
                "hint": "Compare Richard's claim about sleeping through the evening with his digital footprint at the time of the murder."
            }
        ],
        "murderer_id": "suspect_1",
        "solution_narrative": "Julian Vance was selling forged paintings under Arthur's nose. When Arthur discovered the truth and threatened to call the police, Julian knew his career was over. During the private viewing, Julian slipped away from the library (leaving the tea cup untouched and missing the butler's visit) and confronted Arthur in the gallery. A struggle ensued, and Julian struck Arthur with a heavy marble bust, shattering his reading glasses in the process and leaving them behind. He then swapped 'The Whispering Muse' with a forged copy to make it look like a simple art heist, but his flawed alibi and left-behind glasses sealed his fate."
    },
    {
        "victim_name": "Baron Reginald Sterling",
        "victim_occupation": "Master Winemaker",
        "victim_backstory": "Reginald was hosting an exclusive tasting of his vault reserve, the 1945 'Chateau Sterling', reserved for his closest companions. He collapsed after taking the first sip.",
        "crime_scene": "Sterling Winery Vault",
        "crime_scene_description": "A stone cellar lined with ancient oak barrels. A tasting table stands in the center, featuring an uncorked bottle and several crystal glasses.",
        "time_of_death": "8:15 PM",
        "cause_of_death": "Cyanide poisoning",
        "initial_report": "During the tasting of the 1945 Chateau Sterling, Baron Reginald fell to the ground clutching his throat. The wine was found to be laced with potassium cyanide. Three associates were present in the cellar during the tasting.",
        "suspects": [
            {
                "id": "suspect_1",
                "name": "Evelyn Sterling",
                "occupation": "Sommelier",
                "relationship": "Reginald's estranged daughter",
                "motive": "Evelyn was cut out of her father's will in favor of his business partner, and wanted to reclaim her inheritance.",
                "alibi": "I was preparing the appetizer platters in the cellar kitchen from 8:00 PM to 8:20 PM. I only returned when I heard the glass shatter.",
                "is_murderer": False
            },
            {
                "id": "suspect_2",
                "name": "Dr. Marcus Vance",
                "occupation": "Toxicologist",
                "relationship": "Family physician",
                "motive": "Marcus was being blackmailed by Reginald over falsified medical certificates for winery insurance claims.",
                "alibi": "I was standing near the cellar entrance, talking on a phone call with the hospital about an emergency patient from 8:10 PM until 8:20 PM.",
                "is_murderer": True
            },
            {
                "id": "suspect_3",
                "name": "Lawrence Croft",
                "occupation": "Wine Distributor",
                "relationship": "Business partner",
                "motive": "Lawrence was embezzling millions from the winery, and Reginald was about to audit the distribution accounts the next day.",
                "alibi": "I was examining the barrel casks at the far end of the cellar from 8:05 PM to 8:15 PM. I never went near the tasting table.",
                "is_murderer": False
            }
        ],
        "clues": [
            {
                "id": "clue_1",
                "title": "Kitchen Logs",
                "description": "The kitchen service logs show Evelyn was indeed logged in and out of the kitchen between 8:00 PM and 8:20 PM.",
                "type": "document",
                "related_suspect_id": "suspect_1"
            },
            {
                "id": "clue_2",
                "title": "Syringe in Dustbin",
                "description": "A medical-grade syringe containing traces of cyanide found in the restroom trash bin.",
                "type": "physical",
                "related_suspect_id": "suspect_2"
            },
            {
                "id": "clue_3",
                "title": "Cellar Phone Records",
                "description": "Network tower records show Dr. Marcus Vance's phone did not make or receive any calls between 7:30 PM and 9:00 PM.",
                "type": "phone_record",
                "related_suspect_id": "suspect_2"
            },
            {
                "id": "clue_4",
                "title": "Corkscrew Fingerprints",
                "description": "Clear fingerprints belonging to Lawrence Croft found on the corkscrew used to open the vintage bottle.",
                "type": "fingerprint",
                "related_suspect_id": "suspect_3"
            },
            {
                "id": "clue_5",
                "title": "Wine Glass Traces",
                "description": "Forensic analysis shows poison was only present in Reginald's glass, not inside the main wine bottle.",
                "type": "forensic",
                "related_suspect_id": "suspect_2"
            }
        ],
        "contradictions": [
            {
                "id": "marcus_phone_alibi",
                "description": "Dr. Marcus Vance claimed he was on an emergency phone call with the hospital from 8:10 PM to 8:20 PM, but the phone records show his phone had no call activity during that time.",
                "clue_ids": ["clue_3"],
                "suspect_id": "suspect_2",
                "hint": "Compare Marcus's claim of being on the phone with the network tower logs."
            },
            {
                "id": "poison_location",
                "description": "Lawrence Croft was suspected because of his fingerprints on the corkscrew, but forensic evidence shows the bottle was not poisoned; only Reginald's glass was laced, indicating the poison was added after the wine was poured.",
                "clue_ids": ["clue_4", "clue_5"],
                "suspect_id": "suspect_3",
                "hint": "Look at where the poison was found compared to who opened the bottle."
            }
        ],
        "murderer_id": "suspect_2",
        "solution_narrative": "Dr. Marcus Vance was desperate to keep his blackmail secret. Knowing Reginald was opening the rare vintage, Marcus brought a syringe filled with liquid cyanide. While Lawrence was busy uncorking the wine and Evelyn was in the kitchen, Marcus claimed he had to take a phone call. Instead of making a call, he slipped to the tasting table under the guise of examining the glass, injected the cyanide directly into Reginald's crystal glass, and disposed of the syringe in the restroom. The phone record discrepancy and the localized poison on the glass exposed his crime."
    }
]


def generate_mock_mystery(theme: str | None = None) -> Mystery:
    """Returns a pre-validated offline mystery based on the selected theme."""
    logger.info("Generating mock/offline mystery for theme: %s", theme)
    
    selected_data = None
    if theme:
        theme_lower = theme.lower()
        if "art" in theme_lower or "forge" in theme_lower:
            selected_data = MOCK_MYSTERIES[0]
        elif "wine" in theme_lower or "vintage" in theme_lower:
            selected_data = MOCK_MYSTERIES[1]
            
    if not selected_data:
        selected_data = random.choice(MOCK_MYSTERIES)
        
    return validate_mystery(selected_data)


# ═══════════════════════════════════════════════════════════════
#  SCORING CONSTANTS & FUNCTIONS (from services/scoring_service.py)
# ═══════════════════════════════════════════════════════════════

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
    """Return the detective rank for a given score."""
    for threshold, rank in RANKS:
        if score >= threshold:
            return rank
    return "🔰 Rookie"


def calculate_max_score(num_clues: int, num_suspects: int, num_contradictions: int) -> int:
    """Calculate the maximum possible score for a given mystery."""
    return (
        (num_clues * POINTS_CLUE)
        + (num_suspects * POINTS_INTERROGATION)
        + (num_contradictions * POINTS_CONTRADICTION)
        + POINTS_CORRECT_ACCUSATION
    )


# ═══════════════════════════════════════════════════════════════
#  SESSION STATE MANAGER (from utils/session_manager.py)
# ═══════════════════════════════════════════════════════════════

def sm_init_session() -> None:
    """Initialise session state with defaults if not already set."""
    if "game_state" not in st.session_state:
        st.session_state.game_state = get_default_game_state()
    if "is_offline_mode" not in st.session_state:
        st.session_state.is_offline_mode = False
    if "use_offline_preference" not in st.session_state:
        st.session_state.use_offline_preference = False


def sm_reset_session() -> None:
    """Reset all game state for a new game."""
    st.session_state.game_state = get_default_game_state()


def sm_get_state() -> dict:
    """Get the current game state dictionary."""
    return st.session_state.game_state


def sm_set_mystery(mystery) -> None:
    """Store a validated Mystery object and transition to investigating phase."""
    state = sm_get_state()
    state["mystery"] = mystery
    state["game_phase"] = "investigating"


def sm_set_phase(phase: str) -> None:
    """Set the current game phase."""
    sm_get_state()["game_phase"] = phase


def sm_get_phase() -> str:
    """Get the current game phase string."""
    return sm_get_state()["game_phase"]


def sm_get_mystery():
    """Get the current Mystery object, or None."""
    return sm_get_state()["mystery"]


def sm_get_score() -> int:
    """Get the current score."""
    return sm_get_state()["score"]


def sm_add_score(points: int, description: str) -> None:
    """Add points to the score and log the action."""
    state = sm_get_state()
    state["score"] += points
    state["score_log"].append((description, points))


def sm_reveal_clue(clue_id: str) -> bool:
    """Mark a clue as revealed. Returns True if first time."""
    state = sm_get_state()
    if clue_id not in state["revealed_clues"]:
        state["revealed_clues"].add(clue_id)
        return True
    return False


def sm_interrogate_suspect(suspect_id: str) -> bool:
    """Mark a suspect as interrogated. Returns True if first time."""
    state = sm_get_state()
    if suspect_id not in state["interrogated_suspects"]:
        state["interrogated_suspects"].add(suspect_id)
        return True
    return False


def sm_discover_contradiction(contradiction_id: str) -> bool:
    """Mark a contradiction as discovered. Returns True if first time."""
    state = sm_get_state()
    if contradiction_id not in state["discovered_contradictions"]:
        state["discovered_contradictions"].add(contradiction_id)
        return True
    return False


def sm_submit_accusation(suspect_id: str) -> None:
    """Record the player's accusation and end the game."""
    state = sm_get_state()
    state["accusation_made"] = True
    state["accused_suspect_id"] = suspect_id
    state["case_closed"] = True
    state["game_phase"] = "case_closed"


def sm_add_note(note: str) -> None:
    """Append an investigation note."""
    sm_get_state()["investigation_notes"].append(note)


def sm_get_progress() -> float:
    """Calculate investigation progress as a float between 0.0 and 1.0."""
    state = sm_get_state()
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


# ═══════════════════════════════════════════════════════════════
#  GAME SERVICE FUNCTIONS (from services/game_service.py)
# ═══════════════════════════════════════════════════════════════

def start_new_case(theme: str | None = None, use_offline: bool = False) -> str | None:
    """Generate a new mystery case and initialise game state."""
    sm_reset_session()
    sm_set_phase("generating")

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

        sm_set_mystery(mystery)
        sm_add_note("📋 Case file opened. Investigation begins.")
        if st.session_state.get("is_offline_mode", False):
            sm_add_note("⚠️ Running in Offline Mode (local case loaded due to API settings or rate limits).")

        logger.info("New case started: victim=%s, scene=%s, offline=%s",
                    mystery.victim_name, mystery.crime_scene, st.session_state.get("is_offline_mode", False))
        return None  # Success
    except Exception as e:
        sm_set_phase("not_started")
        logger.error("Unexpected error starting case: %s", e)
        return "Something went wrong generating your case. Please try again."


def reveal_clue(clue_id: str) -> None:
    """Reveal a clue and award points if it's the first time."""
    is_new = sm_reveal_clue(clue_id)
    if is_new:
        sm_add_score(POINTS_CLUE, f"Examined clue: {clue_id}")

        # Find the clue title for the note
        mystery = sm_get_mystery()
        if mystery:
            clue = next((c for c in mystery.clues if c.id == clue_id), None)
            if clue:
                sm_add_note(f"🔍 Examined evidence: {clue.title}")


def interrogate_suspect(suspect_id: str) -> None:
    """Interrogate a suspect and award points if first time."""
    is_new = sm_interrogate_suspect(suspect_id)
    if is_new:
        sm_add_score(POINTS_INTERROGATION, f"Interrogated: {suspect_id}")

        mystery = sm_get_mystery()
        if mystery:
            suspect = next((s for s in mystery.suspects if s.id == suspect_id), None)
            if suspect:
                sm_add_note(f"🗣️ Interrogated {suspect.name} — noted their alibi.")


def check_contradictions() -> list[str]:
    """
    Check if any undiscovered contradictions can be found based on revealed clues.
    """
    state = sm_get_state()
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
            is_new = sm_discover_contradiction(contradiction.id)
            if is_new:
                sm_add_score(POINTS_CONTRADICTION, f"Found contradiction: {contradiction.id}")
                sm_add_note(f"⚡ Contradiction discovered: {contradiction.description}")
                newly_found.append(contradiction.id)

    return newly_found


def submit_accusation(suspect_id: str) -> bool:
    """Submit the player's accusation and evaluate it."""
    mystery = sm_get_mystery()
    if mystery is None:
        return False

    sm_submit_accusation(suspect_id)
    is_correct = suspect_id == mystery.murderer_id

    if is_correct:
        sm_add_score(POINTS_CORRECT_ACCUSATION, "Correct accusation!")
        sm_add_note("✅ Correct! You identified the murderer!")
    else:
        sm_add_score(POINTS_WRONG_ACCUSATION, "Wrong accusation")
        # Find who the player accused
        accused = next((s for s in mystery.suspects if s.id == suspect_id), None)
        murderer = next((s for s in mystery.suspects if s.id == mystery.murderer_id), None)
        accused_name = accused.name if accused else "Unknown"
        murderer_name = murderer.name if murderer else "Unknown"
        sm_add_note(
            f"❌ Wrong! You accused {accused_name}, "
            f"but the murderer was {murderer_name}."
        )

    return is_correct


# Initialise Session State
sm_init_session()


# ═══════════════════════════════════════════════════════════════
#  UI RENDERING COMPONENTS (from app.py)
# ═══════════════════════════════════════════════════════════════

def render_sidebar():
    """Render the sidebar with case info, score, and controls."""
    with st.sidebar:
        st.markdown("# 🔍 Murder Mystery")
        st.markdown("##### *AI-Powered Detective Game*")
        st.markdown("---")

        phase = sm_get_phase()

        # Start New Case Button
        if phase == "not_started":
            st.markdown("### ⚙️ Case Settings")
            theme_choice = st.selectbox(
                "🎨 Case Setting / Theme",
                options=["🎲 Random Theme", "✍️ Custom Theme..."] + THEME_SEEDS,
                key="theme_choice_start",
            )
            selected_theme = None
            if theme_choice == "✍️ Custom Theme...":
                custom_theme = st.text_input(
                    "Enter custom setting/theme:",
                    placeholder="e.g. Victorian train, space station...",
                    key="custom_theme_start",
                )
                if custom_theme.strip():
                    selected_theme = custom_theme.strip()
            elif theme_choice != "🎲 Random Theme":
                selected_theme = theme_choice

            use_offline = st.checkbox(
                "🔌 Offline Mode (Local Case)",
                value=st.session_state.get("use_offline_preference", False),
                help="Play using pre-written offline cases. Bypasses Gemini API rate limits."
            )

            st.markdown("")
            if st.button("🎲 Start New Case", use_container_width=True, type="primary"):
                with st.spinner("🔮 Generating mystery..."):
                    error = start_new_case(selected_theme, use_offline=use_offline)
                if error:
                    st.error(f"⚠️ {error}")
                else:
                    st.rerun()

        # Case Info
        if phase in ("investigating", "case_closed"):
            mystery = sm_get_mystery()
            if mystery:
                st.markdown("### 📋 Case Info")
                st.markdown(f"**Victim:** {mystery.victim_name}")
                st.markdown(f"**Scene:** {mystery.crime_scene}")
                st.markdown(f"**Cause:** {mystery.cause_of_death}")

                status_emoji = "🔍" if phase == "investigating" else "📁"
                status_text = "Investigating" if phase == "investigating" else "Case Closed"
                if st.session_state.get("is_offline_mode", False):
                    status_text += " (Offline 🔌)"
                st.markdown(f"**Status:** {status_emoji} {status_text}")

                st.markdown("---")

                # Score
                st.markdown("### 🏆 Detective Score")
                score = sm_get_score()
                max_score = calculate_max_score(
                    len(mystery.clues),
                    len(mystery.suspects),
                    len(mystery.contradictions),
                )
                st.metric("Points", score, help=f"Max possible: {max_score}")
                st.markdown(f"**Rank:** {get_rank(score)}")

                st.markdown("---")

                # Progress
                state = sm_get_state()
                st.markdown("### 📊 Investigation Progress")

                clues_found = len(state["revealed_clues"])
                clues_total = len(mystery.clues)
                contradictions_found = len(state["discovered_contradictions"])
                contradictions_total = len(mystery.contradictions)
                suspects_talked = len(state["interrogated_suspects"])
                suspects_total = len(mystery.suspects)

                st.markdown(f"🔎 Clues: **{clues_found}/{clues_total}**")
                st.markdown(f"⚡ Contradictions: **{contradictions_found}/{contradictions_total}**")
                st.markdown(f"🗣️ Interrogated: **{suspects_talked}/{suspects_total}**")

                progress = sm_get_progress()
                st.progress(progress, text=f"{int(progress * 100)}% Complete")

                st.markdown("---")

        # New Game Button (always available when in game)
        if phase in ("investigating", "case_closed"):
            with st.expander("⚙️ Next Case Settings", expanded=False):
                theme_choice = st.selectbox(
                    "🎨 Next Setting / Theme",
                    options=["🎲 Random Theme", "✍️ Custom Theme..."] + THEME_SEEDS,
                    key="theme_choice_new",
                )
                selected_theme = None
                if theme_choice == "✍️ Custom Theme...":
                    custom_theme = st.text_input(
                        "Enter custom setting/theme:",
                        placeholder="e.g. Space colony, medieval castle...",
                        key="custom_theme_new",
                    )
                    if custom_theme.strip():
                        selected_theme = custom_theme.strip()
                elif theme_choice != "🎲 Random Theme":
                    selected_theme = theme_choice

                use_offline = st.checkbox(
                    "🔌 Offline Mode (Local Case)",
                    value=st.session_state.get("use_offline_preference", False),
                    key="offline_choice_new",
                    help="Play using pre-written offline cases. Bypasses Gemini API rate limits."
                )

            if st.button("🔄 New Game", use_container_width=True):
                with st.spinner("🔮 Generating new mystery..."):
                    error = start_new_case(selected_theme, use_offline=use_offline)
                if error:
                    st.error(f"⚠️ {error}")
                else:
                    st.rerun()


def render_welcome():
    """Render the welcome screen when no game is active."""
    st.markdown("""
    <div class="welcome-container">
        <h1>🔍 Murder Mystery Detective</h1>
        <p class="subtitle">Every case is unique. Every clue matters. Can you find the killer?</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="suspect-card" style="text-align:center;">
            <div style="font-size:2.5rem; margin-bottom:0.5rem;">🎭</div>
            <div class="suspect-name">AI-Generated Mysteries</div>
            <div class="suspect-detail">Every case is uniquely crafted by Gemini AI — no two games are alike.</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="suspect-card" style="text-align:center;">
            <div style="font-size:2.5rem; margin-bottom:0.5rem;">🔎</div>
            <div class="suspect-name">Investigate & Deduce</div>
            <div class="suspect-detail">Examine clues, interrogate suspects, and uncover hidden contradictions.</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="suspect-card" style="text-align:center;">
            <div style="font-size:2.5rem; margin-bottom:0.5rem;">⚖️</div>
            <div class="suspect-name">Accuse the Killer</div>
            <div class="suspect-detail">Build your case and make your accusation. One shot — make it count.</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("")
    st.markdown("")
    _, center, _ = st.columns([1, 2, 1])
    with center:
        st.info("👈 Click **Start New Case** in the sidebar to begin your investigation!")


def render_crime_scene():
    """Render the crime scene briefing section."""
    mystery = sm_get_mystery()
    if not mystery:
        return

    if st.session_state.get("is_offline_mode", False):
        st.info("🔌 **Playing in Offline Mode** using a local pre-written case (bypassed Gemini API limits).")

    st.markdown("""<hr class="section-divider">""", unsafe_allow_html=True)
    st.markdown("## 🔍 Crime Scene Briefing")

    # Case file header
    st.markdown(f"""
    <div class="case-header">
        <h2>📁 Case File — {mystery.victim_name}</h2>
        <p><strong>Victim:</strong> {mystery.victim_name} — {mystery.victim_occupation}<br>
        <strong>Location:</strong> {mystery.crime_scene}<br>
        <strong>Time of Death:</strong> {mystery.time_of_death}<br>
        <strong>Cause of Death:</strong> {mystery.cause_of_death}</p>
    </div>
    """, unsafe_allow_html=True)

    # Backstory and scene
    col1, col2 = st.columns([3, 2])
    with col1:
        st.markdown("#### 📝 Initial Report")
        st.markdown(mystery.initial_report)
    with col2:
        st.markdown("#### 🏛️ Crime Scene")
        st.markdown(mystery.crime_scene_description)
        st.markdown("---")
        st.markdown("#### 👤 About the Victim")
        st.markdown(mystery.victim_backstory)


def render_suspects():
    """Render suspect cards with interrogation buttons."""
    mystery = sm_get_mystery()
    if not mystery:
        return

    state = sm_get_state()

    st.markdown("""<hr class="section-divider">""", unsafe_allow_html=True)
    st.markdown("## 🎭 Suspects")

    cols = st.columns(len(mystery.suspects))

    for i, suspect in enumerate(mystery.suspects):
        with cols[i]:
            is_interrogated = suspect.id in state["interrogated_suspects"]
            badge = " ✅" if is_interrogated else ""

            st.markdown(f"""
            <div class="suspect-card">
                <div class="suspect-name">🎭 {suspect.name}{badge}</div>
                <div class="suspect-occupation">{suspect.occupation}</div>
                <div class="suspect-detail"><strong>Relationship:</strong> {suspect.relationship}</div>
                <div class="suspect-detail"><strong>Motive:</strong> {suspect.motive}</div>
            </div>
            """, unsafe_allow_html=True)

            if not is_interrogated:
                if st.button(
                    f"🔎 Interrogate {suspect.name.split()[0]}",
                    key=f"interrogate_{suspect.id}",
                    use_container_width=True,
                ):
                    interrogate_suspect(suspect.id)
                    st.rerun()
            else:
                with st.expander(f"📜 {suspect.name.split()[0]}'s Alibi", expanded=False):
                    st.markdown(f"*\"{suspect.alibi}\"*")


def render_clues():
    """Render the evidence locker with revealable clues."""
    mystery = sm_get_mystery()
    if not mystery:
        return

    state = sm_get_state()

    st.markdown("""<hr class="section-divider">""", unsafe_allow_html=True)
    st.markdown("## 🗄️ Evidence Locker")
    st.caption("Click on evidence items to examine them and earn investigation points.")

    col1, col2 = st.columns(2)

    for i, clue in enumerate(mystery.clues):
        is_revealed = clue.id in state["revealed_clues"]
        target_col = col1 if i % 2 == 0 else col2

        with target_col:
            if is_revealed:
                # Show revealed clue
                st.markdown(f"""
                <div class="clue-card">
                    <div class="clue-title">✅ {clue.title}</div>
                    <div class="clue-type">📂 {clue.type.replace('_', ' ')}</div>
                    <div class="clue-desc">{clue.description}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                # Show hidden clue with reveal button
                st.markdown(f"""
                <div class="clue-card" style="opacity: 0.6;">
                    <div class="clue-title">🔒 Evidence #{i + 1}</div>
                    <div class="clue-type">📂 {clue.type.replace('_', ' ')}</div>
                    <div class="clue-desc" style="color: var(--text-muted); font-style: italic;">
                        Click below to examine this evidence...
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if st.button(
                    f"🔍 Examine Evidence #{i + 1}",
                    key=f"reveal_{clue.id}",
                    use_container_width=True,
                ):
                    reveal_clue(clue.id)
                    st.rerun()

    # Check for Contradictions
    st.markdown("")
    revealed_count = len(state["revealed_clues"])
    if revealed_count >= 2:
        if st.button(
            "⚡ Analyze Evidence for Contradictions",
            use_container_width=True,
            type="primary",
        ):
            newly_found = check_contradictions()
            if newly_found:
                st.rerun()
            else:
                st.info("🔍 No new contradictions found yet. Keep collecting evidence!")


def render_investigation_notes():
    """Render discovered contradictions, notes, and score log."""
    mystery = sm_get_mystery()
    if not mystery:
        return

    state = sm_get_state()

    st.markdown("""<hr class="section-divider">""", unsafe_allow_html=True)
    st.markdown("## 📝 Investigation Notes")

    tab1, tab2, tab3 = st.tabs(["⚡ Contradictions", "📋 Notes", "🏆 Score Log"])

    with tab1:
        discovered = state["discovered_contradictions"]
        if discovered:
            for contradiction in mystery.contradictions:
                if contradiction.id in discovered:
                    st.markdown(f"""
                    <div class="contradiction-found">
                        <div class="contradiction-title">⚡ {contradiction.id.replace('_', ' ').title()}</div>
                        <div class="contradiction-desc">{contradiction.description}</div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.markdown("*No contradictions discovered yet. Examine more clues and analyze the evidence!*")

        # Show hints for undiscovered contradictions
        undiscovered = [
            c for c in mystery.contradictions
            if c.id not in discovered
        ]
        if undiscovered and len(discovered) > 0:
            with st.expander("💡 Hints", expanded=False):
                for c in undiscovered:
                    st.markdown(f"- 💡 *{c.hint}*")

    with tab2:
        notes = state["investigation_notes"]
        if notes:
            for note in notes:
                st.markdown(f"- {note}")
        else:
            st.markdown("*Investigation notes will appear here as you progress.*")

    with tab3:
        score_log = state["score_log"]
        if score_log:
            for action, points in score_log:
                sign = "+" if points >= 0 else ""
                color = "green" if points >= 0 else "red"
                st.markdown(
                    f"- {action}: "
                    f"<span style='color:{color}; font-weight:bold;'>{sign}{points} pts</span>",
                    unsafe_allow_html=True,
                )
            st.markdown(f"**Total: {sm_get_score()} pts**")
        else:
            st.markdown("*Score updates will appear here.*")


def render_accusation():
    """Render the accusation form."""
    mystery = sm_get_mystery()
    if not mystery:
        return

    state = sm_get_state()
    if state["accusation_made"]:
        return

    st.markdown("""<hr class="section-divider">""", unsafe_allow_html=True)
    st.markdown("## ⚖️ Make Your Accusation")
    st.warning("⚠️ **You only get ONE shot.** A correct accusation earns **+100 pts**. A wrong one costs **-50 pts**.")

    suspect_names = {s.name: s.id for s in mystery.suspects}
    selected_name = st.selectbox(
        "Who do you believe is the murderer?",
        options=list(suspect_names.keys()),
        index=None,
        placeholder="Select a suspect...",
    )

    if selected_name:
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("⚖️ Submit Accusation", type="primary"):
                st.session_state._confirm_accusation = True
                st.session_state._accused_name = selected_name

        # Confirmation step
        if getattr(st.session_state, "_confirm_accusation", False):
            st.markdown("")
            st.error(f"🔔 **Are you sure you want to accuse {st.session_state._accused_name}?** This cannot be undone!")
            c1, c2, _ = st.columns([1, 1, 3])
            with c1:
                if st.button("✅ Yes, I'm sure", type="primary"):
                    accused_name = st.session_state._accused_name
                    accused_id = suspect_names[accused_name]
                    del st.session_state._confirm_accusation
                    del st.session_state._accused_name
                    submit_accusation(accused_id)
                    st.rerun()
            with c2:
                if st.button("❌ Cancel"):
                    del st.session_state._confirm_accusation
                    del st.session_state._accused_name
                    st.rerun()


def render_case_closed():
    """Render the case closed results screen."""
    mystery = sm_get_mystery()
    state = sm_get_state()
    if not mystery or not state["case_closed"]:
        return

    accused_id = state["accused_suspect_id"]
    is_correct = accused_id == mystery.murderer_id

    murderer = next((s for s in mystery.suspects if s.id == mystery.murderer_id), None)
    accused = next((s for s in mystery.suspects if s.id == accused_id), None)

    # Result Banner
    if is_correct:
        st.markdown(f"""
        <div class="case-closed-banner correct">
            <h2 style="color: var(--success);">🎉 CASE SOLVED!</h2>
            <p style="font-size: 1.2rem; color: var(--text-primary);">
                Brilliant work, Detective! You correctly identified 
                <strong>{murderer.name}</strong> as the murderer.
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.balloons()
    else:
        st.markdown(f"""
        <div class="case-closed-banner wrong">
            <h2 style="color: var(--danger);">❌ WRONG SUSPECT</h2>
            <p style="font-size: 1.2rem; color: var(--text-primary);">
                You accused <strong>{accused.name if accused else 'Unknown'}</strong>, 
                but the real murderer was <strong>{murderer.name if murderer else 'Unknown'}</strong>.
            </p>
        </div>
        """, unsafe_allow_html=True)

    # Solution Narrative
    st.markdown("### 📖 The Full Story")
    st.markdown(f"""
    <div class="case-header">
        <p>{mystery.solution_narrative}</p>
    </div>
    """, unsafe_allow_html=True)

    # The Murderer
    if murderer:
        st.markdown("### 🎭 The Murderer")
        st.markdown(f"""
        <div class="suspect-card">
            <div class="suspect-name">🔴 {murderer.name}</div>
            <div class="suspect-occupation">{murderer.occupation}</div>
            <div class="suspect-detail"><strong>Relationship:</strong> {murderer.relationship}</div>
            <div class="suspect-detail"><strong>Motive:</strong> {murderer.motive}</div>
            <div class="suspect-detail"><strong>Alibi (flawed):</strong> <em>"{murderer.alibi}"</em></div>
        </div>
        """, unsafe_allow_html=True)

    # Contradictions Summary
    st.markdown("### ⚡ All Contradictions")
    discovered = state["discovered_contradictions"]
    for c in mystery.contradictions:
        found = c.id in discovered
        icon = "✅" if found else "❌ Missed"
        color_class = "contradiction-found" if found else "clue-card"
        st.markdown(f"""
        <div class="{color_class}">
            <div class="contradiction-title">{icon} — {c.id.replace('_', ' ').title()}</div>
            <div class="contradiction-desc">{c.description}</div>
        </div>
        """, unsafe_allow_html=True)

    # Final Score
    st.markdown("""<hr class="section-divider">""", unsafe_allow_html=True)
    st.markdown("### 🏆 Final Results")

    score = sm_get_score()
    max_score = calculate_max_score(
        len(mystery.clues),
        len(mystery.suspects),
        len(mystery.contradictions),
    )
    rank = get_rank(score)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Final Score", f"{score} pts")
    with col2:
        st.metric("Max Possible", f"{max_score} pts")
    with col3:
        st.metric("Detective Rank", rank)

    # Score Breakdown
    with st.expander("📊 Score Breakdown", expanded=True):
        score_log = state["score_log"]
        if score_log:
            for action, points in score_log:
                sign = "+" if points >= 0 else ""
                color = "green" if points >= 0 else "red"
                st.markdown(
                    f"- {action}: "
                    f"<span style='color:{color}; font-weight:bold;'>{sign}{points} pts</span>",
                    unsafe_allow_html=True,
                )

    # Play Again
    st.markdown("")
    _, center, _ = st.columns([1, 2, 1])
    with center:
        if st.button("🎲 Start a New Case", use_container_width=True, type="primary"):
            theme_choice = st.session_state.get("theme_choice_new", "🎲 Random Theme")
            selected_theme = None
            if theme_choice == "✍️ Custom Theme...":
                custom_theme = st.session_state.get("custom_theme_new", "")
                if custom_theme.strip():
                    selected_theme = custom_theme.strip()
            elif theme_choice != "🎲 Random Theme":
                selected_theme = theme_choice

            use_offline = st.session_state.get("offline_choice_new", False)
            with st.spinner("🔮 Generating new mystery..."):
                error = start_new_case(selected_theme, use_offline=use_offline)
            if error:
                st.error(f"⚠️ {error}")
            else:
                st.rerun()


# ═══════════════════════════════════════════════════════════════
#  MAIN APPLICATION ROUTING
# ═══════════════════════════════════════════════════════════════

def main():
    """Main application entry point — routes to the correct phase."""
    render_sidebar()

    phase = sm_get_phase()

    if phase == "not_started":
        render_welcome()

    elif phase == "generating":
        st.markdown("## 🔮 Generating Mystery...")
        st.spinner("Gemini AI is crafting your unique case...")

    elif phase == "investigating":
        render_crime_scene()
        render_suspects()
        render_clues()
        render_investigation_notes()
        render_accusation()

    elif phase == "case_closed":
        render_case_closed()


if __name__ == "__main__":
    main()
