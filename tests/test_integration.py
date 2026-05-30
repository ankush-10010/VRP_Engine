import pytest
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import modal

# Import your actual Modal app definition
from modal_app import app, modal_simulation_task

# Mark this as an integration test so it doesn't accidentally run without Modal credentials
@pytest.mark.integration
@pytest.mark.skipif(not modal.config.config.get("token_id"), reason="Modal credentials not found")
def test_live_modal_ephemeral_environment():
    """
    This test completely spins up a brand new, isolated Modal environment in the cloud,
    runs your simulation against the test CSV and your real JSON matrix file,
    and then immediately destroys the environment.
    """
    # 1. Read our 10-order test CSV
    test_csv_path = os.path.join(os.path.dirname(__file__), "data", "test_orders_10.csv")
    with open(test_csv_path, "r", encoding="utf-8") as f:
        csv_content = f.read()
        
    print("\n[TEST] 1. Starting Ephemeral Modal App...")
    print("ENDED")
    # 2. Spin up the Ephemeral Modal App
    with app.run():
        print("[TEST] 2. Modal App is running! Sending request to cloud container...")
        
        # 3. Call the function remotely
        response = modal_simulation_task.remote(
            file_content=csv_content,
            api_key="mock_key_not_needed_for_database_mode", 
            matrix_mode="database",
            config_dict={"layer_2_interval": 99999, "ortools_timeout": 1}
        )
        
        print(f"[TEST] 3. Received response from Modal: {response.get('status')}")
        
        # 4. Assert the live cloud function actually works
        assert response is not None
        assert response.get("status") == "Completed"
        assert len(response.get("routes", [])) > 0
        
    print("[TEST] 4. Test Complete, Modal App destroyed.")
