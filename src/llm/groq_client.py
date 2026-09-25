from __future__ import annotations
import os
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

def get_groq_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY is not set. Add it to the project .env file or set it in the shell environment.")

    return Groq(api_key=api_key)

def generate_response(prompt:str, model: str = "openai/gpt-oss-20b", temptemperature: float = 0.2) -> str:
    if not prompt or not prompt.strip():
        raise ValueError("Prompt can't be empty.")

    client = get_groq_client()
    response = client.chat.completions.create(
        model = model,
        messages=[
            {
                "role" : "user",
                "content":prompt
            }
        ],
        temperature=temptemperature
    )
    return response.choices[0].message.content.strip()