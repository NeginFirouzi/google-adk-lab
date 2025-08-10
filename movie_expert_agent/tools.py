from .utils import MOVIE_DATABASE, load_movies, call_local_openai_llm, fuzzy_title_lookup
from typing import Optional
import random

# ensure loaded
if not MOVIE_DATABASE:
    try:
        load_movies()
    except Exception:
        pass

MOOD_MAP = {
    "romantic": ["Romance", "Drama", "Comedy"],
    "funny": ["Comedy", "Family"],
    "action": ["Action", "Adventure", "Thriller"],
    "mind-bending": ["Sci-Fi", "Mystery", "Thriller", "Fantasy"],
    "scary": ["Horror", "Thriller", "Mystery"],
    "adventurous": ["Adventure", "Action", "Fantasy"],
    "feel-good": ["Comedy", "Family", "Romance"],
    "dramatic": ["Drama"],
    "inspirational": ["Biography", "Drama", "Documentary"],
}

def recommend_movie(genre: Optional[str] = None, mood: Optional[str] = None) -> str:
    """Recommend 1-3 comedy movies with playful explanations, prioritizing high ratings with randomness."""
    candidates = []
    genre_q = (genre or "").lower().strip()
    mood_candidates = MOOD_MAP.get(mood.lower(), []) if mood else []
    
    for title, data in MOVIE_DATABASE.items():
        g = data.get("genre", "").lower()
        rating = data.get("rating", 0)
        
        # Quality filter - only consider well-rated comedies
        if rating < 7.0 and genre_q not in g:
            continue
        
        genre_ok = (not genre_q) or (genre_q in g)
        mood_ok = not mood_candidates or any(mc.lower() in g for mc in mood_candidates)
        
        if genre_ok and mood_ok:
            # Prioritize movies with multiple genres
            genre_bonus = 1.5 if len(data.get("genre", "").split(",")) > 1 else 0
            candidates.append((title, data, rating + genre_bonus + random.uniform(0, 0.5)))
    
    if not candidates:
        return "Hmm, I couldn't find a match — want to try a different mood or genre? 🎬"
    
    # Weighted selection
    candidates.sort(key=lambda x: x[2], reverse=True)
    top_tier = [c for c in candidates if c[2] >= 8.0][:15] or candidates[:10]
    
    # Select 1-3 unique recommendations
    selected_titles = set()
    selected_movies = []
    while len(selected_movies) < min(3, len(top_tier)) and top_tier:
        movie = random.choice(top_tier)
        title = movie[0]
        if title not in selected_titles:
            selected_titles.add(title)
            selected_movies.append(movie)
        top_tier.remove(movie)
    
    # Build responses
    replies = []
    for movie in selected_movies:
        title, data, _ = movie
        director = data.get('director', 'unknown')
        year = data.get('year', '?')
        rating = data.get('rating', '?')
        
        # Clean title formatting
        clean_title = title.strip()
        if clean_title.startswith(("'", '"')) and clean_title.endswith(("'", '"')):
            clean_title = clean_title[1:-1]
                
        replies.append(f"🎬 {clean_title} directed by {director} ,({year}) | Rating: {rating}/10")
        
    return "Here are some fresh picks:\n" + "\n".join(replies) + "\nEnjoy the show! 🍿"

def compare_movies(movie1: str, movie2: str) -> str:
    """Playful comparison that never declares a single winner."""
    m1 = MOVIE_DATABASE.get(movie1)
    m2 = MOVIE_DATABASE.get(movie2)

    # try fuzzy lookup if direct not found
    if not m1:
        m1_matches = fuzzy_title_lookup(movie1)
        if m1_matches:
            m1 = MOVIE_DATABASE[m1_matches[0]]
            movie1 = m1_matches[0]
    if not m2:
        m2_matches = fuzzy_title_lookup(movie2)
        if m2_matches:
            m2 = MOVIE_DATABASE[m2_matches[0]]
            movie2 = m2_matches[0]

    if not m1 or not m2:
        missing = movie1 if not m1 else movie2
        return f"⚠️ I couldn't find *{missing}* in my dataset — maybe try a slightly different title?"

    lines = [
        f"🎬 Which to watch? A cheeky comparison:",
        f"• {movie1} — {m1.get('genre')} • {m1.get('rating')}/10 • dir: {m1.get('director')}",
        f"• {movie2} — {m2.get('genre')} • {m2.get('rating')}/10 • dir: {m2.get('director')}",
        ""
    ]

    # playful difference highlights
    if m1.get('rating') != m2.get('rating'):
        higher = movie1 if m1.get('rating') > m2.get('rating') else movie2
        lines.append(f"📊 By ratings, {higher} edges ahead — but does that match your vibe? Depends on your mood! 😉")
    else:
        lines.append("⭐ Both score similarly — taste decides, not me!")

    # director connection
    if m1.get('director') and m1.get('director') == m2.get('director'):
        lines.append(f"Fun fact: both are by {m1.get('director')} — double signature style!")

    lines.append("\nWant a tie-breaker? Tell me your mood and I'll pick!")
    return "\n".join(lines)

def movie_info(movie_title: str) -> str:
    """
    Provide a compact 'about' summary: year, genre, director, cast, rating, short overview.
    """
    if not movie_title:
        return "Tell me which film you'd like to know about."

    title = movie_title.strip()
    m = MOVIE_DATABASE.get(title)
    if not m:
        matches = fuzzy_title_lookup(title)
        if matches:
            title = matches[0]
            m = MOVIE_DATABASE.get(title)

    if not m:
        return f"Sorry, I couldn't find '{movie_title}' in my database — try another title or add it to movies_simple.csv."

    genre = m.get("genre","N/A")
    year = m.get("year","?")
    director = m.get("director","Unknown")
    rating = m.get("rating","?")
    cast = ", ".join(m.get("cast",[])[:4]) if m.get("cast") else "N/A"
    overview = m.get("overview","No summary available.")[:500]
    return (f"🎬 '{title}' ({year}) — {genre}\n"
            f"Directed by: {director}\n"
            f"Main cast: {cast}\n"
            f"Rating: {rating}/10\n\n"
            f"Quick Summary: {overview}\n"
            f"Want trivia? Say 'tell me a trivia about {title}' 🔮")

def movie_trivia(title: str) -> str:
    prompt = f"Provide one surprising, factual, and verifiable piece of trivia about the movie '{title}'. " \
             f"Make it sound playful but accurate. Include a short source reference if possible."
    trivia = call_local_openai_llm(prompt)
    return f"🎬 Here's a juicy secret about '{title}': {trivia}"
