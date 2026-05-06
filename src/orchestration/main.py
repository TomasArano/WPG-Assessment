import asyncio
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any

from src.orchestration.listener import SeismicListener
from src.orchestration.pipelines import Orchestrator, ArithmeticService, ListenerService

# --- Configuration ---
POLL_INTERVAL_MINUTES = 5  # The "m" minutes variable
AGENCY_A = "https://mock-agency-a.com/events" 
AGENCY_B = "https://mock-agency-b.com/events"

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
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")