from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict

class Location(BaseModel):
    original_address: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    formatted_address: Optional[str] = None
    
class GeocodeRequest(BaseModel):
    addresses: List[str]

class GeocodeResponse(BaseModel):
    locations: List[Location]
    failed_addresses: List[str]

class MatrixRequest(BaseModel):
    locations: List[Location]
    depot_index: int = 0
    departure_time_offset_hours: int = 24 # Default to 24h later

class MatrixResponse(BaseModel):
    locations: List[Location]
    time_matrix: List[List[float]]
    distance_matrix: List[List[float]]

class Order(BaseModel):
    order_id: str
    timestamp: int
    location: Location
    demand: int = 1
    # Add other fields as necessary

class OptimizationRequest(BaseModel):
    orders: List[Order]
    matrix: MatrixResponse # Pass the matrix directly or use an ID if we had a DB
    num_vehicles: int = 10
    vehicle_capacity: int = 20

class RouteStep(BaseModel):
    stop_index: int
    address: str
    lat: float
    lng: float
    arrival_time_min: float
    departure_time_min: float

class VehicleRoute(BaseModel):
    vehicle_id: int
    steps: List[RouteStep]
    total_cost: float
    total_time_min: float

class OptimizationLogEntry(BaseModel):
    iteration: int
    timestamp: str # "HH:MM:SS"
    l2_cost: float
    l3_cost: float
    winner: str # "L2" or "L3"
    improvement_pct: float

class SimulationEvent(BaseModel):
    time: str # "HH:MM"
    type: str # "new_order", "assignment", "optimization", "rejected"
    description: str
    success: Optional[bool] = None

class AnalyticsMetrics(BaseModel):
    total_orders: int
    assigned_orders: int
    success_rate: float
    avg_wait_time_min: float
    fleet_utilization_pct: float
    total_distance_km: float

class OptimizationResponse(BaseModel):
    routes: List[VehicleRoute]
    unassigned_orders: List[str] # List of order IDs
    total_fleet_cost: float
    analytics: Optional[AnalyticsMetrics] = None
    optimization_log: List[OptimizationLogEntry] = []
    events: List[SimulationEvent] = []

class SimulationConfig(BaseModel):
    # Fleet Settings
    num_vehicles: int = 10
    vehicle_capacity: int = 20
    
    # Cost Settings
    fixed_cost_per_truck: float = 5000.0
    variable_cost_per_km: float = 15.0
    
    # Hybrid Solver Settings
    layer_2_interval: int = 600 # Seconds
    
    # ALNS Settings (Layer 3)
    alns_enabled: bool = True
    alns_iterations: int = 5000
    alns_segment_length: int = 50
    alns_reaction_factor: float = 0.7
    alns_destroy_min_pct: float = 0.15
    alns_destroy_max_pct: float = 0.40
