"""
Gemini AI service for mystery generation.

Handles API configuration, prompt building, API calls,
JSON extraction, and retry logic.

Uses the `google-genai` SDK (new recommended client).
"""

import json
import logging
import os
import random

from google import genai
from google.genai import types
from dotenv import load_dotenv

from models.mystery import Mystery
from prompts.mystery_prompts import SYSTEM_PROMPT, GENERATION_PROMPT, RETRY_PROMPT
from utils.validator import validate_mystery, ValidationError

logger = logging.getLogger(__name__)

# Theme seeds for diversity
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
    """
    Load the API key and create a Gemini client.

    Returns:
        A google.genai.Client instance.

    Raises:
        GeminiServiceError: If the API key is missing.
    """
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key or api_key == "your_gemini_api_key_here":
        raise GeminiServiceError(
            "GEMINI_API_KEY is not set. Please add your API key to the .env file."
        )

    return genai.Client(api_key=api_key)


def _extract_json(text: str) -> dict:
    """
    Extract a JSON object from Gemini's response text.

    Handles cases where the response might be wrapped in
    markdown code fences or contain extra whitespace.

    Args:
        text: Raw response text from Gemini.

    Returns:
        Parsed dictionary.

    Raises:
        GeminiServiceError: If JSON extraction fails.
    """
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
    """
    Generate a complete mystery using Gemini AI.

    Sends the generation prompt, validates the response,
    and retries up to MAX_RETRIES times if validation fails.

    Args:
        theme: Optional custom theme or setting string.

    Returns:
        A validated Mystery instance.

    Raises:
        GeminiServiceError: If generation fails after all retries.
    """
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
            # If it's a rate limit or timeout/connectivity issue, raise immediately
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


# ── Offline/Mock Mystery Data ──────────────────────────────────────
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
                "alibi": "I was in the library downstairs reading from 10:00 PM to 11:00 PM. I never went upstairs to the gallery. You can ask the butler, he brought me a cup of chamomile tea in the library at 10:45 PM.",
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
    """
    Returns a pre-validated offline mystery based on the selected theme.
    """
    logger.info("Generating mock/offline mystery for theme: %s", theme)
    
    # Try to find a theme matching the user's choice
    selected_data = None
    if theme:
        theme_lower = theme.lower()
        if "art" in theme_lower or "forge" in theme_lower:
            selected_data = MOCK_MYSTERIES[0]
        elif "wine" in theme_lower or "vintage" in theme_lower:
            selected_data = MOCK_MYSTERIES[1]
            
    # Fallback to random choice from mock mysteries if not matched
    if not selected_data:
        selected_data = random.choice(MOCK_MYSTERIES)
        
    return validate_mystery(selected_data)

