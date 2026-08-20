import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
model_name = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")

# init client
client = None
if api_key:
    client = genai.Client(api_key=api_key)

def load_system_prompt():
    prompt_path = os.path.join(os.path.dirname(__file__), "SYSTEM_PROMPT.md")
    if os.path.exists(prompt_path):
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()
    return "You are Zara, sales assistant for Northstar Homes (Northstar One, Sector 79 Gurugram)."

SYSTEM_INSTRUCTION = load_system_prompt()

def get_agent_response(history: list) -> str:
    """
    history is a list of dicts: [{"role": "user"|"model", "text": "..."}]
    """
    if not client:
        return "LLM API key is missing. Please set GEMINI_API_KEY in your .env file."
    
    contents = []
    for turn in history:
        role = "user" if turn["role"] == "user" else "model"
        contents.append(
            types.Content(
                role=role,
                parts=[types.Part.from_text(text=turn["text"])]
            )
        )
    
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                max_output_tokens=1000
            )
        )
        if response.candidates:
            print(f"DEBUG - Finish Reason: {response.candidates[0].finish_reason}")
        return response.text.strip()
    except Exception as e:
        print(f"Error calling Gemini: {e}")
        return "I'm having a little trouble connecting to my system right now. Could you please say that again?"

def extract_analytics(conversation_history: list) -> dict:
    """
    Runs a second pass over the transcript to extract lead attributes and key metrics.
    """
    if not client or not conversation_history:
        return {
            "budget_mentioned": None,
            "configuration_interest": "undecided",
            "interest_level": "cold",
            "site_visit_status": "not requested",
            "follow_up_required": False,
            "preferred_language": "English",
            "objections_raised": [],
            "opted_out": False,
            "summary": "No transcript available."
        }

    # format readable transcript for analytics prompt
    transcript = ""
    for msg in conversation_history:
        speaker = "Customer" if msg["role"] == "user" else "Zara"
        transcript += f"{speaker}: {msg['text']}\n"

    prompt = f"""
Analyze the following sales conversation transcript between a real estate customer and sales agent Zara (Northstar Homes).
Extract structured insights in strict JSON format.

TRANSCRIPT:
{transcript}

Return ONLY valid JSON matching this exact structure:
{{
  "budget_mentioned": "<string range or null if not stated>",
  "configuration_interest": "<'2BHK' | '3BHK' | 'undecided'>",
  "interest_level": "<'hot' | 'warm' | 'cold'>",
  "site_visit_status": "<'booked' | 'failed' | 'not requested'>",
  "follow_up_required": <true | false>,
  "preferred_language": "<'English' | 'Hindi' | 'Hinglish'>",
  "objections_raised": ["<short string description of any objections like price, location, etc.>"],
  "opted_out": <true | false>,
  "summary": "<1-2 concise sentences summarizing buyer intent and current stage>"
}}
"""

    try:
        res = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.1
            )
        )
        data = json.loads(res.text.strip())
        return data
    except Exception as e:
        print(f"Analytics extraction failed: {e}")
        return {
            "budget_mentioned": None,
            "configuration_interest": "undecided",
            "interest_level": "warm",
            "site_visit_status": "not requested",
            "follow_up_required": True,
            "preferred_language": "English",
            "objections_raised": [],
            "opted_out": False,
            "summary": "Analytics extraction error fallback."
        }

def detect_booking_intent(message: str) -> bool:
    """
    Uses the LLM to detect if the user is trying to book a site visit,
    handling English, Hindi, and Hinglish naturally.
    """
    if not client:
        return False
        
    prompt = f"""
    Analyze the following message sent by a customer to a real estate agent.
    Does the user express a clear intent to schedule, book, or confirm a site visit / property tour?
    Consider English, Hindi, and Hinglish (e.g., "dekhne aana hai", "site visit karni hai").
    
    Reply with exactly one word: YES or NO.
    
    Message: "{message}"
    """
    
    try:
        # We use temperature 0.0 because we want a strict classification, not creativity
        res = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.0)
        )
        # Check if the model replied with YES
        return "YES" in res.text.strip().upper()
    except Exception as e:
        print(f"Intent detection failed: {e}")
        return False