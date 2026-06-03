import json
from app.services import parsing, geocoding, matrix, simulation
from app.models.schemas import SimulationConfig, Location

# Load default CSV
with open("order_history_kaggle_data.csv", "r", encoding="utf-8") as f:
    file_content = f.read()

orders = parsing.parse_csv_content(file_content)

# Use dummy locations for everything since we don't have API key
for i, order in enumerate(orders):
    order.location = Location(
        original_address=f"Address {i}",
        latitude=28.0 + i*0.01,
        longitude=77.0 + i*0.01,
        formatted_address=f"Address {i}"
    )

# dummy matrix
num_nodes = len(orders) + 1
dummy_matrix = [[1.0] * num_nodes for _ in range(num_nodes)]

config = SimulationConfig(alns_enabled=True, alns_iterations=10) # Just to test ALNS

print("Running simulation...")
try:
    res = simulation.run_hybrid_simulation(
        orders=orders,
        time_matrix=dummy_matrix,
        distance_matrix=dummy_matrix,
        config=config,
        job_id="test_job_id"
    )
    print("Success! Routes:", len(res.routes))
except Exception as e:
    import traceback
    traceback.print_exc()
