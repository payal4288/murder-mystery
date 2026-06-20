import os
import logging
from google import genai
from google.genai import types
from dotenv import load_dotenv
from models.mystery import Mystery
from prompts.mystery_prompts import SYSTEM_PROMPT, GENERATION_PROMPT

# Set up logging to console
logging.basicConfig(level=logging.INFO)

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
print("debug: load_dotenv returned, api_key =", api_key[:10] if api_key else "None")

if api_key:
    client = genai.Client(api_key=api_key)
    prompt = GENERATION_PROMPT.replace("{theme_seed}", "art forgery")
    
    # Test 1: gemini-2.5-flash with 8192 tokens
    try:
        print("\nTesting gemini-2.5-flash with max_output_tokens=8192...")
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.9,
                max_output_tokens=8192,
                response_mime_type="application/json",
                response_schema=Mystery,
            ),
        )
        print("Success gemini-2.5-flash!")
        print(f"Length: {len(response.text)}")
    except Exception as e:
        print("Error gemini-2.5-flash:")
        print(e)

    # Test 2: gemini-flash-latest (1.5-flash) with 8192 tokens
    try:
        print("\nTesting gemini-flash-latest with max_output_tokens=8192...")
        response = client.models.generate_content(
            model="gemini-flash-latest",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.9,
                max_output_tokens=8192,
                response_mime_type="application/json",
                response_schema=Mystery,
            ),
        )
        print("Success gemini-flash-latest!")
        print(f"Length: {len(response.text)}")
    except Exception as e:
        print("Error gemini-flash-latest:")
        print(e)

    # Test 3: offline mock mysteries validation
    try:
        print("\nTesting generate_mock_mystery and validate_mystery...")
        from services.gemini_service import generate_mock_mystery, MOCK_MYSTERIES
        for i in range(len(MOCK_MYSTERIES)):
            mock_mystery = generate_mock_mystery(theme="art" if i == 0 else "wine")
            print(f"Success validating mock mystery {i+1}: {mock_mystery.victim_name}")
    except Exception as e:
        print("Error validating mock mysteries:")
        print(e)

