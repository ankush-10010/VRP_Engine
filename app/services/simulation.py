from typing import List, Dict, Any, Tuple
import copy
from datetime import datetime, timedelta

from ..models.schemas import (
    Order, Location, VehicleRoute, RouteStep, SimulationConfig, 
    OptimizationResponse, OptimizationLogEntry, SimulationEvent, AnalyticsMetrics
)
from . import solver

def format_time(minutes_from_start: int, start_hour: int = 8) -> str:
    """Formats minutes from start into HH:MM string."""
    total_minutes = (start_hour * 60) + minutes_from_start
    h = (total_minutes // 60) % 24
    m = total_minutes % 60
    return f"{h:02d}:{m:02d}"

def run_hybrid_simulation(orders: List[Order], 
                          time_matrix: List[List[float]], 
                          distance_matrix: List[List[float]],
                          config: SimulationConfig) -> OptimizationResponse:
    """
    Simulates the delivery day, processing orders as they 'arrive'.
    Tracks analytics and events for frontend visualization.
    """
    
    # --- 1. Setup ---
    if not orders:
        return OptimizationResponse(routes=[], unassigned_orders=[], total_fleet_cost=0.0)
        
    start_time = min(o.timestamp for o in orders)
    end_time = max(o.timestamp for o in orders) + 3600 
    
    orders_by_minute = {}
    for order in orders:
        minute = int((order.timestamp - start_time) / 60)
        if minute not in orders_by_minute:
            orders_by_minute[minute] = []
        orders_by_minute[minute].append(order)
        
    # State
    current_routes: Dict[int, List[Dict]] = {i: [] for i in range(config.num_vehicles)}
    pending_orders: List[Dict] = []
    
    # Logs
    optimization_log: List[OptimizationLogEntry] = []
    events: List[SimulationEvent] = []
    
    # Internal Maps
    input_orders_mapped = []
    for i, pydantic_order in enumerate(orders):
        input_orders_mapped.append({
            "id": pydantic_order.order_id,
            "index": i + 1,
            "demand": pydantic_order.demand,
            "timestamp": pydantic_order.timestamp,
            "original_order": pydantic_order
        })
        
    events_by_minute = {}
    for order in input_orders_mapped:
        minute = int((order['timestamp'] - start_time) / 60)
        if minute not in events_by_minute: events_by_minute[minute] = []
        events_by_minute[minute].append(order)
        
    simulation_duration_minutes = int((end_time - start_time) / 60)
    last_opt_time = -9999
    
    # Metrics State
    total_wait_time = 0.0
    wait_time_counts = 0
    assigned_order_ids = set()
    
    # --- 2. Time Loop ---
    for current_minute in range(0, simulation_duration_minutes + 1):
        formatted_curr_time = format_time(current_minute)
        
        # A. New Orders Arrive
        if current_minute in events_by_minute:
            new_arrivals = events_by_minute[current_minute]
            for new_order in new_arrivals:
                events.append(SimulationEvent(
                    time=formatted_curr_time,
                    type="new_order",
                    description=f"New Order #{new_order['id']} (Demand: {new_order['demand']})",
                    success=True
                ))
                
                # Layer 1: Immediate Assignment
                new_routes_l1, method = solver.solve_l1_greedy_tabu(new_order, current_routes, time_matrix, config)
                
                if new_routes_l1:
                    current_routes = new_routes_l1
                    assigned_order_ids.add(new_order['id'])
                    events.append(SimulationEvent(
                        time=formatted_curr_time,
                        type="assignment",
                        description=f"Assigned Order #{new_order['id']} via {method}",
                        success=True
                    ))
                    # Zero wait time for instant assignment (simplification)
                    wait_time_counts += 1
                else:
                    pending_orders.append(new_order)
                    events.append(SimulationEvent(
                        time=formatted_curr_time,
                        type="rejected",
                        description=f"Order #{new_order['id']} queued for batch optimization",
                        success=False
                    ))
                    
        # B. Periodic Re-optimization
        interval_min = config.layer_2_interval / 60.0
        if (current_minute - last_opt_time) >= interval_min:
            last_opt_time = current_minute
            
            # Use Pending orders AND currently assigned orders
            # (In reality, we'd filter committed orders. Here we re-optimize everything not completed)
            # Optimization considers entire current state
            has_active_orders = len(pending_orders) > 0 or any(len(route) > 0 for route in current_routes.values())
            if not has_active_orders:
                 # Skip expensive re-optimization if we have no active orders
                 # This speeds up the simulation significantly during idle periods
                 continue
            from ..core_engine.solvers.factory import SolverFactory

            # --- Solver Execution ---
            
            # Calculate L1 cost before optimization
            l1_cost, _, _ = solver.calculate_total_fleet_cost(current_routes, distance_matrix, config)
            l1_adj_cost = l1_cost + (len(pending_orders) * config.fixed_cost_per_truck * 10)
            
            l2_cost = float('inf')
            l3_cost = float('inf')
            l2_routes, l2_unassigned = {}, []
            l3_routes, l3_unassigned = {}, []
            l2_adj_cost = float('inf')
            l3_adj_cost = float('inf')

            strategy = config.strategy.lower()

            if strategy in ["ortools", "benchmark"]:
                print(f"[SIMULATION] Calling ORToolsSolver...")
                ortools_solver = SolverFactory.create_solver("ortools")
                l2_routes, l2_unassigned = ortools_solver.solve(current_routes, pending_orders, time_matrix, distance_matrix, config)
                print(f"[SIMULATION] ORToolsSolver returned.")
                l2_cost, _, _ = solver.calculate_total_fleet_cost(l2_routes, distance_matrix, config)
                l2_adj_cost = l2_cost + (len(l2_unassigned) * config.fixed_cost_per_truck * 10)

            if strategy in ["alns", "benchmark"] and config.alns_enabled:
                print(f"[SIMULATION] Calling ALNSSolver...")
                alns_solver = SolverFactory.create_solver("alns")
                l3_routes, l3_unassigned = alns_solver.solve(current_routes, pending_orders, time_matrix, distance_matrix, config)
                print(f"[SIMULATION] ALNSSolver returned.")
                l3_cost, _, _ = solver.calculate_total_fleet_cost(l3_routes, distance_matrix, config)
                l3_adj_cost = l3_cost + (len(l3_unassigned) * config.fixed_cost_per_truck * 10)
                
            # Compare
            winner = "L1"
            improvement = 0.0
            
            if strategy == "benchmark":
                best_cost = l1_adj_cost
                if l2_adj_cost < float('inf') and l2_adj_cost < best_cost:
                    best_cost = l2_adj_cost
                    winner = "L2"
                if l3_adj_cost < float('inf') and l3_adj_cost < best_cost:
                    best_cost = l3_adj_cost
                    winner = "L3"
                    
                if winner == "L2":
                    current_routes = l2_routes
                    pending_orders = l2_unassigned
                elif winner == "L3":
                    current_routes = l3_routes
                    pending_orders = l3_unassigned
            elif strategy == "ortools" and l2_adj_cost < float('inf'):
                current_routes = l2_routes
                pending_orders = l2_unassigned
                winner = "L2"
            elif strategy == "alns" and l3_adj_cost < float('inf'):
                current_routes = l3_routes
                pending_orders = l3_unassigned
                winner = "L3"
                
            if winner != "None":
                # Log Analytics
                # Avoid infinite improvement calc
                valid_costs = [c for c in [l2_cost, l3_cost] if c != float('inf')]
                if len(valid_costs) == 2:
                    improvement = ((max(l2_cost, l3_cost) - min(l2_cost, l3_cost)) / max(l2_cost, l3_cost)) * 100
                else:
                    improvement = 0.0
                    
                optimization_log.append(OptimizationLogEntry(
                    iteration=len(optimization_log) + 1,
                    timestamp=formatted_curr_time,
                    l1_cost=l1_adj_cost if l1_adj_cost != float('inf') else 0.0,
                    l2_cost=l2_cost if l2_cost != float('inf') else 0.0,
                    l3_cost=l3_cost if l3_cost != float('inf') else 0.0,
                    winner=winner,
                    improvement_pct=improvement
                ))
                
                final_cost = l1_cost
                if winner == "L2": final_cost = l2_cost
                elif winner == "L3": final_cost = l3_cost
                
                events.append(SimulationEvent(
                    time=formatted_curr_time,
                    type="optimization",
                    description=f"Global Optimization: {winner} won. Cost: {final_cost:.2f}",
                    success=True
                ))
                
                # Update assigned set
                for r in current_routes.values():
                    for o in r:
                        assigned_order_ids.add(o['id'])
                        
    # --- 3. Finalize ---
    
    total_cost, num_trucks, total_dist = solver.calculate_total_fleet_cost(current_routes, distance_matrix, config)
    
    final_routes = []
    total_capacity_used = 0
    
    for v_id, route_orders in current_routes.items():
        if not route_orders: continue
        
        steps = []
        current_time = 0.0 
        last_idx = 0
        
        # Depot Start
        depot_lat = 28.5707  # Hardcoded depot
        depot_lng = 77.3262
        
        steps.append(RouteStep(
            stop_index=0, 
            address="Depot", 
            lat=depot_lat,
            lng=depot_lng,
            arrival_time_min=0, 
            departure_time_min=0
        ))
        
        route_cap = 0
        for order in route_orders:
            idx = order['index']
            travel_sec = time_matrix[last_idx][idx]
            accum_min = current_time + (travel_sec / 60.0)
            
            orig = order['original_order'].location
            
            steps.append(RouteStep(
                stop_index=idx,
                address=orig.original_address,
                lat=orig.latitude or 0.0,
                lng=orig.longitude or 0.0,
                arrival_time_min=accum_min,
                departure_time_min=accum_min + 5
            ))
            
            current_time = accum_min + 5
            last_idx = idx
            route_cap += order['demand']
            
        total_capacity_used += route_cap
        
        # Depot End
        travel_sec = time_matrix[last_idx][0]
        end_min = current_time + (travel_sec / 60.0)
        steps.append(RouteStep(
            stop_index=0, 
            address="Depot",
            lat=depot_lat,
            lng=depot_lng, 
            arrival_time_min=end_min, 
            departure_time_min=end_min
        ))
        
        final_routes.append(VehicleRoute(
            vehicle_id=v_id,
            steps=steps,
            total_cost=0.0,
            total_time_min=end_min
        ))
        
    # Analytics Metrics
    total_orders = len(orders)
    assigned_count = len(assigned_order_ids)
    success_rate = (assigned_count / total_orders * 100) if total_orders > 0 else 0
    
    total_capacity_avail = config.num_vehicles * config.vehicle_capacity
    utilization = (total_capacity_used / total_capacity_avail * 100) if total_capacity_avail > 0 else 0
    
    analytics = AnalyticsMetrics(
        total_orders=total_orders,
        assigned_orders=assigned_count,
        success_rate=success_rate,
        avg_wait_time_min=0.0, # Simplification for now
        fleet_utilization_pct=utilization,
        total_distance_km=total_dist
    )
        
    return OptimizationResponse(
        routes=final_routes, 
        unassigned_orders=[o['id'] for o in pending_orders],
        total_fleet_cost=total_cost,
        analytics=analytics,
        optimization_log=optimization_log,
        events=events
    )
