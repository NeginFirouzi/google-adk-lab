import csv
from pathlib import Path
import os
import difflib
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MOVIE_DATABASE = {}

def load_movies(csv_path="movie_expert_agent/movies_simple.csv"):
    global MOVIE_DATABASE
    MOVIE_DATABASE = {}
    p = Path(csv_path)
    if not p.exists():
        raise FileNotFoundError(f"{csv_path} not found. Run data_prep.py first.")
    with p.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            title = r["title"].strip()
            MOVIE_DATABASE[title] = {
                "genre": r.get("genre",""),
                "rating": float(r.get("rating") or 0.0),
                "year": int(r.get("year")) if r.get("year") else None,
                "director": r.get("director",""),
                "cast": r.get("cast","").split("|") if r.get("cast") else [],
                "overview": r.get("overview",""),
            }

# auto-load on import
try:
    load_movies()
except Exception:
    MOVIE_DATABASE = {}

def fuzzy_title_lookup(name, cutoff=0.6):
    names = list(MOVIE_DATABASE.keys())
    if not names:
        return []
    return difflib.get_close_matches(name, names, n=5, cutoff=cutoff)

def call_local_openai_llm(
    prompt: str,
    model: str = "gpt-4o-mini",
    max_tokens: int = 300,
    temperature: float = 0.2
) -> str:
    """
    Minimal direct call to the OpenAI Chat Completions API.
    """
    if not client.api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable not set")

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content":
                    "You are a concise, factual movie trivia assistant. Only provide facts you are reasonably certain about. "
                    "If you are unsure, say 'I might be mistaken' and avoid fabricating details. "
                    "When possible, add a short provenance like 'source: IMDB'."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"❌ Error calling OpenAI API: {e}"