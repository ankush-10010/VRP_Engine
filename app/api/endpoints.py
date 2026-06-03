from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Form, WebSocket
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
    file: Optional[UploadFile] = File(None), 
    use_default_csv: bool = Form(False),
    matrix_mode: str = Form("scratch"),
    matrix_file: Optional[UploadFile] = File(None),
    settings: Optional[str] = Form(None),
    api_key: str = Depends(get_api_key)
):
    """
    Upload a CSV file to start a full simulation pipeline via Modal.
    Optionally accepts a 'settings' JSON string for configuration.
    Returns a Task ID.
    """
    if use_default_csv:
        csv_text = "DEFAULT_CSV"
        filename = "order_history_kaggle_data.csv"
    else:
        if not file:
            raise HTTPException(status_code=400, detail="File must be provided if not using default CSV")
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be a CSV")
            
        contents = await file.read()
        csv_text = contents.decode('utf-8')
        filename = file.filename
    
    config_dict = None
    if settings:
        try:
            config_dict = json.loads(settings)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON in settings field")
            
    custom_matrix_data = None
    if matrix_mode == 'upload':
        if not matrix_file:
            raise HTTPException(status_code=400, detail="Matrix file must be provided when mode is upload")
        if not matrix_file.filename.endswith('.json'):
            raise HTTPException(status_code=400, detail="Matrix file must be a JSON file")
        try:
            matrix_contents = await matrix_file.read()
            custom_matrix_data = json.loads(matrix_contents.decode('utf-8'))
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON in matrix file")
    
    import sys
    import os
    # Ensure root directory is accessible for modal import
from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Form, WebSocket
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
    file: Optional[UploadFile] = File(None), 
    use_default_csv: bool = Form(False),
    matrix_mode: str = Form("scratch"),
    matrix_file: Optional[UploadFile] = File(None),
    settings: Optional[str] = Form(None),
    api_key: str = Depends(get_api_key)
):
    """
    Upload a CSV file to start a full simulation pipeline via Modal.
    Optionally accepts a 'settings' JSON string for configuration.
    Returns a Task ID.
    """
    if use_default_csv:
        csv_text = "DEFAULT_CSV"
        filename = "order_history_kaggle_data.csv"
    else:
        if not file:
            raise HTTPException(status_code=400, detail="File must be provided if not using default CSV")
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be a CSV")
            
        contents = await file.read()
        csv_text = contents.decode('utf-8')
        filename = file.filename
    
    config_dict = None
    if settings:
        try:
            config_dict = json.loads(settings)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON in settings field")
            
    custom_matrix_data = None
    if matrix_mode == 'upload':
        if not matrix_file:
            raise HTTPException(status_code=400, detail="Matrix file must be provided when mode is upload")
        if not matrix_file.filename.endswith('.json'):
            raise HTTPException(status_code=400, detail="Matrix file must be a JSON file")
        try:
            matrix_contents = await matrix_file.read()
            custom_matrix_data = json.loads(matrix_contents.decode('utf-8'))
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON in matrix file")
    
    import sys
    import os
    # Ensure root directory is accessible for modal import
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
    from modal_app import modal_simulation_task
    
    import uuid
    job_id = str(uuid.uuid4())
    
    # Trigger Background Task on Modal
    call = await modal_simulation_task.spawn.aio(csv_text, api_key, config_dict, matrix_mode, custom_matrix_data, job_id)
    
    return {"task_id": call.object_id, "job_id": job_id, "status": "Simulation started", "filename": filename}

@router.websocket("/simulation/ws/{job_id}/{task_id}")
async def simulation_websocket(websocket: WebSocket, job_id: str, task_id: str):
    await websocket.accept()
    
    import modal
    import asyncio
    
    progress_dict = modal.Dict.from_name("vrp-progress-dict")
    
    try:
        last_cost = None
        while True:
            # Look up this specific task's progress
            if job_id in progress_dict:
                current_state = progress_dict[job_id]
                
                # Only send a message if route improved
                if current_state.get("total_cost") != last_cost:
                    await websocket.send_json(current_state)
                    last_cost = current_state.get("total_cost")
            
            # Check if the Modal function has finished
            call = modal.FunctionCall.from_id(task_id)
            try:
                result = await call.get.aio(timeout=0.1)
                await websocket.send_json({"type": "complete", "results": result})
                break
            except TimeoutError:
                await asyncio.sleep(1)
                
    except Exception as e:
        print(f"WebSocket disconnected or error: {e}")
    finally:
        await websocket.close()
