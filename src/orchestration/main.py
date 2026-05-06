import asyncio
import datetime
from random import  random, randint
from datetime import timezone
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any

from src.orchestration.listener import SeismicListener
from src.orchestration.pipelines import Orchestrator, ArithmeticService, ListenerService

# --- Configuration ---
POLL_INTERVAL_MINUTES = 5  # The "m" minutes variable
AGENCY_A = "http://127.0.0.1:8000/mock-agency-a" 
AGENCY_B = "http://127.0.0.1:8000/mock-agency-b"

# --- Global State ---
http_client = httpx.AsyncClient()
listener = SeismicListener(http_client, AGENCY_A, AGENCY_B)

# Wire up the Orchestrator
services = {
    "listener": ListenerService(listener),
    "math": ArithmeticService()
}
orchestrator = Orchestrator(services)

# --- Background Task (Task 1) ---
async def scheduled_polling():
    """Pulls real-time data every 'm' minutes."""
    while True:
        try:
            print(f"--- Running scheduled fetch (every {POLL_INTERVAL_MINUTES}m) ---")
            events = await listener.pull_events()
            print(f"Scheduled fetch retrieved {len(events)} new unique events.")
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"Scheduled polling error: {e}")
            
        await asyncio.sleep(POLL_INTERVAL_MINUTES * 60)

# --- Lifespan Manager ---
async def lifespan(app: FastAPI):
    # Startup: Start the background polling task
    polling_task = asyncio.create_task(scheduled_polling())
    yield
    # Shutdown: Clean up resources
    polling_task.cancel()
    await http_client.aclose()

# --- FastAPI App ---
app = FastAPI(lifespan=lifespan, title="Agentic AI Backend - Option 3")

# --- API Models ---
class PipelineRequest(BaseModel):
    tenant_id: str
    steps: List[str]
    expression_template: str = "{event_count}"
    expression: str = "0"

# --- API Endpoints (Task 2) ---
@app.post("/agent/act")
async def trigger_pipeline(request: PipelineRequest):
    """
    Receives API calls and triggers a choice of processing steps.
    """
    try:
        # Pass the payload dict to our orchestrator
        response = await orchestrator.process_request(request.model_dump())
        
        if response.get("error"):
            raise HTTPException(status_code=400, detail=response["error"])
            
        return response
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    
# --- Mock Agency Endpoint for Testing ---

@app.get("/mock-agency-a")
async def get_mock_data_a():
    """
    Primary Agency. 
    Simulates a 50% failure rate to demonstrate the automatic fallback mechanism.
    """
    # 50% chance to simulate a server crash/timeout
    if random() < 0.5:
        raise HTTPException(status_code=503, detail="Agency A is currently down.")

    # If it succeeds, return 5 high-magnitude events
    return [
        {
            "eid": randint(10000, 99999),
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "lat": 45.0, "lon": 90.0, "depth": -10.0,
            "Mw": 5.5, "dist": 100.0, "azi": 45.0, "loclat": 46.0, "loclon": 91.0
        } for _ in range(5)
    ]

@app.get("/mock-agency-b")
async def get_mock_data_b():
    """
    Fallback Agency.
    Always succeeds. Returns distinctly different data to prove the fallback occurred.
    """
    # Returns only 3 lower-magnitude events so we can easily spot the fallback in the console
    return [
        {
            "eid": randint(10000, 99999), 
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "lat": 35.0, "lon": -118.0, "depth": -5.0,
            "Mw": 4.2, "dist": 50.0, "azi": 90.0, "loclat": 36.0, "loclon": -119.0
        } for _ in range(3)
    ]