import os
import requests
from dotenv import load_dotenv
from config import API_MODEL

load_dotenv()

# --- Model Selection Logic ---
# OpenRouter API Key and URL (Commented)
API_KEY = os.getenv("OPENROUTER_API_KEY")
URL = "https://openrouter.ai/api/v1/chat/completions"

# Groq API Key and URL
# API_KEY = os.getenv("GROQ_API_KEY")
# URL = "https://api.groq.com/openai/v1/chat/completions"

import time

def generate_api(system_prompt, user_prompt):
    max_retries = 3
    retry_delay = 1 # Groq is faster but still manage rate limits
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    combined_prompt = f"### System Instructions:\n{system_prompt}\n\n### User Prompt:\n{user_prompt}"

    payload = {
        "model": API_MODEL,
        "messages": [
            {"role": "user", "content": combined_prompt}
        ],
        "temperature": 0.7
    }

    for attempt in range(max_retries):
        try:
            # Pacing
            time.sleep(retry_delay)
            
            response = requests.post(URL, headers=headers, json=payload, timeout=60)
            
            if response.status_code == 429:
                print(f"[API] Rate limited (429). Retrying in {retry_delay*5}s...")
                time.sleep(retry_delay * 5)
                continue
                
            if response.status_code != 200:
                raise Exception(f"API returned error {response.status_code}: {response.text}")

            data = response.json()
            if "choices" not in data:
                raise KeyError(f"Unexpected API response format: {data}")

            return data["choices"][0]["message"]["content"]
            
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            print(f"[API] Error: {e}. Retrying...")
            time.sleep(2)