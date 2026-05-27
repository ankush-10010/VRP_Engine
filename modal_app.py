import modal
import json
from typing import Dict, List
import sys
import os

# Create the Modal App
app = modal.App("vrp-optimizer")

# Define the image with all dependencies and mount the app directory
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "fastapi", "uvicorn", "pydantic", "googlemaps", "pandas", "sqlalchemy", "ortools", "psycopg2-binary", "python-dotenv", "python-multipart"
    )
    .add_local_dir("app", remote_path="/root/app")
)

@app.function(timeout=3600, image=image, secrets=[modal.Secret.from_name("custom-secret")])
def modal_simulation_task(file_content: str, api_key: str, config_dict: dict = None):
    """
    Full pipeline: Parse CSV -> Geocode -> Matrix -> Hybrid Simulation on Modal.
    """
    # Import inside function to avoid local import issues if running just modal deploy
    sys.path.append("/root")
    from app.services import matrix, parsing, geocoding, solver, simulation
    from app.models.schemas import Location, SimulationConfig
    
    print("[MODAL WORKER] Starting Parsing CSV...")
    # 1. Parse CSV
    try:
        orders = parsing.parse_csv_content(file_content)
    except Exception as e:
        return {"status": "Failed", "error": f"Parsing failed: {str(e)}"}
    
    if not orders:
        return {"status": "Failed", "error": "No valid orders found in CSV."}

    print(f"[MODAL WORKER] Geocoding {len(orders)} orders...")
    # 2. Extract Unique Addresses and Geocode
    unique_address_strings = parsing.extract_unique_addresses(orders)
    geocoded_locations, failed = geocoding.geocode_addresses(unique_address_strings, api_key)
    
    print(f"[MODAL WORKER] Geocoding Complete. {len(geocoded_locations)} unique locations found.")
    loc_map = {loc.original_address: loc for loc in geocoded_locations}
    
    # 3. Update Orders and Filter
    valid_orders = []
    for order in orders:
        if order.location.original_address in loc_map:
            order.location = loc_map[order.location.original_address]
            valid_orders.append(order)
            
    if not valid_orders:
        return {"status": "Failed", "error": "Geocoding failed for all addresses."}

    print(f"[MODAL WORKER] Starting Matrix Calculation for {len(valid_orders)} orders (plus Depot)...")
    # 4. Build Matrix with DEPOT
    depot = Location(
        original_address="Central Depot (Hardcoded)",
        latitude=28.5707,
        longitude=77.3262,
        formatted_address="Central Depot, Delhi"
    )
    
    customer_locations = list(loc_map.values())
    matrix_locations = [depot] + customer_locations
    
    time_mat, dist_mat = matrix.calculate_matrix(matrix_locations, api_key)
    print(f"[MODAL WORKER] Matrix Calculation Complete.")

    # 5. Solve: Expand Matrix and Call Solver
    unique_loc_index = {loc.original_address: i for i, loc in enumerate(matrix_locations)}
    
    num_solver_nodes = len(orders) + 1
    solver_matrix = [[0.0] * num_solver_nodes for _ in range(num_solver_nodes)]
    solver_dist_matrix = [[0.0] * num_solver_nodes for _ in range(num_solver_nodes)]
    
    def get_unique_idx(solver_node_idx):
        if solver_node_idx == 0:
            return 0
        order = orders[solver_node_idx - 1]
        addr = order.location.original_address
        return unique_loc_index.get(addr, 0)

    for i in range(num_solver_nodes):
        for j in range(num_solver_nodes):
            u_i = get_unique_idx(i)
            u_j = get_unique_idx(j)
            solver_matrix[i][j] = time_mat[u_i][u_j]
            solver_dist_matrix[i][j] = dist_mat[u_i][u_j]

    if config_dict:
        try:
            config = SimulationConfig(**config_dict)
        except Exception:
            config = SimulationConfig()
    else:
        config = SimulationConfig()
    
    print(f"[MODAL WORKER] Starting Hybrid Simulation...")
    sim_response = simulation.run_hybrid_simulation(
        orders=orders,
        time_matrix=solver_matrix,
        distance_matrix=solver_dist_matrix,
        config=config
    )
    print(f"[MODAL WORKER] Simulation Complete. Routes: {len(sim_response.routes)}")
    
    result_data = {
        "status": "Completed",
        "orders_processed": len(orders),
        "unique_locations_found": len(customer_locations),
        "routes": [route.dict() for route in sim_response.routes],
        "total_cost": sim_response.total_fleet_cost,
        "unassigned": sim_response.unassigned_orders,
        "analytics": sim_response.analytics.dict() if sim_response.analytics else None,
        "optimization_log": [log.dict() for log in sim_response.optimization_log],
        "events": [event.dict() for event in sim_response.events]
    }
    
    return result_data

@app.function(image=image, secrets=[modal.Secret.from_name("custom-secret")])
@modal.asgi_app()
def fastapi_modal_wrapper():
    sys.path.append("/root")
    from app.main import app as fastapi_app
    return fastapi_app
