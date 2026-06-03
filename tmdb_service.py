import httpx
import time
import os
from fastapi import HTTPException
from dotenv import load_dotenv
from models import SearchResponse
from helpers import parse_result, parse_details, _verify_response
import asyncio

load_dotenv()

CACHE_TTL_SECONDS = 36000

trending_cache = {"data": None, "last_fetched": 0.0}
popular_cache = {"data": None, "last_fetched": 0.0}


# Search using query
async def search_by_multi(client: httpx.AsyncClient, q, include_adult, page):
    params = {
        "api_key": os.getenv("TMDB_API_KEY"),
        "query": q,
        "include_adult": str(include_adult).lower(),
        "page": page,
    }

    try:
        response = await client.get(
            f"{os.getenv('TMDB_BASE_URL')}/search/multi",
            params=params,
        )

    except httpx.RequestError as e:
        print(f"🚨 Network Error: {e}")
        raise HTTPException(status_code=503, detail="Network Error!.")

    _verify_response(response)

    data = response.json()

    return SearchResponse(
        query=q,
        page=data.get("page", 1),
        total_results=data.get("total_results", 0),
        total_pages=data.get("total_pages", 0),
        results=[parse_result(item) for item in data.get("results", [])],
    )


# Get details of a Movie/TVs
async def get_media_details(client: httpx.AsyncClient, media_type, id):
    api_key = os.getenv("TMDB_API_KEY")
    url = (
        f"{os.getenv('TMDB_BASE_URL')}/{media_type}/{id}"
        f"?api_key={api_key}"
        "&append_to_response=credits%2Cvideos%2Cwatch%2Fproviders"
        "&language=en-US"
    )

    try:
        response = await client.get(url)
        _verify_response(response)
    except httpx.RequestError as e:
        print(f"🚨 Network Error: {e}")
        raise HTTPException(status_code=503, detail="Network Error!.")

    data = response.json()

    return parse_details(data)


# Get Trending Movies/TVs
async def get_trending_today(client: httpx.AsyncClient):

    params = {
        "api_key": os.getenv("TMDB_API_KEY"),
    }
    current_time = time.time()

    if trending_cache["data"] and (
        current_time - trending_cache["last_fetched"] < CACHE_TTL_SECONDS
    ):
        print("Trending data from cache!")
        return trending_cache["data"]

    else:
        try:
            response = await client.get(
                f"{os.getenv('TMDB_BASE_URL')}/trending/all/day",
                params=params,
            )

        except httpx.RequestError as e:
            print(f"🚨 Network Error: {e}")
            raise HTTPException(status_code=503, detail="Network Error!.")

        _verify_response(response)

        data = response.json()
        data = [parse_result(item) for item in data.get("results", [])[:10]]
        trending_cache["data"] = data
        trending_cache["last_fetched"] = current_time
        return data


async def fetch_tmdb_from_imdb(client: httpx.AsyncClient, imdb_id):
    """
    Takes an IMDb ID, queries the TMDB /find endpoint, and returns a parsed MediaResult.
    """

    url = f"{os.getenv('TMDB_BASE_URL')}/find/{imdb_id}"
    params = {"api_key": os.getenv("TMDB_API_KEY"), "external_source": "imdb_id"}

    try:
        response = await client.get(url, params=params)
        _verify_response(response)
    except httpx.RequestError as e:
        print(f"🚨 Network error fetching {imdb_id}: {e}")
        return None

    data = response.json()

    # Check if movie or TV
    # add the media_type manually for when missing

    if data.get("movie_results") and len(data["movie_results"]) > 0:
        raw_item = data["movie_results"][0]
        raw_item["media_type"] = "movie"
        return parse_result(raw_item)

    elif data.get("tv_results") and len(data["tv_results"]) > 0:
        raw_item = data["tv_results"][0]
        raw_item["media_type"] = "tv"
        return parse_result(raw_item)

    return None


async def get_tmdb_popular(client: httpx.AsyncClient):
    current_time = time.time()

    if popular_cache["data"] and (
        current_time - popular_cache["last_fetched"] < CACHE_TTL_SECONDS
    ):
        print("Serving from cache!")
        return popular_cache["data"]

    params = {
        "api_key": os.getenv("TMDB_API_KEY"),
        "language": "en-US",
        "page": 1,
        "sort_by": "popularity.desc",
    }
    url_tv = f"{os.getenv('TMDB_BASE_URL')}/discover/tv"
    url_movie = f"{os.getenv('TMDB_BASE_URL')}/discover/movie"
    urls = [
        get_both_popular_results(client, url_tv, params),
        get_both_popular_results(client, url_movie, params),
    ]

    results = await asyncio.gather(*urls)

    formatted_popular = []
    for index, item in enumerate(results):
        current_media_type = "tv" if index == 0 else "movie"

        results_list = item.get("results", [])

        first_five = results_list[:5]

        # Append each item to our new list
        for item in first_five:
            item["media_type"] = current_media_type

            formatted_popular.append(parse_result(item))

    # Sort the final list by the 'popularity' key in descending order
    formatted_popular.sort(
        key=lambda item: (
            item.popularity if item.popularity is not None else float("-inf")
        ),
        reverse=True,
    )
    popular_cache["data"] = formatted_popular
    popular_cache["last_fetched"] = current_time
    return formatted_popular


async def get_both_popular_results(client, url, params):
    try:
        response = await client.get(url, params=params)
        _verify_response(response)
    except httpx.RequestError as e:
        print(f"🚨 Network error fetching : {e}")
        return None

    data = response.json()
    return data


# Get Similar TV/Movies


async def get_similar(client: httpx.AsyncClient, media_type, id):
    api_key = os.getenv("TMDB_API_KEY")
    url = (
        f"{os.getenv('TMDB_BASE_URL')}/{media_type}/{id}/similar"
        f"?api_key={api_key}"
        "&language=en-US"
    )

    try:
        response = await client.get(url)
        _verify_response(response)
    except httpx.RequestError as e:
        print(f"🚨 Network Error: {e}")
        raise HTTPException(status_code=503, detail="Network Error!.")

    data = response.json()

    results = data.get("results", [])
    for item in results:
        item["media_type"] = media_type
    return [parse_result(item) for item in results]
