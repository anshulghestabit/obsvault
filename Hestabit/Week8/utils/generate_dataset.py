import json
import requests
from tqdm import tqdm

API_URL = "https://api.openai.com/v1/chat/completions"
API_KEY = "YOUR_API_KEY"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

PROMPT = """
Generate a coding instruction dataset example.

Return JSON with keys:
instruction
input
output

Types must include:
1) QA about programming
2) reasoning/debugging
3) code extraction

Example format:
{"instruction":"...","input":"...","output":"..."}

Return only JSON.
"""

def generate_sample():
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role":"system","content":"You generate high-quality coding instruction datasets."},
            {"role":"user","content":PROMPT}
        ],
        "temperature":0.7
    }

    r = requests.post(API_URL,headers=HEADERS,json=payload)
    text = r.json()["choices"][0]["message"]["content"]

    try:
        data=json.loads(text)
        return data
    except:
        return None


OUTPUT_FILE="data/raw/coding_dataset.jsonl"

def main():
    samples=[]
    for _ in tqdm(range(1200)):
        sample=generate_sample()
        if sample:
            samples.append(sample)

    with open(OUTPUT_FILE,"w") as f:
        for s in samples:
            f.write(json.dumps(s)+"\n")

    print("Saved",len(samples),"samples")


if __name__=="__main__":
    main()