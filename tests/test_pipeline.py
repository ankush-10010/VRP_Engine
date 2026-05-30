import pytest
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from unittest.mock import patch

# IMPORTANT: To test modal functions locally, we need to ensure app can be imported
from app.services import parsing, simulation
from app.models.schemas import SimulationConfig

@pytest.fixture
def sample_csv_content():
    """Fixture to load our small, 10-row test dataset"""
    test_file_path = os.path.join(os.path.dirname(__file__), "data", "test_orders_10.csv")
    with open(test_file_path, "r", encoding="utf-8") as f:
        return f.read()

def test_parsing_feature(sample_csv_content):
    """
    Test that the backend can successfully parse the Kaggle dataset format.
    """
    orders = parsing.parse_csv_content(sample_csv_content)
    # We extracted 11 lines (1 header + 10 rows), so we expect up to 10 orders
    assert len(orders) > 0
    assert len(orders) <= 10
    
    # Verify the structure of the parsed data
    first_order = orders[0]
    assert first_order.order_id is not None
    assert first_order.location.original_address is not None

@patch('app.services.geocoding.geocode_addresses')
@patch('app.services.matrix.calculate_matrix')
def test_scratch_calculation_feature(mock_calc_matrix, mock_geocode, sample_csv_content):
    """
    Test the 'Calculate from Scratch' mode logic.
    We MOCK the Google Maps API so we don't actually get charged or slowed down!
    """
    orders = parsing.parse_csv_content(sample_csv_content)
    
    # 1. Mock Geocoding Response (Fake coordinates)
    from app.models.schemas import Location
    mock_locs = [Location(original_address=o.location.original_address, latitude=28.5, longitude=77.3, formatted_address="Mock") for o in orders]
    mock_geocode.return_value = (mock_locs, [])
    
    # 2. Mock Matrix API Response (Fake distances)
    num_nodes = len(mock_locs) + 1 # +1 for depot
    mock_time_matrix = [[10.0] * num_nodes for _ in range(num_nodes)]
    mock_dist_matrix = [[5000.0] * num_nodes for _ in range(num_nodes)]
    mock_calc_matrix.return_value = (mock_time_matrix, mock_dist_matrix)
    
    # Give it a strict iteration limit in testing so it never hangs infinitely
    config = SimulationConfig(alns_iterations=5, strategy="ortools", layer_2_interval=99999, ortools_timeout=1)
    response = simulation.run_hybrid_simulation(
        orders=orders,
        time_matrix=mock_time_matrix,
        distance_matrix=mock_dist_matrix,
        config=config
    )
    
    # Assertions to prove the feature works
    assert response is not None
    assert len(response.routes) > 0
    assert response.total_fleet_cost > 0

def test_upload_matrix_feature(sample_csv_content):
    """
    Test the 'Upload Custom Matrix' mode logic.
    We pass in a pre-made matrix directly instead of calculating it.
    """
    orders = parsing.parse_csv_content(sample_csv_content)
    
    # Load the real matrix from your project folder
    import json
    matrix_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "matrix_data_with_distance.json")
    with open(matrix_path, "r") as f:
        master_matrix_data = json.load(f)
        
    master_locations = master_matrix_data.get("locations", [])
    time_mat = master_matrix_data.get("time_matrix", [])
    dist_mat = master_matrix_data.get("distance_matrix", [])
    
    unique_loc_index = {loc['original_address']: i for i, loc in enumerate(master_locations)}
    
    # Filter the 10 orders to make sure they actually exist in the master matrix
    valid_orders = []
    for order in orders:
        if order.location.original_address in unique_loc_index:
            # We don't overwrite the original order list, just collect valid ones
            valid_orders.append(order)
            
    # Build solver matrix matching the valid orders
    num_nodes = len(valid_orders) + 1
    custom_time_matrix = [[0.0] * num_nodes for _ in range(num_nodes)]
    custom_dist_matrix = [[0.0] * num_nodes for _ in range(num_nodes)]
    
    def get_unique_idx(solver_node_idx):
        if solver_node_idx == 0: return 0
        addr = valid_orders[solver_node_idx - 1].location.original_address
        return unique_loc_index.get(addr, 0)

    for i in range(num_nodes):
        for j in range(num_nodes):
            u_i = get_unique_idx(i)
            u_j = get_unique_idx(j)
            custom_time_matrix[i][j] = time_mat[u_i][u_j]
            custom_dist_matrix[i][j] = dist_mat[u_i][u_j]
            
    # Give it a strict iteration limit in testing so it never hangs infinitely
    config = SimulationConfig(alns_iterations=5, strategy="ortools", layer_2_interval=99999, ortools_timeout=1)
    response = simulation.run_hybrid_simulation(
        orders=valid_orders,
        time_matrix=custom_time_matrix,
        distance_matrix=custom_dist_matrix,
        config=config
    )
    
    # Verify the simulation successfully processes using uploaded data
    assert response is not None
