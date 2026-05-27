from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Form
from typing import List, Optional
import os
import json
from ..models.schemas import (
    GeocodeRequest, GeocodeResponse, 
    MatrixRequest, MatrixResponse, 
    OptimizationRequest, OptimizationResponse
)
from ..services import geocoding, matrix, solver

router = APIRouter()

# Dependency to get API Key (can be improved)
def get_api_key():
    key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not key:
        raise HTTPException(status_code=500, detail="Google Maps API Key not configured.")
    return key

@router.post("/geocode", response_model=GeocodeResponse)
async def geocode_locations(request: GeocodeRequest, api_key: str = Depends(get_api_key)):
    """
    Geocode a list of addresses.
    """
    locations, failed = geocoding.geocode_addresses(request.addresses, api_key)
    return GeocodeResponse(locations=locations, failed_addresses=failed)

@router.get("/matrix-status/{task_id}")
async def get_matrix_status(task_id: str):
    """
    Check the status of a background matrix task on Modal.
    """
    import modal
    
    try:
        call = modal.FunctionCall.from_id(task_id)
        # Check if the cloud server finished the math without blocking
        result = call.get(timeout=0.1)
        return {"status": "Completed", "result": result}
    except TimeoutError:
        return {"status": "Progress", "meta": {"message": "Processing in Modal cloud..."}}
    except Exception as e:
        return {"status": "Failure", "error": str(e)}

@router.post("/simulation/upload-csv")
async def upload_simulation_csv(
    file: UploadFile = File(...), 
    settings: Optional[str] = Form(None),
    api_key: str = Depends(get_api_key)
):
    """
    Upload a CSV file to start a full simulation pipeline via Modal.
    Optionally accepts a 'settings' JSON string for configuration.
    Returns a Task ID.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
        
    contents = await file.read()
    csv_text = contents.decode('utf-8')
    
    config_dict = None
    if settings:
        try:
            config_dict = json.loads(settings)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON in settings field")
    
    import sys
    import os
    # Ensure root directory is accessible for modal import
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
    from modal_app import modal_simulation_task
    
    # Trigger Background Task on Modal
    call = modal_simulation_task.spawn(csv_text, api_key, config_dict)
    
    return {"task_id": call.object_id, "status": "Simulation started", "filename": file.filename}
