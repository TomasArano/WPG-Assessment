import asyncio
import time
import logging
from typing import Dict, Any, Protocol
from functools import wraps

logger = logging.getLogger(__name__)

# --- 1. Timing Decorator ---
def track_performance(func):
    """
    Decorator to measure and expose execution (CPU) and wall-clock times.
    Wraps the return payload in a standardized multi-tenant response.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        wall_start = time.perf_counter()
        cpu_start = time.process_time()
        
        error_msg = None
        data = None
        try:
            data = await func(*args, **kwargs)
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Pipeline execution failed: {error_msg}")
            
        wall_end = time.perf_counter()
        cpu_end = time.process_time()
        
        return {
            "data": data,
            "error": error_msg,
            "wall_clock_ms": round((wall_end - wall_start) * 1000, 4),
            "execution_cpu_ms": round((cpu_end - cpu_start) * 1000, 4)
        }
    return wrapper

# --- 2. Service Protocol (Interface) ---
class PipelineService(Protocol):
    """Standardized interface for all downstream pipelines."""
    async def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        ...

# --- 3. Concrete Services ---
class ArithmeticService:
    """
    Service 2: Performs floating point calculations in an external Shell.
    """
    async def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        expression = payload.get("expression", "0")
        
        # We use Python as our highly-precise, cross-platform *nix shell calculator.
        # Security Note: In a real system, strictly sanitize 'expression' to prevent shell injection.
        cmd = f'python -c "print(float({expression}))"'
        
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            return {"error": f"Shell arithmetic failed: {stderr.decode().strip()}"}
            
        try:
            return {"result": float(stdout.decode().strip())}
        except ValueError:
             return {"error": "Could not parse shell output to float."}

class ListenerService:
    """
    Service 1: Triggers an immediate data pull via the SeismicListener.
    """
    def __init__(self, listener):
        self._listener = listener

    async def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # Force immediate pull
        events = await self._listener.pull_events()
        return {
            "event_count": len(events),
            "events_retrieved": [e.eid if hasattr(e, 'eid') else e for e in events]
        }

# --- 4. The Orchestrator ---
class Orchestrator:
    """
    Multi-tenant backend that routes requests and chains pipelines.
    """
    def __init__(self, services: Dict[str, PipelineService]):
        self._services = services

    @track_performance
    async def process_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Heuristic: Reads the 'steps' array in the payload and chains them.
        Passes variables from previous steps into the next step.
        """
        steps = payload.get("steps", [])
        if not steps:
            raise ValueError("No pipeline steps requested.")

        current_state = {}
        
        # Process Chaining Loop
        for step_name in steps:
            if step_name not in self._services:
                raise ValueError(f"Unknown service: {step_name}")
                
            service = self._services[step_name]
            
            # Prepare payload for this step based on heuristic
            step_payload = payload.copy()
            
            # If this is the math step chained after the listener step, 
            # inject the event count into the mathematical expression template.
            if step_name == "math" and "event_count" in current_state:
                template = payload.get("expression_template", "0")
                step_payload["expression"] = template.replace(
                    "{event_count}", str(current_state["event_count"])
                )

            # Execute step
            step_result = await service.execute(step_payload)
            
            # Handle graceful failure mid-pipeline
            if "error" in step_result:
                raise RuntimeError(f"Step '{step_name}' failed: {step_result['error']}")
                
            # Update state with the result for the next step in the chain
            current_state.update(step_result)

        return {"final_result": current_state}