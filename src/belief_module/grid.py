import numpy as np
import xarray as xr
from typing import Tuple

class BeliefGrid:
    """
    Represents the 4D belief state of seismic S-wave velocities (Vs).
    Velocities are strictly positive and modeled via a Log-Normal distribution.
    The grid stores the parameters of the underlying Normal distribution:
    mu (mean of ln(Vs)) and var (variance of ln(Vs)).
    """
    
    def __init__(self, lat_range: Tuple[float, float, int], 
                 lon_range: Tuple[float, float, int], 
                 depth_range: Tuple[float, float, int], 
                 soilsat_range: Tuple[float, float, int]):
        """
        Initializes the xarray Dataset for the 4D grid.
        Ranges are given as (start, stop, num_points).
        """
        self.lats = np.linspace(*lat_range)
        self.lons = np.linspace(*lon_range)
        self.depths = np.linspace(*depth_range)
        self.soilsats = np.linspace(*soilsat_range)
        
        # Initialize with uninformative priors
        # mu = 0.0 (ln(1.0 km/s) = 0), high variance = highly uncertain
        shape = (len(self.lats), len(self.lons), len(self.depths), len(self.soilsats))
        initial_mu = np.zeros(shape)
        initial_var = np.ones(shape) * 10.0 
        
        self.dataset = xr.Dataset(
            {
                "mu": (["lat", "lon", "depth", "soilsat"], initial_mu),
                "var": (["lat", "lon", "depth", "soilsat"], initial_var),
            },
            coords={
                "lat": self.lats,
                "lon": self.lons,
                "depth": self.depths,
                "soilsat": self.soilsats,
            }
        )

    def get_state(self, lat: float, lon: float, depth: float, soilsat: float) -> Tuple[float, float]:
        """Returns the (mu, var) for the nearest grid point."""
        point = self.dataset.sel(lat=lat, lon=lon, depth=depth, soilsat=soilsat, method="nearest")
        return float(point["mu"].values), float(point["var"].values)

    def set_state(self, lat: float, lon: float, depth: float, soilsat: float, new_mu: float, new_var: float):
        """Updates the (mu, var) for the nearest grid point."""
        # 1. First, find the exact coordinates of the nearest existing grid node
        nearest = self.dataset.sel(lat=lat, lon=lon, depth=depth, soilsat=soilsat, method="nearest")
        
        # 2. Build an indexer using those exact mathematical coordinates
        exact_indexer = {
            "lat": nearest.lat.item(),
            "lon": nearest.lon.item(),
            "depth": nearest.depth.item(),
            "soilsat": nearest.soilsat.item()
        }
        
        # 3. Safely update the grid
        self.dataset["mu"].loc[exact_indexer] = new_mu
        self.dataset["var"].loc[exact_indexer] = new_var