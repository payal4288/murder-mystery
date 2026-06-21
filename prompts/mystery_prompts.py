"""
Prompt templates for Gemini AI mystery generation.

All prompts are stored as string constants here to keep
prompt engineering isolated from application logic.
"""

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
