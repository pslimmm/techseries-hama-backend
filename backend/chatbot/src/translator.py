import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

model = None

if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel(GEMINI_MODEL)

def translate_text(text: str, target_language: str) -> str:
    global model
    prompt = (
        f"Translate the following text into {target_language}. "
        "Keep structure (headings, lists) where possible. "
        "Do not add commentary.\n\n"
        f"TEXT:\n{text}"
    )
    if model is None:
        return "[DEBUG] No GOOGLE_API_KEY. Would translate to: " + target_language + "\n\n" + text[:1500]
    resp = model.generate_content(prompt)
    try:
        return resp.text.strip() if hasattr(resp, "text") and resp.text else ""
    except Exception:
        try:
            return resp.candidates[0].content.parts[0].text
        except Exception:
            return ""

def answer_from_context(system_prompt: str, user_prompt: str) -> str:
    global model
    if model is None:
        return "[DEBUG] No GOOGLE_API_KEY. Would answer with system+user prompts."
    prompt = system_prompt + "\n\n" + user_prompt
    resp = model.generate_content(prompt)
    try:
        return resp.text.strip() if hasattr(resp, "text") and resp.text else ""
    except Exception:
        try:
            return resp.candidates[0].content.parts[0].text
        except Exception:
            return ""
