import pytest
from unittest.mock import AsyncMock, MagicMock
import httpx
from datetime import datetime

from src.orchestration.listener import SeismicListener
from src.shared.models import SeismicEvent

@pytest.fixture
def mock_client():
    """Provides a mocked HTTPX AsyncClient."""
    client = MagicMock(spec=httpx.AsyncClient)
    client.get = AsyncMock()
    return client

@pytest.fixture
def listener(mock_client):
    """Provides a configured SeismicListener instance."""
    return SeismicListener(
        http_client=mock_client,
        agency_a_url="http://mock-agency-a.com/events",
        agency_b_url="http://mock-agency-b.com/events"
    )

@pytest.mark.asyncio
async def test_fetch_success_from_agency_a(listener, mock_client):
    """Test that the listener successfully fetches data from Agency A."""
    # Arrange
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = [{
        "eid": 1, "timestamp": "2024-01-01T12:00:00Z", "lat": 45.0, "lon": 90.0,
        "depth": -10.0, "Mw": 5.5, "dist": 100.0, "azi": 45.0, "loclat": 46.0, "loclon": 91.0
    }]
    mock_client.get.return_value = mock_response

    # Act
    events = await listener.pull_events()

    # Assert
    assert len(events) == 1
    assert events[0].eid == 1
    mock_client.get.assert_called_once_with("http://mock-agency-a.com/events", timeout=5.0)

@pytest.mark.asyncio
async def test_fallback_to_agency_b(listener, mock_client):
    """Test that the listener falls back to Agency B if Agency A timeouts."""
    # Arrange
    # First call (Agency A) raises a TimeoutException, Second call (Agency B) succeeds
    mock_response_b = MagicMock()
    mock_response_b.raise_for_status.return_value = None
    mock_response_b.json.return_value = [{
        "eid": 2, "timestamp": "2024-01-01T12:05:00Z", "lat": 45.0, "lon": 90.0,
        "depth": -10.0, "Mw": 5.5, "dist": 100.0, "azi": 45.0, "loclat": 46.0, "loclon": 91.0
    }]
    mock_client.get.side_effect = [httpx.TimeoutException("Timeout"), mock_response_b]

    # Act
    events = await listener.pull_events()

    # Assert
    assert len(events) == 1
    assert events[0].eid == 2
    assert mock_client.get.call_count == 2

@pytest.mark.asyncio
async def test_deduplication(listener, mock_client):
    """Test that duplicate events (already processed EIDs) are ignored."""
    # Arrange
    payload = [{
        "eid": 1, "timestamp": "2024-01-01T12:00:00Z", "lat": 45.0, "lon": 90.0,
        "depth": -10.0, "Mw": 5.5, "dist": 100.0, "azi": 45.0, "loclat": 46.0, "loclon": 91.0
    }]
    mock_response = MagicMock()
    mock_response.json.return_value = payload
    mock_client.get.return_value = mock_response

    # Act
    events_run_1 = await listener.pull_events()
    events_run_2 = await listener.pull_events()

    # Assert
    assert len(events_run_1) == 1
    assert len(events_run_2) == 0  # Should be empty because EID 1 is already in the set