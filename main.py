from fastapi import FastAPI, Request, Query
from httpx import AsyncClient
from contextlib import asynccontextmanager
from tmdb_service import (
    search_by_multi,
    get_media_details,
    get_trending_today,
    get_tmdb_popular,
    get_similar,
)
from telegram_service import sync_tg_fetch_tmdb
from models import MediaDetails, SearchResponse, MediaType, MediaResult
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.client = AsyncClient()
    yield
    await app.client.aclose()


app = FastAPI(lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Welcome to Rotten Potatoes!"}


@app.get("/search", response_model=SearchResponse)
async def search(
    request: Request,
    q: str = Query(..., min_length=1),
    include_adult: bool = Query(False),
    page: int = Query(1, ge=1),
):
    """Search using your query."""

    return await search_by_multi(request.app.client, q, include_adult, page)


@app.get("/details/{media_type}/{id}", response_model=MediaDetails)
async def get_details(request: Request, media_type: MediaType, id: int):
    """Get selected Movie/Tv details"""
    return await get_media_details(request.app.client, media_type.value, id)


@app.get("/trending", response_model=list[MediaResult])
async def get_trending(request: Request):
    """Get Today's Trending Movie/Tv"""
    return await get_trending_today(request.app.client)


@app.get("/rp-rec", response_model=list[MediaResult])
async def get_rp_rec(request: Request):
    """
    rp-rec = Rotten Potatoes own recommendations
    """
    return await sync_tg_fetch_tmdb(request.app.client)


@app.get("/popular", response_model=list[MediaResult])
async def get_popular(request: Request):
    return await get_tmdb_popular(request.app.client)


@app.get("/similar/{media_type}/{id}", response_model=list[MediaResult])
async def get_similar_results(request: Request, media_type: MediaType, id: int):
    """Get Similar TV/Movies"""
    return await get_similar(request.app.client, media_type.value, id)
