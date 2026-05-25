import os
from fastapi import HTTPException
import httpx
from models import Actor, Crew, MediaDetails, MediaResult, WatchProviders


def _verify_response(response: httpx.Response):
    """A single source of truth for TMDB error handling."""
    if response.status_code == 401:
        raise HTTPException(status_code=401, detail="Invalid TMDB API key.")
    if response.status_code == 422:
        raise HTTPException(status_code=422, detail="Invalid query parameters.")
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="TMDB API error.")


def build_image_url(path, size="w500"):
    """Return full poster url"""

    return f"{os.getenv('TMDB_IMAGE_BASE')}/{size}{path}" if path else None


def parse_result(item: dict) -> MediaResult:
    """Parse and return formatted Searched Item Response"""
    extracted_title = item.get("title") or item.get("name") or "Unknown Title"
    release_date = item.get("release_date") or item.get("first_air_date") or "NA"

    return MediaResult(
        id=item["id"],
        media_type=item.get("media_type", "unknown"),
        title=extracted_title,
        overview=item.get("overview"),
        release_date=release_date,
        vote_average=item.get("vote_average"),
        vote_count=item.get("vote_count"),
        popularity=item.get("popularity", 0),
        poster_url=build_image_url(item.get("poster_path")),
        backdrop_url=build_image_url(item.get("backdrop_path"), size="w1280"),
        genre_ids=item.get("genre_ids", []),
        original_language=item.get("original_language"),
    )


def parse_details(item: dict) -> MediaDetails:
    """Parse and return formatted individual MOVIE/TV Response"""

    extracted_title = item.get("title") or item.get("name") or "Unknown Title"
    release_date = item.get("release_date") or item.get("first_air_date") or "NA"

    def extract_actor(data: list[dict]) -> list[Actor]:
        """Extract Actors from response and return formatted result"""

        actors = []

        for item in data:
            if item.get("order") <= 5:
                actors.append(
                    Actor(
                        id=item.get("id"),
                        known_for_department=item.get("known_for_department"),
                        name=item.get("name"),
                        popularity=item.get("popularity", 0),
                        profile_path=item.get("profile_path"),
                        character=item.get("character"),
                        order=item.get("order"),
                    )
                )

        return actors

    def extract_crew(data: list[dict]) -> list[Crew]:
        """Extract Crew from response and return formatted result"""

        crew = []

        for item in data:
            if item["known_for_department"] == "Directing":
                crew.append(
                    Crew(
                        id=item.get("id"),
                        known_for_department=item.get("known_for_department"),
                        name=item.get("name"),
                        popularity=item.get("popularity"),
                        profile_path=item.get("profile_path"),
                        department=item.get("department"),
                        job=item.get("job"),
                    )
                )

        return crew[:2]

    def extract_watch_providers(in_data: dict) -> list[WatchProviders]:
        """Extract Watch Providers from the IN region safely"""

        # If the movie isn't available in India at all, return early
        if not in_data:
            return []

        providers = {}

        # A movie might be streaming, free, for rent, or for purchase.
        # We loop through all categories so we don't miss anything.
        for category in ["flatrate", "free", "rent", "buy"]:
            for item in in_data.get(category, []):
                p_name = item.get("provider_name")

                # Prevent duplicates (e.g., Google Play is often in both 'rent' and 'buy')
                if p_name and p_name not in providers:
                    providers[p_name] = WatchProviders(
                        logo_url=item.get("logo_path"),
                        provider_name=p_name,
                        display_priority=item.get("display_priority", 0),
                    )

        # Sort them by priority so the main ones (Netflix/Prime) show up first
        return sorted(providers.values(), key=lambda x: x.display_priority)

    return MediaDetails(
        id=item["id"],
        title=extracted_title,
        imdb_id=item.get("imdb_id"),
        country=item.get("origin_country", [None])[0],
        number_of_episodes=item.get("number_of_episodes"),
        number_of_seasons=item.get("number_of_seasons"),
        original_language=item.get("original_language"),
        overview=item.get("overview"),
        release_date=release_date,
        runtime=item.get("runtime"),
        tagline=item.get("tagline"),
        vote_average=item.get("vote_average"),
        vote_count=item.get("vote_count"),
        popularity=item.get("popularity", 0),
        poster_url=build_image_url(item.get("poster_path")),
        backdrop_url=build_image_url(item.get("backdrop_path"), size="w1280"),
        genre_ids=item.get("genres", []),
        actors=extract_actor(item.get("credits", {}).get("cast", [])),
        crew=extract_crew(item.get("credits", {}).get("crew", [])),
        watch=extract_watch_providers(
            item.get("watch/providers", {}).get("results", {}).get("IN", {})
        ),
    )
