"""Afterglow API: content-based movie recommendations over a TF-IDF matrix.

Run:  uvicorn main:app --reload
Docs: http://127.0.0.1:8000/docs
"""
import asyncio
import os
import pickle
import re
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv(".env")
load_dotenv("_env")  # your upload is named "_env"; either filename works

DATA_DIR = Path(os.getenv("DATA_DIR", "."))
TMDB_KEY = (os.getenv("TMDB_API_KEY") or "").strip()
TMDB_SEARCH = "https://api.themoviedb.org/3/search/movie"
TMDB_IMG = "https://image.tmdb.org/t/p/w342"
GENRE_RE = re.compile(r"Science Fiction|TV Movie|\w+")  # genres are stored space-joined

S: dict = {}  # everything loaded at startup lives here


class Movie(BaseModel):
    id: int
    title: str
    tagline: str = ""
    overview: str = ""
    genres: list[str] = []
    rating: float = 0.0
    popularity: float = 0.0
    score: float | None = None  # cosine similarity (0 to 1) when ranked
    poster: str | None = None
    year: int | None = None


class Recommendations(BaseModel):
    anchor: Movie | None = None
    results: list[Movie]


def _load(name: str):
    with open(DATA_DIR / name, "rb") as f:
        return pickle.load(f)


@asynccontextmanager
async def lifespan(app: FastAPI):
    df = _load("df.pkl").reset_index(drop=True)
    df["popularity"] = pd.to_numeric(df["popularity"], errors="coerce").fillna(0.0)
    S.update(
        df=df,
        indices=_load("indicies.pkl"),
        matrix=_load("tdidf_matrix.pkl"),
        tfidf=_load("tfidf.pkl"),
        title_lc=df["title"].str.lower(),
        rating=df["vote_average"].to_numpy(dtype=float),
        popularity=df["popularity"].to_numpy(dtype=float),
        genres=[GENRE_RE.findall(g) for g in df["genres"]],
        client=httpx.AsyncClient(timeout=4.0),
        sem=asyncio.Semaphore(8),
        posters={},
    )
    yield
    await S["client"].aclose()


app = FastAPI(title="Afterglow API", version="1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"], allow_headers=["*"])


# ---------- helpers ----------
def to_movie(i: int, score: float | None = None) -> Movie:
    r = S["df"].iloc[i]
    return Movie(
        id=int(i), title=r["title"], tagline=r["tagline"], overview=r["overview"],
        genres=S["genres"][i], rating=float(r["vote_average"]),
        popularity=float(r["popularity"]), score=score,
    )


async def tmdb_lookup(title: str) -> tuple[str | None, int | None]:
    """Poster URL and release year via TMDB title search. Cached per title."""
    key = title.lower()
    if not TMDB_KEY:
        return None, None
    if key in S["posters"]:
        return S["posters"][key]
    try:
        async with S["sem"]:
            r = await S["client"].get(TMDB_SEARCH, params={"api_key": TMDB_KEY, "query": title})
        r.raise_for_status()
    except httpx.HTTPError:
        return None, None  # transient failure: don't cache, retry next time
    hits = [h for h in r.json().get("results", []) if h.get("poster_path")]
    hit = next((h for h in hits if h["title"].lower() == key), hits[0] if hits else None)
    out = (None, None)
    if hit:
        date = hit.get("release_date") or ""
        out = (TMDB_IMG + hit["poster_path"], int(date[:4]) if date[:4].isdigit() else None)
    S["posters"][key] = out
    return out


async def hydrate(movies: list[Movie]) -> list[Movie]:
    found = await asyncio.gather(*(tmdb_lookup(m.title) for m in movies))
    for m, (poster, year) in zip(movies, found):
        m.poster, m.year = poster, year
    return movies


def top_k(scores, n, exclude=None, min_rating=0.0, genre=None):
    scores = scores.copy()
    keep = S["rating"] >= min_rating
    if genre:
        keep &= np.fromiter((genre in g for g in S["genres"]), bool, len(scores))
    scores[~keep] = -1
    if exclude is not None:
        scores[scores > 0.999] = -1  # identical duplicate rows of the query film
        scores[exclude] = -1
    idx = np.argpartition(-scores, n)[:n]
    idx = idx[np.argsort(-scores[idx])]
    return [(int(i), float(scores[i])) for i in idx if scores[i] > 0]


# ---------- routes ----------
@app.get("/health")
def health():
    return {"status": "ok", "films": len(S["df"]), "tmdb": bool(TMDB_KEY)}


@app.get("/genres", response_model=list[str])
def genres():
    return sorted({g for gs in S["genres"] for g in gs})


@app.get("/search", response_model=list[Movie])
def search(q: str = Query(..., min_length=1), limit: int = Query(8, ge=1, le=25)):
    """Title contains `q`. Prefix matches first, then most popular."""
    q = q.strip().lower()
    ids = np.flatnonzero(S["title_lc"].str.contains(q, regex=False).to_numpy())
    starts = S["title_lc"].iloc[ids].str.startswith(q).to_numpy()
    order = np.lexsort((-S["popularity"][ids], ~starts))
    return [to_movie(int(i)) for i in ids[order][:limit]]


@app.get("/popular", response_model=list[Movie])
async def popular(limit: int = Query(6, ge=1, le=20)):
    """Well-rated, widely seen films: good starting points for a first search."""
    pop = np.where(S["rating"] >= 7, S["popularity"], -1)
    movies = [to_movie(int(i)) for i in np.argsort(-pop)[:limit]]
    return await hydrate(movies)


@app.get("/recommend", response_model=Recommendations)
async def recommend(
    movie_id: int | None = None,
    title: str | None = None,
    top_n: int = Query(10, ge=1, le=50),
    min_rating: float = Query(0.0, ge=0, le=10),
    genre: str | None = None,
):
    """Films closest to one film. Pass `movie_id` (row id from /search) or an exact `title`."""
    if movie_id is None and title:
        hit = S["indices"].get(title)
        if hit is None:
            raise HTTPException(404, f"No film titled '{title}'")
        ids = np.atleast_1d(hit)  # duplicate titles return several ids: take the most popular
        movie_id = int(ids[np.argmax(S["popularity"][ids])])
    if movie_id is None or not 0 <= movie_id < len(S["df"]):
        raise HTTPException(404, "Unknown film id")

    M = S["matrix"]
    scores = (M @ M[movie_id].T).toarray().ravel()  # rows are L2-normalised: dot product = cosine
    ranked = top_k(scores, top_n, exclude=movie_id, min_rating=min_rating, genre=genre)
    movies = await hydrate([to_movie(movie_id)] + [to_movie(i, s) for i, s in ranked])
    return Recommendations(anchor=movies[0], results=movies[1:])


@app.get("/discover", response_model=Recommendations)
async def discover(
    q: str = Query(..., min_length=3, description="Free-text description of the film you want"),
    top_n: int = Query(10, ge=1, le=50),
    min_rating: float = Query(0.0, ge=0, le=10),
    genre: str | None = None,
):
    """Rank films against a free-text description using the fitted TF-IDF vectoriser."""
    clean = re.sub(r"[^a-z\s]", " ", q.lower().replace("'", ""))
    vec = S["tfidf"].transform([clean])
    if vec.nnz == 0:
        return Recommendations(results=[])
    scores = (S["matrix"] @ vec.T).toarray().ravel()
    ranked = top_k(scores, top_n, min_rating=min_rating, genre=genre)
    return Recommendations(results=await hydrate([to_movie(i, s) for i, s in ranked]))
