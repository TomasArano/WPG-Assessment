import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch
from src.orchestration.main import app

# --- Pytest Configuration ---
pytestmark = pytest.mark.asyncio
transport = ASGITransport(app=app)
base_url = "http://testserver"

# --- The Tests ---

async def test_requirement_process_chaining_and_metrics():
    """
    PROVES: 
    1. "Passes outputs from one pipeline to the next (process-chaining)"
    2. "Exposes execution and wall-clock times for each request."
    3. "multi-tenant, system"
    """
    async with AsyncClient(transport=transport, base_url=base_url) as client:
        payload = {
            "tenant_id": "integration_tenant_1",
            "steps": ["listener", "math"],
            "expression_template": "{event_count} * 100"
        }
        
        # FIX: Patch the function directly based on how it was imported in main.py
        with patch("src.orchestration.main.random", return_value=0.9):
            response = await client.post("/agent/act", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "wall_clock_ms" in data
        assert "execution_cpu_ms" in data
        assert data["wall_clock_ms"] > 0
        
        assert data["data"]["final_result"]["event_count"] == 5
        assert data["data"]["final_result"]["result"] == 500.0


async def test_requirement_automatic_fallback():
    """
    PROVES: 
    "automatic fall-back, from another distant Agency "B" in case the first agency 
    becomes temporarily unavailable"
    """
    async with AsyncClient(transport=transport, base_url=base_url) as client:
        payload = {
            "tenant_id": "integration_tenant_2",
            "steps": ["listener"] 
        }
        
        # FIX: Patch the function directly to force a 503 error
        with patch("src.orchestration.main.random", return_value=0.1):
            response = await client.post("/agent/act", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        # Proves it successfully hit Agency B
        assert data["data"]["final_result"]["event_count"] == 3


async def test_requirement_gracious_error_handling():
    """
    PROVES:
    "Handles errors or failures graciously"
    """
    async with AsyncClient(transport=transport, base_url=base_url) as client:
        payload = {
            "tenant_id": "integration_tenant_3",
            "steps": ["math"],
            # FIX: Send the broken string directly to 'expression'
            "expression": "this_is_not_math" 
        }
        
        response = await client.post("/agent/act", json=payload)
        
        assert response.status_code == 400
        data = response.json()
        
        assert "detail" in data
        assert "Step 'math' failed" in data["detail"]