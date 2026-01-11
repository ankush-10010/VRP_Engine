from .celery_app import celery_app
from .services import matrix, parsing, geocoding, solver
from .models.schemas import Location, MatrixResponse, Order
from typing import List, Dict
import os
import time

@celery_app.task
def calculate_matrix_task(locations_dicts: List[dict], api_key: str, departure_offset: int):
    """
    Celery task to calculate matrix in background.
    """
    locations = [Location(**loc) for loc in locations_dicts]
    time_mat, dist_mat = matrix.calculate_matrix(locations, api_key, departure_offset)
    return {
        "locations": locations_dicts,
        "time_matrix": time_mat,
        "distance_matrix": dist_mat
    }

@celery_app.task(bind=True)
def run_simulation_task(self, file_content: str, api_key: str, config_dict: Dict = None):
    """
    Full pipeline: Parse CSV -> Geocode -> Matrix -> Hybrid Simulation.
    """
    self.update_state(state='PROGRESS', meta={'message': 'Parsing CSV...'})
    
    # 1. Parse CSV
    try:
        orders = parsing.parse_csv_content(file_content)
    except Exception as e:
        return {"status": "Failed", "error": f"Parsing failed: {str(e)}"}
    
    if not orders:
        return {"status": "Failed", "error": "No valid orders found in CSV."}

    self.update_state(state='PROGRESS', meta={'message': f'Geocoding {len(orders)} orders...'})
    print(f"[WORKER] Starting Geocoding for {len(orders)} orders...")

    # 2. Extract Unique Addresses and Geocode
    unique_address_strings = parsing.extract_unique_addresses(orders)
    geocoded_locations, failed = geocoding.geocode_addresses(unique_address_strings, api_key)
    
    print(f"[WORKER] Geocoding Complete. {len(geocoded_locations)} unique locations found.")
    
    loc_map = {loc.original_address: loc for loc in geocoded_locations}
    
    # 3. Update Orders and Filter
    valid_orders = []
    
    for order in orders:
        if order.location.original_address in loc_map:
            order.location = loc_map[order.location.original_address]
            valid_orders.append(order)
            
    if not valid_orders:
        return {"status": "Failed", "error": "Geocoding failed for all addresses."}

    self.update_state(state='PROGRESS', meta={'message': f'Building Matrix...'})
    print(f"[WORKER] Starting Matrix Calculation for {len(valid_orders)} orders (plus Depot)...")

    # 4. Build Matrix with DEPOT
    # We MUST inject a Depot at Index 0 because the Solver expects it.
    # In a real app, this should come from the User Request.
    # For now, we hardcode a default Depot (like the legacy script did).
    
    depot = Location(
        original_address="Central Depot (Hardcoded)",
        latitude=28.5707,  # Example from legacy
        longitude=77.3262,
        formatted_address="Central Depot, Delhi"
    )
    
    # Unique locations from orders (Customers)
    customer_locations = list(loc_map.values())
    
    # IMPORTANT: The matrix "locations" list must start with Depot
    matrix_locations = [depot] + customer_locations
    
    time_mat, dist_mat = matrix.calculate_matrix(matrix_locations, api_key)
    print(f"[WORKER] Matrix Calculation Complete.")

    # 5. Solve: Expand Matrix and Call Solver
    # Strategy:
    # The Matrix (MxM) corresponds to `matrix_locations` (Depot + Unique Customers).
    # The Solver expects `orders` where order[i] maps to a specific matrix node.
    # But current simplistic Solver assumes strict 1:1 mapping (Order[i] is Node[i+1]).
    # To use the current Solver without rewriting it, we must construct a full NxN matrix
    # where N = Depot + NumOrders.
    
    # Map: Unique Location String -> Matrix Index (0..M-1)
    unique_loc_index = {loc.original_address: i for i, loc in enumerate(matrix_locations)}
    
    # We need to build a new `solver_matrix` of size (num_orders + 1) x (num_orders + 1)
    # Node 0 = Depot
    # Node k = Order k-1 (for k=1..num_orders)
    
    num_solver_nodes = len(orders) + 1
    solver_matrix = [[0.0] * num_solver_nodes for _ in range(num_solver_nodes)]
    solver_dist_matrix = [[0.0] * num_solver_nodes for _ in range(num_solver_nodes)]
    
    # Function scope imports
    from .db.session import SessionLocal
    from .models.db_models import Simulation as SimulationDB
    from .models.schemas import SimulationConfig
    from .services import simulation
    
    # ... Helper function ...
    def get_unique_idx(solver_node_idx):
        if solver_node_idx == 0:
            return 0 # Depot
        order = orders[solver_node_idx - 1]
        addr = order.location.original_address
        return unique_loc_index.get(addr, 0)

    # Note: run_hybrid_simulation expects the "Master Matrix" (Unique Locations)
    # and handles the order-to-location mapping internally.
    
    # Fill expanded matrices
    for i in range(num_solver_nodes):
        for j in range(num_solver_nodes):
            u_i = get_unique_idx(i)
            u_j = get_unique_idx(j)
            solver_matrix[i][j] = time_mat[u_i][u_j]
            solver_dist_matrix[i][j] = dist_mat[u_i][u_j]

    # Load config
    if config_dict:
        try:
            config = SimulationConfig(**config_dict)
        except Exception:
            # Fallback if validation fails
            config = SimulationConfig()
    else:
        config = SimulationConfig()
    
    print(f"[WORKER] Starting Hybrid Simulation...")
    # Run the Hybrid Simulation Pipeline
    sim_response = simulation.run_hybrid_simulation(
        orders=orders,
        time_matrix=solver_matrix,
        distance_matrix=solver_dist_matrix,
        config=config
    )
    print(f"[WORKER] Simulation Complete. Routes: {len(sim_response.routes)}")
    
    result_data = {
        "status": "Completed",
        "orders_processed": len(orders),
        "unique_locations_found": len(customer_locations),
        "routes": [route.dict() for route in sim_response.routes],
        "total_cost": sim_response.total_fleet_cost,
        "unassigned": sim_response.unassigned_orders
    }

    # Save to DB
    try:
        db = SessionLocal()
        task_id = self.request.id
        sim_record = db.query(SimulationDB).filter(SimulationDB.id == task_id).first()
        if not sim_record:
            sim_record = SimulationDB(id=task_id, status="Completed")
            db.add(sim_record)
        else:
            sim_record.status = "Completed"
            
        sim_record.result = result_data 
        
        db.commit()
        db.close()
    except Exception as e:
        print(f"DB Save Error: {e}")
    
    return result_data
