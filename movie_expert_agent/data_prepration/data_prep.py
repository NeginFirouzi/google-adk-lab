import pandas as pd
import ast
from pathlib import Path

MOVIES_METADATA = "movies_metadata.csv"
CREDITS = "credits.csv"
OUT = "movies_simple.csv"

def safe_eval(x):
    try:
        return ast.literal_eval(x) if pd.notna(x) else []
    except Exception:
        try:
            return eval(x) if isinstance(x, str) else []
        except Exception:
            return []

def get_year(release_date):
    try:
        if not release_date or pd.isna(release_date):
            return None
        return int(str(release_date)[:4])
    except Exception:
        return None

def extract_director(crew_list):
    for member in crew_list:
        if isinstance(member, dict) and member.get("job") == "Director":
            return member.get("name")
    return None

def normalize_id_series(s):
    """Return string ids with .0 trimmed and whitespace removed."""
    s = s.astype(str).str.strip()
    # remove trailing .0 for numeric strings like "1234.0"
    s = s.str.replace(r'\.0+$', '', regex=True)
    # remove surrounding quotes if any
    s = s.str.replace(r'^"|"$', '', regex=True)
    return s

def try_merge(meta, credits):
    # find id-like column names
    if 'id' in meta.columns:
        meta['id_norm'] = normalize_id_series(meta['id'])
    elif 'movie_id' in meta.columns:
        meta['id_norm'] = normalize_id_series(meta['movie_id'])
    else:
        meta['id_norm'] = normalize_id_series(meta.index.astype(str))

    if 'id' in credits.columns:
        credits['id_norm'] = normalize_id_series(credits['id'])
    elif 'movie_id' in credits.columns:
        credits['id_norm'] = normalize_id_series(credits['movie_id'])
    else:
        credits['id_norm'] = normalize_id_series(credits.index.astype(str))

    # try merging on normalized id
    merged = pd.merge(meta, credits, left_on='id_norm', right_on='id_norm', how='left', suffixes=('_meta', '_credits'))

    sample_col = 'crew' if 'crew' in credits.columns else (credits.columns[0] if len(credits.columns)>0 else None)
    if sample_col and merged[sample_col].isna().mean() > 0.30:
        meta['title_clean'] = meta['title'].astype(str).str.strip().str.lower()
        credits['title_clean'] = credits['title'].astype(str).str.strip().str.lower() if 'title' in credits.columns else credits.get('movie_name', pd.Series(['']*len(credits))).astype(str).str.strip().str.lower()
        merged2 = pd.merge(meta, credits, left_on='title_clean', right_on='title_clean', how='left', suffixes=('_meta', '_credits'))
        if merged2[sample_col].isna().mean() < merged[sample_col].isna().mean():
            merged = merged2
    return merged

def main():
    p_meta = Path(MOVIES_METADATA)
    p_credits = Path(CREDITS)
    if not p_meta.exists() or not p_credits.exists():
        raise FileNotFoundError("Make sure movies_metadata.csv and credits.csv are in the working directory.")

    meta = pd.read_csv(MOVIES_METADATA, low_memory=False)
    credits = pd.read_csv(CREDITS, low_memory=False)

    merged = try_merge(meta, credits)

    rows = []
    for _, r in merged.iterrows():
        title = r.get('title') or r.get('original_title') or ''
        if not title or pd.isna(title):
            continue

        # parse genres
        genres_raw = r.get('genres') or r.get('genres_meta') or '[]'
        genres = safe_eval(genres_raw)
        # genres may be list of dicts or a comma string
        if isinstance(genres, list):
            genre_names = ", ".join([g.get('name') for g in genres if isinstance(g, dict) and g.get('name')])
        else:
            genre_names = str(genres)

        overview = r.get('overview') if r.get('overview') and not pd.isna(r.get('overview')) else ''
        try:
            rating = float(r.get('vote_average') if 'vote_average' in r and pd.notna(r.get('vote_average')) else r.get('rating') or 0.0)
        except Exception:
            rating = 0.0

        year = get_year(r.get('release_date') or r.get('release_date_meta') or r.get('release_date_credits'))

        # cast and crew parsing
        cast_list = safe_eval(r.get('cast') or r.get('cast_credits') or '[]')
        cast_names = []
        if isinstance(cast_list, list):
            for c in cast_list[:3]:
                if isinstance(c, dict) and c.get('name'):
                    cast_names.append(c.get('name'))
                elif isinstance(c, str):
                    cast_names.append(c)
        crew_list = safe_eval(r.get('crew') or r.get('crew_credits') or '[]')
        director = extract_director(crew_list) or r.get('director') or ""

        rows.append({
            "title": str(title).strip(),
            "genre": genre_names,
            "rating": round(rating, 1) if rating else 0.0,
            "year": year or "",
            "director": director or "",
            "cast": "|".join(cast_names),
            "overview": str(overview).replace("\n"," ").strip()
        })

    out_df = pd.DataFrame(rows).drop_duplicates(subset=["title"])
    out_df.to_csv(OUT, index=False)
    print(f"Wrote {len(out_df)} rows to {OUT}")

if __name__ == "__main__":
    main()
