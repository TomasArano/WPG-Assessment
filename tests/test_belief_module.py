import pytest
import numpy as np
from belief_module.grid import BeliefGrid
from belief_module.updater import BayesianLogNormalUpdater

@pytest.fixture
def sample_grid():
    """Fixture to provide a fresh, small 4D grid for each test."""
    return BeliefGrid(
        lat_range=(40.0, 41.0, 2),    # Just 2 points: 40.0, 41.0
        lon_range=(-75.0, -74.0, 2),  # Just 2 points: -75.0, -74.0
        depth_range=(-10.0, 0.0, 2),
        soilsat_range=(0.0, 1.0, 2)
    )

@pytest.fixture
def updater():
    """Fixture to provide the Bayesian updater."""
    return BayesianLogNormalUpdater()

def test_grid_initialization(sample_grid):
    """
    Criterion: Represent the belief state with uncertainty.
    Ensures the grid initializes with an uninformative prior (high variance).
    """
    mu, var = sample_grid.get_state(lat=40.0, lon=-75.0, depth=-10.0, soilsat=0.0)
    
    assert mu == 0.0, "Initial log-mean should be 0.0"
    assert var == 10.0, "Initial log-variance should be high (uninformative prior)"

def test_positive_velocity_constraint(sample_grid, updater):
    """
    Criterion: Physical constraints: Velocities are positive.
    Ensures the updater rejects zero or negative Vs values.
    """
    with pytest.raises(ValueError, match="strictly positive"):
        updater.update(
            sample_grid, 
            lat=40.0, lon=-75.0, depth=-10.0, soilsat=0.0, 
            obs_val=0.0, # Invalid physical value
            obs_uncertainty=0.1
        )

def test_bayesian_update_reduces_uncertainty(sample_grid, updater):
    """
    Criterion: Epistemic uncertainty propagation.
    Ensures that applying a valid measurement reduces the variance (uncertainty)
    of the belief state at that node.
    """
    target_coords = {"lat": 40.0, "lon": -75.0, "depth": -10.0, "soilsat": 0.0}
    
    # Get prior
    prior_mu, prior_var = sample_grid.get_state(**target_coords)
    
    # Apply an observation
    updater.update(
        sample_grid, 
        **target_coords, 
        obs_val=3.0, 
        obs_uncertainty=0.5
    )
    
    # Get posterior
    post_mu, post_var = sample_grid.get_state(**target_coords)
    
    # Assertions
    assert post_var < prior_var, "Posterior variance should be strictly less than prior variance after a measurement."
    assert post_mu != prior_mu, "Posterior mean should shift towards the observation."

def test_spatial_independence(sample_grid, updater):
    """
    Criterion: Efficient storage of multi-variate data.
    Ensures that updating a specific nearest neighbor node does not bleed 
    into adjacent nodes in the xarray dataset.
    """
    target_node = {"lat": 40.0, "lon": -75.0, "depth": -10.0, "soilsat": 0.0}
    adjacent_node = {"lat": 41.0, "lon": -75.0, "depth": -10.0, "soilsat": 0.0}
    
    # Apply an observation to the target node
    updater.update(
        sample_grid, 
        **target_node, 
        obs_val=3.0, 
        obs_uncertainty=0.5
    )
    
    # Check the target node (should be updated)
    target_mu, target_var = sample_grid.get_state(**target_node)
    assert target_var < 10.0, "Target node should have reduced variance."
    
    # Check the adjacent node (should remain at uninformative prior)
    adj_mu, adj_var = sample_grid.get_state(**adjacent_node)
    assert adj_var == 10.0, "Adjacent node variance should remain unchanged."
    assert adj_mu == 0.0, "Adjacent node mean should remain unchanged."