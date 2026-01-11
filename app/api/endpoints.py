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

@router.post("/matrix-async")
async def build_matrix_async(request: MatrixRequest, api_key: str = Depends(get_api_key)):
    """
    Trigger a background task to calculate the matrix.
    Returns a Task ID.
    """
    from ..worker import calculate_matrix_task
    
    # Convert Pydantic models to dicts for Celery serialization
    locations_dicts = [loc.dict() for loc in request.locations]
    
    task = calculate_matrix_task.delay(
        locations_dicts, 
        api_key, 
        request.departure_time_offset_hours
    )
    
    return {"task_id": task.id, "status": "Processing started"}

@router.get("/matrix-status/{task_id}")
async def get_matrix_status(task_id: str):
    """
    Check the status of a background matrix task.
    """
    from ..worker import calculate_matrix_task, run_simulation_task
    from celery.result import AsyncResult
    
    # Check both task types (not ideal but works for now)
    task_result = AsyncResult(task_id, app=calculate_matrix_task.app)
    
    if task_result.state == 'PENDING':
        return {"status": "Pending"}
    elif task_result.state == 'PROGRESS':
        return {"status": "Progress", "meta": task_result.info}
    elif task_result.state == 'SUCCESS':
        return {"status": "Success", "result": task_result.result}
    elif task_result.state == 'FAILURE':
        return {"status": "Failure", "error": str(task_result.result)}
    else:
        return {"status": task_result.state}

@router.post("/simulation/upload-csv")
async def upload_simulation_csv(
    file: UploadFile = File(...), 
    settings: Optional[str] = Form(None),
    api_key: str = Depends(get_api_key)
):
    """
    Upload a CSV file to start a full simulation pipeline.
    Optionally accepts a 'settings' JSON string for configuration.
    Returns a Task ID.
    """
    from ..worker import run_simulation_task
    
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
    
    # Trigger Background Task
    task = run_simulation_task.delay(csv_text, api_key, config_dict)
    
    return {"task_id": task.id, "status": "Simulation started", "filename": file.filename}

@router.post("/matrix", response_model=MatrixResponse)
async def build_matrix(request: MatrixRequest, api_key: str = Depends(get_api_key)):
    """
    Build a time/distance matrix synchronously.
    Retained for small testing, but /matrix-async is recommended for production.
    """
    # Assuming the first location is the depot or user specified logic
    # Here we just pass all locations
    time_mat, dist_mat = matrix.calculate_matrix(
        request.locations, 
        api_key, 
        request.departure_time_offset_hours
    )
    
    return MatrixResponse(
        locations=request.locations,
        time_matrix=time_mat,
        distance_matrix=dist_mat
    )

@router.post("/optimize", response_model=OptimizationResponse)
async def optimize_routes(request: OptimizationRequest):
    """
    Run the solver.
    """
    # Helper to reconstruct config from request if needed, or stick to simple
    # logic. Since solver refactor, solve_cvrp is gone.
    # We should probably use solve_l2_ortools or something simple here.
    # For now, let's just return 501.
    raise HTTPException(status_code=501, detail="This endpoint is being refactored. Use /simulation/upload-csv.")
