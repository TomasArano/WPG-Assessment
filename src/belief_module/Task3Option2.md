**Option 2 Task 2: Design Principles and Implementation Notes**

- **Each code component should have clear responsibilities and be easy to swap/update:**
	- The architecture enforces strict separation of concerns. The `BeliefGrid` exclusively handles spatial querying and state management via `xarray`, whilst the mathematical operations are abstracted behind an Updater protocol interface. By decoupling data storage from computation, either domain can be modified or entirely swapped without triggering cascading changes across the codebase.

- **Update mechanisms should be upgradable or extendable (e.g., with new update mechanism(s)):**
	- By applying the Open/Closed Principle with Python Protocols, the architecture ensures that the update mechanism can be extended without altering the rest of the system. Later we can introduce new algorithms like Ensemble Kalman Filter or an ML-based algo, simply by authoring a new class that satisfies the interface I have defined.

- **Memory efficient for data with large footprint and efficient GPU compute:**
	- To handle massive 4D tensors I used `xarray`, which can support chunked storage formats, like Zarr. This ensures we only load required spatial subsets into RAM rather than the entire dataset. For GPU compute, the functional, array-first design allows a seamless swap from CPU-bound `numpy` arrays to GPU-bound `cupy` arrays, delivering hardware (Nvidia) acceleration without altering the core update logic.

- **Minimal code change when going from single-user execution to multi-user executions (for instance, for concurrent data extraction and updates in several disjoint regions):**
	- The mockup provided used a single global lock, which forces every user to wait in one long queue just to make an update. Instead I used a 'stateless' updater, which should handle multiple users updating different regions at the exact same time, with a background queue, like Celery. This avoids Python's threading limits with the GIL, allowing the system to scale to many users/jobs.

- **Tracking belief reliability through belief state update:**
	- Rather than calculating an arbitrary confidence score, the system measures reliability using statistics. We model the seismic velocities as probability distributions so that our certainty is directly tied to the statistical variance at any given location.
	- So each time we feed a new measurement into the system, the underlying Bayesian math shrinks this variance, proving we are becoming more certain (unless you consider yourself a frequentist).

- **Ease of coding, ease of debugging, latency, compute cost:**
	- Beyond what has already been discussed, I tried to implement SOLID principles, clean code practices and use comprehensive docstrings to keep the codebase maintainable like I would in my day to day work. I used a Test Driven approach to validate my code as well as show my understanding of the assessment's criteria.