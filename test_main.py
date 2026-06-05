import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from models import SearchResponse, MediaResult
from main import app


@pytest.fixture
def client():
    """
    Using a 'with' block forces FastAPI to run the lifespan startup events,
    which creates the request.app.client session!
    """
    with TestClient(app) as test_client:
        yield test_client


def test_root_endpoint(client):
    """Verify the API boots and returns the welcome message."""

    response = client.get("/")

    assert response.status_code == 200

    assert response.json() == {"message": "Welcome to Rotten Potatoes!"}


def test_search_success(client):
    """Verify the /search endpoint returns proper data when TMDB succeeds."""

    # fake data we want our mocked TMDB service to return
    fake_media = MediaResult(
        id=123,
        media_type="movie",
        title="Mocked Batman",
        popularity=100.0,
        genre_ids=[28],
    )
    fake_response = SearchResponse(
        query="batman", page=1, total_results=1, total_pages=1, results=[fake_media]
    )

    with patch("main.search_by_multi", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = fake_response

        response = client.get("/search?q=batman&include_adult=False&page=1")

        assert response.status_code == 200

        data = response.json()

        assert data["query"] == "batman"
        assert len(data["results"]) == 1
        assert data["results"][0]["title"] == "Mocked Batman"

        mock_search.assert_called_once()


def test_rp_rec_endpoint(client):
    """Verify the /rp-rec endpoint returns a list of movies from the sync service."""

    # fake list of movies that cache would normally hold
    fake_movies = [
        MediaResult(
            id=1,
            media_type="movie",
            title="RP Choice 1",
            popularity=99.0,
            genre_ids=[28],
        ),
        MediaResult(
            id=2,
            media_type="movie",
            title="RP Choice 2",
            popularity=88.0,
            genre_ids=[12],
        ),
    ]

    with patch("main.sync_tg_fetch_tmdb", new_callable=AsyncMock) as mock_sync:
        mock_sync.return_value = fake_movies
        response = client.get("/rp-rec")

        assert response.status_code == 200
        data = response.json()

        # Verify it's a list with two items
        assert isinstance(data, list)
        assert len(data) == 2

        # Verify the parsing holds up
        assert data[0]["title"] == "RP Choice 1"
        assert data[1]["id"] == 2

        mock_sync.assert_called_once()
