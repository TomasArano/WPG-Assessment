# Assessment Maps: Option 2 and Option 3

This repository contains implementations for both **Option 2** (Belief Module) and **Option 3** (Orchestration) of the technical assessment. 

Below is an index of how the codebase maps to the respective assessment options and tasks (Tasks 1 & 2):

##  Assessment Index Map

### Option 2: Belief State Updates 
- **Task 1 (Implementation):** Handled by the module at `src/belief_module/` and its testing suite.
  - `src/belief_module/__init__.py`
  - `src/belief_module/grid.py`
  - `src/belief_module/main.py`
  - `src/belief_module/updater.py`
  - `tests/test_belief_module.py`
- **Task 2 (Design Principles & Notes):** [Task 2 Design Notes](src/belief_module/Task3Option2.md) *(Note: The document acts as Task 2 for Option 2)*

### Option 3: Agentic Orchestration Pipeline
- **Task 1 (Fault-Tolerant Retrieval):** Handled by the listener service at `src/orchestration/listener.py`.
- **Task 2 (Execution Orchestrator):** Addressed by the rest of the orchestration and pipeline files:
  - `src/orchestration/__init__.py`
  - `src/orchestration/main.py`
  - `src/orchestration/pipelines.py`
  - `tests/test_integration.py`
  - `tests/test_listener.py`
  - `tests/test_pipelines.py`

---

## Prerequisites
- **Python:** 3.13 or higher
- **Package Manager:** `uv` or `pip`

---

##  Installation Instructions (macOS & Linux)

### Option A: Using `uv` (my recommendation)

```bash
# 1. Install uv (if you don't have it)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Clone the repository and navigate into it
git clone <repository_url> WPG-Assessment
cd WPG-Assessment

# 3. Create a virtual environment and sync all dependencies
uv venv
source .venv/bin/activate
uv sync --all-groups
```

### Option B: Using Standard `pip` and `venv`
```bash
# 1. Clone the repository and navigate into it
git clone <repository_url> WPG-Assessment
cd WPG-Assessment

# 2. Create the virtual environment
python3 -m venv venv

# 3. Activate the virtual environment
# On macOS and Linux:
source venv/bin/activate

# 4. Install standard backend and test dependencies 
pip install fastapi uvicorn httpx pydantic pytest pytest-asyncio numpy scipy
```


---

## Belief Module (Option 2)

This repository also includes the core `belief_module` implementation located in `src/belief_module/`, which handles 4D spatial querying and Bayesian state management using `xarray`.

### Design Principles and Implementation Notes

For a detailed breakdown of the architecture, separation of concerns, and design patterns used for this component, please refer to the design document: 
[Task 2 Option 2 ](src/belief_module/Task3Option2.md)

### Testing the Belief Module

The module includes its own dedicated test suite (`tests/test_belief_module.py`) to validate grid initialization, epistemic uncertainty updates, physical constraints, and data independence.

You can run this specific test suite using `uv`:
```bash
uv run pytest tests/test_belief_module.py
```

---

##  Agentic Orchestration Pipeline, running the API (Option 3)

To start the main FASTAPI orchestration server:

```bash
uvicorn src.orchestration.main:app --host 127.0.0.1 --port 8000 --reload
```
*Note: We specifically use port `8000` because the listener routes fallback URLs conditionally expect `http://127.0.0.1:8000`.*

### What happens when you run it?
- A background routine automatically starts up (`scheduled_polling`), polling the mock agency data every 5 minutes and printing background logs.
- Three endpoints become available locally:
  - `POST /agent/act`: The main ingress agent URL to trigger orchestration pipelines.
  - `GET /mock-agency-a`: Simulates the primary Agency (returns 5 events, but has a 50% randomized failure rate to demonstrate resilience).
  - `GET /mock-agency-b`: Simulates the Fallback Agency (returns 3 events and is highly stable).

### Options (Interact with the Pipeline)
You can directly test the API by hitting the `/agent/act` endpoint using cURL or via the built-in interactive Swagger interface at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

**Example cURL Pipeline Request:**
```bash
curl -X POST "http://127.0.0.1:8000/agent/act" \
	  -H "Content-Type: application/json" \
	  -d '{
			  "tenant_id": "demo_tenant_1",
			  "steps": ["listener", "math"],
			  "expression_template": "{event_count} * 100"
			}'
```
This forces the orchestrator to fetch agency data, recover from failure if the primary is down, count the events, and evaluate the final math expression dynamically!

---

##  Testing Option 3

We leverage `pytest` and `pytest-asyncio` for exhaustive unit and integration testing. 

To run the entire suite of tests, run:
```bash
pytest tests/ -v
```

### Example Test Output

```text
============================= test session starts ==============================
platform darwin -- Python 3.13.0, pytest-8.3.3, pluggy-1.5.0 -- /WPG-Assessment/venv/bin/python
cachedir: .pytest_cache
rootdir: /WPG-Assessment
configfile: pytest.ini
plugins: asyncio-0.24.0
asyncio: mode=Mode.AUTO, default_loop_scope=session
collected 3 items                                                               

tests/test_integration.py::test_requirement_process_chaining_and_metrics PASSED [ 33%]
tests/test_integration.py::test_requirement_automatic_fallback PASSED           [ 66%]
tests/test_integration.py::test_requirement_gracious_error_handling PASSED      [100%]

============================== 3 passed in 0.21s ===============================
```

### Explaining the Tests
The test module (`tests/test_integration.py`) comprehensively checks key Option 3 architectural requirements:

1. **`test_requirement_process_chaining_and_metrics`**: 
	- **How it works:** Injects a payload into `/agent/act` chaining the `[listener, math]` steps. Through mocking the randomized failure down to 0%, it forces the Primary agency to succeed.
	- **What it verifies:** Demonstrates that contexts are gracefully passed from one service to another, verifies dynamic expression evaluations (e.g. `{event_count} * 10`), and ultimately asserts that precise system metrics (like `execution_cpu_ms`, `wall_clock_ms`) are collected.

2. **`test_requirement_automatic_fallback`**:
	- **How it works:** Tests the resilient auto-fallback orchestrator mechanism.
	- **What it verifies:** It safely hardcodes a 100% mocked failure rate for the primary node. We assert that underneath the hood, the pipeline intercepts the error and routes the fallback query natively to Agency B (demonstrated by returning the designated secondary `3` event nodes layout).

3. **`test_requirement_gracious_error_handling`**:
	- **How it works:** Feeds corrupted operations (like invalid mathematical expressions `this_is_not_math` ) to the final math service.
	- **What it verifies:** Checks that failures in sequential multi-tenant pipelines do not crash the REST application. Errors are caught safely, packed into an HTTP 400 response with detail payloads, keeping the server globally reliable.



