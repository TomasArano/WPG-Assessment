from typing import Protocol
import numpy as np
from .grid import BeliefGrid

class Updater(Protocol):
    """Protocol defining the interface for belief update mechanisms."""
    def update(self, grid: BeliefGrid, lat: float, lon: float, depth: float, soilsat: float, 
               obs_val: float, obs_uncertainty: float) -> None:
        ...

class BayesianLogNormalUpdater:
    """
    Implements a Bayesian update for a Log-Normal distribution.
    Transforms observations into log-space, performs a conjugate Gaussian update,
    and writes the posterior moments back to the grid.
    """
    
    def update(self, grid: BeliefGrid, lat: float, lon: float, depth: float, soilsat: float, 
               obs_val: float, obs_uncertainty: float) -> None:
        """
        Updates the grid using Bayesian inference.
        Note: obs_uncertainty here is treated as the variance in the log space for simplicity 
        in this MVP. In a full system, a helper would map raw Vs variance to log-variance.
        """
        if obs_val <= 0:
            raise ValueError("Observation value (Vs) must be strictly positive.")
            
        # 1. Transform observation to log space
        log_obs = np.log(obs_val)
        
        # 2. Get Prior moments from the grid
        prior_mu, prior_var = grid.get_state(lat, lon, depth, soilsat)
        
        # 3. Calculate Posterior using Gaussian conjugate prior math
        # Precision is the inverse of variance. Adding precisions = Bayesian update.
        prior_precision = 1.0 / prior_var
        obs_precision = 1.0 / obs_uncertainty
        
        posterior_precision = prior_precision + obs_precision
        posterior_var = 1.0 / posterior_precision
        
        posterior_mu = posterior_var * ((prior_mu * prior_precision) + (log_obs * obs_precision))
        
        # 4. Write Posterior back to grid
        grid.set_state(lat, lon, depth, soilsat, posterior_mu, posterior_var)