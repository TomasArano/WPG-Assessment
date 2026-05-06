from grid import BeliefGrid
from updater import BayesianLogNormalUpdater

def main():
    # 1. Initialize the 4D xarray Grid (Lat, Lon, Depth, SoilSat)
    # Using small ranges for demonstration purposes
    grid = BeliefGrid(
        lat_range=(40.0, 41.0, 10),
        lon_range=(-75.0, -74.0, 10),
        depth_range=(-10.0, 0.0, 5),
        soilsat_range=(0.0, 1.0, 5)
    )
    
    # 2. Instantiate our chosen update mechanism
    updater = BayesianLogNormalUpdater()
    
    # Target coordinates for our test
    target_lat = 40.5
    target_lon = -74.5
    target_depth = -5.0
    target_soilsat = 0.5
    
    # Print Prior
    prior_mu, prior_var = grid.get_state(target_lat, target_lon, target_depth, target_soilsat)
    print(f"--- Prior State ---")
    print(f"Log-Mean (mu): {prior_mu:.4f}, Log-Variance: {prior_var:.4f}\n")
    
    # 3. Simulate incoming tomographic measurements
    # Measurement 1: Vs = 2.5 km/s, Uncertainty (log-variance) = 0.2
    print("Applying Measurement 1: Vs = 2.5, Var = 0.2")
    updater.update(grid, target_lat, target_lon, target_depth, target_soilsat, obs_val=2.5, obs_uncertainty=0.2)
    
    post1_mu, post1_var = grid.get_state(target_lat, target_lon, target_depth, target_soilsat)
    print(f"--- Posterior State 1 ---")
    print(f"Log-Mean (mu): {post1_mu:.4f}, Log-Variance: {post1_var:.4f}\n")
    
    # Measurement 2: Vs = 2.8 km/s, Uncertainty (log-variance) = 0.1 (More confident measurement)
    print("Applying Measurement 2: Vs = 2.8, Var = 0.1")
    updater.update(grid, target_lat, target_lon, target_depth, target_soilsat, obs_val=2.8, obs_uncertainty=0.1)
    
    post2_mu, post2_var = grid.get_state(target_lat, target_lon, target_depth, target_soilsat)
    print(f"--- Posterior State 2 ---")
    print(f"Log-Mean (mu): {post2_mu:.4f}, Log-Variance: {post2_var:.4f}")

if __name__ == "__main__":
    main()