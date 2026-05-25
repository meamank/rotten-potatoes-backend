from pydantic import BaseModel
from typing import Optional
from enum import Enum


class MediaResult(BaseModel):
    id: int
    media_type: str
    title: Optional[str] = None
    overview: Optional[str] = None
    release_date: Optional[str] = None
    first_air_date: Optional[str] = None
    vote_average: Optional[float] = None
    vote_count: Optional[int] = None
    popularity: float
    poster_url: Optional[str] = None
    backdrop_url: Optional[str] = None
    genre_ids: list[int] = []
    original_language: Optional[str] = None


class SearchResponse(BaseModel):
    query: str
    page: int
    total_results: int
    total_pages: int
    results: list[MediaResult]


class Actor(BaseModel):
    id: int
    known_for_department: Optional[str] = None
    name: str
    popularity: float
    profile_path: Optional[str] = None
    character: Optional[str] = None
    order: int


class Crew(BaseModel):
    id: int
    known_for_department: Optional[str] = None
    name: str
    popularity: float
    profile_path: Optional[str] = None
    department: Optional[str] = None
    job: Optional[str] = None


class WatchProviders(BaseModel):
    logo_url: str
    provider_name: str
    display_priority: int


class MediaDetails(BaseModel):
    id: int
    title: Optional[str] = None
    imdb_id: Optional[str] = None
    country: Optional[str] = None
    number_of_episodes: Optional[int] = None
    number_of_seasons: Optional[int] = None
    original_language: Optional[str] = None
    overview: Optional[str] = None
    release_date: Optional[str] = None
    runtime: Optional[int] = None
    tagline: Optional[str] = None
    vote_average: Optional[float] = None
    vote_count: Optional[int] = None
    popularity: float
    poster_url: Optional[str] = None
    backdrop_url: Optional[str] = None
    genre_ids: list[dict] = []
    actors: list[Actor] = []
    crew: list[Crew] = []
    watch: list[WatchProviders] = []


class MediaType(str, Enum):
    movie = "movie"
    tv = "tv"
