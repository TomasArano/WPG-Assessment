import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.orchestration.pipelines import (
    Orchestrator, 
    ArithmeticService, 
    ListenerService,
    track_performance
)

# --- 1. Test the Performance Tracker ---
@pytest.mark.asyncio
async def test_performance_tracking_decorator():
    """Test that the timing decorator captures wall-clock and CPU times."""
    
    @track_performance
    async def dummy_task(payload: dict):
        return {"status": "success"}

    response = await dummy_task({})
    
    assert response["data"]["status"] == "success"
    assert "wall_clock_ms" in response
    assert "execution_cpu_ms" in response
    assert response["error"] is None

# --- 2. Test the Arithmetic Shell Service ---
@pytest.mark.asyncio
@patch("asyncio.create_subprocess_shell")
async def test_arithmetic_service_success(mock_shell):
    """Test the arithmetic service safely executes shell commands and returns floats."""
    # Arrange: Mock the shell subprocess
    mock_process = AsyncMock()
    mock_process.communicate.return_value = (b"42.5\n", b"")
    mock_process.returncode = 0
    mock_shell.return_value = mock_process

    service = ArithmeticService()
    
    # Act
    result = await service.execute({"expression": "20.0 + 22.5"})
    
    # Assert
    assert result["result"] == 42.5
    mock_shell.assert_called_once()

@pytest.mark.asyncio
@patch("asyncio.create_subprocess_shell")
async def test_arithmetic_service_graceful_failure(mock_shell):
    """Test that shell errors are caught and handled graciously."""
    mock_process = AsyncMock()
    mock_process.communicate.return_value = (b"", b"SyntaxError: invalid syntax\n")
    mock_process.returncode = 1
    mock_shell.return_value = mock_process

    service = ArithmeticService()
    result = await service.execute({"expression": "invalid_math"})
    
    assert "error" in result
    assert "SyntaxError" in result["error"]

# --- 3. Test the Orchestrator Routing & Chaining ---
@pytest.mark.asyncio
async def test_orchestrator_process_chaining():
    """Test that the Orchestrator can pass outputs from one pipeline to the next."""
    # Arrange: Mock the listener to return exactly 3 mock events
    mock_listener = AsyncMock()
    mock_listener.pull_events.return_value = ["event1", "event2", "event3"]
    
    # We use our real ArithmeticService but mock the shell for safety
    service_a = ListenerService(listener=mock_listener)
    service_b = ArithmeticService()
    
    orchestrator = Orchestrator(services={"listener": service_a, "math": service_b})
    
    # Act: The heuristic instructs the orchestrator to run 'listener', 
    # then pass the event count into a 'math' expression.
    request_payload = {
        "tenant_id": "tenant_1",
        "steps": ["listener", "math"],
        # The math step will replace {event_count} with the output from the listener step
        "expression_template": "{event_count} * 3.14" 
    }
    
    with patch("asyncio.create_subprocess_shell") as mock_shell:
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"9.42\n", b"") # 3 * 3.14
        mock_process.returncode = 0
        mock_shell.return_value = mock_process

        response = await orchestrator.process_request(request_payload)

    # Assert
    assert response["error"] is None
    # Verify the chained pipeline output
    assert response["data"]["final_result"]["result"] == 9.42
    # Verify timings exist
    assert response["wall_clock_ms"] > 0