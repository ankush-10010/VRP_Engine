import math
import random
import copy
import time
from typing import List, Dict, Any, Tuple, Optional
from collections import deque
from datetime import datetime

from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

from ..models.schemas import Order, VehicleRoute, RouteStep, OptimizationResponse, SimulationConfig

# --- Helper Functions ---

def calculate_raw_route_distance(stop_indices: List[int], distance_matrix: List[List[float]]) -> float:
    """Calculates total distance (km) for a list of location indices."""
    if not stop_indices:
        return 0.0
    
    total_distance = 0.0
    last_idx = 0 # Start at depot
    
    for stop_idx in stop_indices:
         if last_idx >= len(distance_matrix) or stop_idx >= len(distance_matrix[last_idx]):
             return float('inf')
         total_distance += distance_matrix[last_idx][stop_idx]
         last_idx = stop_idx
         
    # Return to depot
    if last_idx >= len(distance_matrix):
        return float('inf')
    total_distance += distance_matrix[last_idx][0]
    return total_distance

def calculate_raw_route_time(stop_indices: List[int], time_matrix: List[List[float]]) -> float:
    """Calculates total time (seconds/minutes depending on matrix unit) for stop indices."""
    if not stop_indices:
        return 0.0
    
    total_time = 0.0
    last_idx = 0
    
    for stop_idx in stop_indices:
         if last_idx >= len(time_matrix) or stop_idx >= len(time_matrix[last_idx]):
             return float('inf')
         total_time += time_matrix[last_idx][stop_idx]
         last_idx = stop_idx
         
    # Return to depot
    total_time += time_matrix[last_idx][0]
    return total_time

def calculate_total_fleet_cost(routes_dict: Dict[int, List[Dict]], 
                               distance_matrix: List[List[float]],
                               config: SimulationConfig) -> Tuple[float, int, float]:
    """Calculates total cost, used trucks, and total distance."""
    total_distance = 0.0
    num_trucks_used = 0
    
    for _, route_orders in routes_dict.items():
        if route_orders:
            num_trucks_used += 1
            stop_indices = list(dict.fromkeys([o['index'] for o in route_orders]))
            dist = calculate_raw_route_distance(stop_indices, distance_matrix)
            if dist != float('inf'):
                total_distance += dist
                
    total_cost = (config.fixed_cost_per_truck * num_trucks_used) + \
                 (config.variable_cost_per_km * total_distance)
                 
    return total_cost, num_trucks_used, total_distance

def calculate_route_cost(route_orders: List[Dict], time_matrix: List[List[float]]) -> float:
    """Calculates route duration in minutes (assuming matrix is in seconds)."""
    if not route_orders:
        return 0.0
    stop_indices = list(dict.fromkeys([o['index'] for o in route_orders]))
    time_seconds = calculate_raw_route_time(stop_indices, time_matrix)
    return time_seconds / 60.0

def calculate_total_cost(routes_dict: Dict[int, List[Dict]], time_matrix: List[List[float]]) -> float:
    """Calculates total duration (in minutes) for all routes."""
    total = 0.0
    for route in routes_dict.values():
        total += calculate_route_cost(route, time_matrix)
    return total

# --- LAYER 1: GREEDY + TABU ---

def _greedy_insert_capacity(new_order: Dict, current_routes: Dict[int, List[Dict]], 
                           time_matrix: List[List[float]], config: SimulationConfig) -> Tuple[Optional[Dict], str]:
    best_cost_increase = float('inf')
    best_vehicle = -1
    best_insertion_idx = -1
    
    new_order_idx = new_order['index']
    new_order_demand = new_order['demand']
    
    # 1. Try existing routes
    for v_id, route_orders in current_routes.items():
        if not route_orders: continue
        
        current_load = sum(o['demand'] for o in route_orders)
        if current_load + new_order_demand > config.vehicle_capacity:
            continue
            
        stop_indices = list(dict.fromkeys([o['index'] for o in route_orders]))
        original_cost = calculate_raw_route_time(stop_indices, time_matrix)
        
        for i in range(len(route_orders) + 1):
            temp_route = route_orders[:i] + [new_order] + route_orders[i:]
            new_indices = list(dict.fromkeys([o['index'] for o in temp_route]))
            new_cost = calculate_raw_route_time(new_indices, time_matrix)
            
            # Duration check (minutes)
            if (new_cost / 60.0) > 200: # Hardcoded max duration from legacy or config
                continue
                
            increase = new_cost - original_cost
            if increase < best_cost_increase:
                best_cost_increase = increase
                best_vehicle = v_id
                best_insertion_idx = i
                
    if best_vehicle != -1:
        new_routes = copy.deepcopy(current_routes)
        new_routes[best_vehicle].insert(best_insertion_idx, new_order)
        return new_routes, "Best Insertion"
        
    # 2. Try empty vehicle
    new_route_cost = calculate_raw_route_time([new_order_idx], time_matrix)
    if (new_order_demand <= config.vehicle_capacity) and ((new_route_cost/60.0) <= 200):
        for v_id, route_orders in current_routes.items():
            if not route_orders:
                new_routes = copy.deepcopy(current_routes)
                new_routes[v_id].append(new_order)
                return new_routes, "New Vehicle"
                
    return None, "Failed"

def _tabu_search_capacity(initial_solution: Dict, time_matrix: List[List[float]], 
                         config: SimulationConfig, iterations: int = 50) -> Dict:
    if not initial_solution: return None
    
    best_solution = copy.deepcopy(initial_solution)
    best_cost = calculate_total_cost(best_solution, time_matrix)
    current_solution = copy.deepcopy(initial_solution)
    tabu_list = deque(maxlen=7)
    
    for _ in range(iterations):
        neighborhood = []
        for v_id, route in current_solution.items():
            if len(route) > 1:
                for i in range(len(route)):
                    for j in range(i + 1, len(route)):
                        idx_i = route[i]['index']
                        idx_j = route[j]['index']
                        if idx_i == idx_j: continue
                        if (idx_i, idx_j) in tabu_list or (idx_j, idx_i) in tabu_list: continue
                        
                        neighbor = route[:]
                        neighbor[i], neighbor[j] = neighbor[j], neighbor[i]
                        
                        if calculate_route_cost(neighbor, time_matrix) <= 200:
                            neighborhood.append((v_id, neighbor, (idx_i, idx_j)))
                            
        if not neighborhood: break
        
        best_n_vehicle = -1
        best_n_route = None
        best_n_cost_change = float('inf')
        best_tabu_move = None
        
        for v_id, n_route, move in neighborhood:
            change = calculate_route_cost(n_route, time_matrix) - calculate_route_cost(current_solution[v_id], time_matrix)
            if change < best_n_cost_change:
                best_n_cost_change = change
                best_n_vehicle = v_id
                best_n_route = n_route
                best_tabu_move = move
                
        if best_n_vehicle != -1:
            current_solution[best_n_vehicle] = best_n_route
            tabu_list.append(best_tabu_move)
            cur_cost = calculate_total_cost(current_solution, time_matrix)
            if cur_cost < best_cost:
                best_solution = copy.deepcopy(current_solution)
                best_cost = cur_cost
                
    return best_solution

def solve_l1_greedy_tabu(new_order: Dict, current_routes: Dict[int, List[Dict]], 
                        time_matrix: List[List[float]], config: SimulationConfig) -> Tuple[Optional[Dict], str]:
    """Layer 1: Real-time incremental assignment."""
    greedy_sol, method = _greedy_insert_capacity(new_order, current_routes, time_matrix, config)
    if not greedy_sol:
        return None, "Failed"
        
    greedy_cost = calculate_total_cost(greedy_sol, time_matrix)
    
    tabu_sol = _tabu_search_capacity(greedy_sol, time_matrix, config)
    if tabu_sol:
        tabu_cost = calculate_total_cost(tabu_sol, time_matrix)
        if tabu_cost < greedy_cost - 0.1:
            return tabu_sol, "Tabu Search"
            
    return greedy_sol, method

# --- LAYER 2: OR-TOOLS VRP ---

def solve_l2_ortools(current_routes: Dict[int, List[Dict]], pending_orders: List[Dict],
                    time_matrix: List[List[float]], config: SimulationConfig) -> Tuple[Dict[int, List[Dict]], List[Dict]]:
    """Layer 2: Batch optimization using OR-Tools."""
    
    # Flatten all orders
    all_orders = pending_orders[:]
    for route in current_routes.values():
        all_orders.extend(route)
        
    if not all_orders:
        return {i: [] for i in range(config.num_vehicles)}, []
        
    # Map orders to "solver indices" (Depot=0, Order1=1, Order2=2...)
    map_solver_to_order = {i+1: order for i, order in enumerate(all_orders)}
    num_solver_locs = len(all_orders) + 1
    
    # Build Solver Matrix (Order-to-Order)
    solver_matrix = [[0] * num_solver_locs for _ in range(num_solver_locs)]
    for i in range(num_solver_locs):
        for j in range(num_solver_locs):
            if i == j: continue
            
            idx_i = 0 if i == 0 else map_solver_to_order[i]['index']
            idx_j = 0 if j == 0 else map_solver_to_order[j]['index']
            
            solver_matrix[i][j] = time_matrix[idx_i][idx_j]
            
    demands = [0] + [o['demand'] for o in all_orders]
    
    # OR-Tools Setup
    manager = pywrapcp.RoutingIndexManager(num_solver_locs, config.num_vehicles, 0)
    routing = pywrapcp.RoutingModel(manager)
    
    def time_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        # Service time: 1 min per stop (legacy behavior)
        service = 1 if from_node != 0 else 0
        return int(solver_matrix[from_node][to_node]) + service
        
    transit_idx = routing.RegisterTransitCallback(time_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_idx)
    
    def demand_callback(from_index):
        return demands[manager.IndexToNode(from_index)]
    
    demand_idx = routing.RegisterUnaryTransitCallback(demand_callback)
    routing.AddDimensionWithVehicleCapacity(
        demand_idx, 0, [config.vehicle_capacity]*config.num_vehicles, True, 'Capacity'
    )
    
    routing.AddDimension(
        transit_idx, 30, 999999, False, 'Time' # Large max duration for now
    )
    time_dim = routing.GetDimensionOrDie('Time')
    for i in range(config.num_vehicles):
        time_dim.SetCumulVarSoftUpperBound(routing.End(i), 200 * 60, 0) # 200 mins max
        
    # Penalties for dropped nodes
    for i in range(1, num_solver_locs):
        routing.AddDisjunction([manager.NodeToIndex(i)], 1000000)
        
    search_params = pywrapcp.DefaultRoutingSearchParameters()
    search_params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    search_params.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    search_params.time_limit.FromSeconds(3)
    
    solution = routing.SolveWithParameters(search_params)
    
    if not solution:
        print(f"[SOLVER] OR-Tools failed to find a solution. Status: {routing.status()}")
        # Inspect Matrix for issues
        max_time = max(max(row) for row in solver_matrix)
        print(f"[SOLVER] Max time in matrix: {max_time}")
        
    new_routes = {i: [] for i in range(config.num_vehicles)}
    unassigned = []
    
    if solution:
        print(f"[SOLVER] Solution Found!")
        for v_id in range(config.num_vehicles):
            index = routing.Start(v_id)
            while not routing.IsEnd(index):
                node = manager.IndexToNode(index)
                if node != 0:
                    new_routes[v_id].append(map_solver_to_order[node])
                index = solution.Value(routing.NextVar(index))
                
        # Find unassigned
        assigned_ids = set()
        for r in new_routes.values():
            for o in r:
                assigned_ids.add(id(o)) # Use obj id or unique logic
                
        # Re-verify based on original list (safer)
        for order in all_orders:
            # This logic is weak if we have duplicate objects. 
            # Ideally order['order_id'] should be used.
            pass 
            
        # Proper unassigned logic:
        # Check every node in the model
        for node in range(1, num_solver_locs):
            if routing.IsStart(solution.Value(routing.NextVar(manager.NodeToIndex(node)))):
                # It's unassigned if next var is itself? No, IsStart check logic.
                # Simplest: check if it appears in any route we built.
                pass
                
        # Better: OR-Tools lets you iterate unassigned.
        # But our simple route builder above is exhaustive for assigned.
        # So we just diff against all_orders.
        
        flat_assigned = []
        for r in new_routes.values(): flat_assigned.extend(r)
        flat_assigned_ids = set(o['id'] for o in flat_assigned)
        
        for order in all_orders:
            if order['id'] not in flat_assigned_ids:
                unassigned.append(order)
                
    else:
        unassigned = all_orders
        
    return new_routes, unassigned

# --- LAYER 3: ALNS ---

def _repair_greedy(partial_routes, request_bank, time_matrix, config):
    """ALNS Repair: Insert orders greedily."""
    repaired = copy.deepcopy(partial_routes)
    uninserted = []
    random.shuffle(request_bank)
    
    for order in request_bank:
        best_increase = float('inf')
        best_v, best_i = -1, -1
        
        for v_id, route in repaired.items():
            load = sum(o['demand'] for o in route)
            if load + order['demand'] > config.vehicle_capacity: continue
            
            indices = list(dict.fromkeys([o['index'] for o in route]))
            orig_cost = calculate_raw_route_time(indices, time_matrix)
            
            for i in range(len(route)+1):
                temp = route[:i] + [order] + route[i:]
                new_inds = list(dict.fromkeys([o['index'] for o in temp]))
                new_cost = calculate_raw_route_time(new_inds, time_matrix)
                if (new_cost/60.0) <= 200:
                    diff = new_cost - orig_cost
                    if diff < best_increase:
                        best_increase = diff
                        best_v, best_i = v_id, i
                        
        if best_v != -1:
            repaired[best_v].insert(best_i, order)
        else:
            # Try new route
            new_cost = calculate_raw_route_time([order['index']], time_matrix)
            if (order['demand'] <= config.vehicle_capacity) and ((new_cost/60.0) <= 200):
                 for v in range(config.num_vehicles):
                     if not repaired[v]:
                         repaired[v].append(order)
                         break
                 else:
                     uninserted.append(order)
            else:
                uninserted.append(order)
                
    return repaired, uninserted
    
def _destroy_random(routes, num_remove):
    """ALNS Destroy: Remove random orders."""
    partial = copy.deepcopy(routes)
    removed = []
    
    candidates = []
    for v_id, route in partial.items():
        for i, order in enumerate(route):
            candidates.append((v_id, i, order))
            
    if not candidates: return partial, []
    
    to_remove = random.sample(candidates, min(num_remove, len(candidates)))
    
    # Sort by index desc to remove safely
    to_remove.sort(key=lambda x: x[1], reverse=True)
    
    # Group by vehicle
    rem_map = {}
    for v, i, o in to_remove:
        if v not in rem_map: rem_map[v] = []
        rem_map[v].append(i)
        removed.append(o)
        
    for v, indices in rem_map.items():
        for i in indices:
            del partial[v][i]
            
    return partial, removed

def solve_l3_alns(current_routes: Dict[int, List[Dict]], pending_orders: List[Dict],
                 time_matrix: List[List[float]], distance_matrix: List[List[float]], 
                 config: SimulationConfig) -> Tuple[Dict[int, List[Dict]], List[Dict]]:
    """Layer 3: ALNS Optimization."""
    
    # Initial Solution: Greedy repair of everything
    initial_full_pending = pending_orders[:]
    for r in current_routes.values(): initial_full_pending.extend(r)
    
    start_routes = {i: [] for i in range(config.num_vehicles)}
    curr_sol, curr_unassigned = _repair_greedy(start_routes, initial_full_pending, time_matrix, config)
    
    curr_cost, _, _ = calculate_total_fleet_cost(curr_sol, distance_matrix, config)
    curr_obj = curr_cost + (len(curr_unassigned) * config.fixed_cost_per_truck * 10)
    
    best_sol = curr_sol
    best_unassigned = curr_unassigned
    best_obj = curr_obj
    
    temp = 1000
    cooling = 0.995
    
    iterations = config.alns_iterations
    
    for i in range(iterations):
        # Only 1 operator pair implemented for now
        num_assigned = sum(len(r) for r in curr_sol.values())
        if num_assigned == 0: break
        
        # Destroy
        pct = random.uniform(config.alns_destroy_min_pct, config.alns_destroy_max_pct)
        num_rem = max(1, int(num_assigned * pct))
        partial, bank = _destroy_random(curr_sol, num_rem)
        bank.extend(curr_unassigned)
        
        # Repair
        new_sol, new_un = _repair_greedy(partial, bank, time_matrix, config)
        
        new_cost, _, _ = calculate_total_fleet_cost(new_sol, distance_matrix, config)
        new_obj = new_cost + (len(new_un) * config.fixed_cost_per_truck * 10)
        
        delta = new_obj - curr_obj
        accept = False
        
        if delta < 0:
            accept = True
            if new_obj < best_obj:
                best_sol = copy.deepcopy(new_sol)
                best_unassigned = new_un[:]
                best_obj = new_obj
        else:
             if random.random() < math.exp(-delta / temp):
                 accept = True
                 
        if accept:
            curr_sol = new_sol
            curr_unassigned = new_un
            curr_obj = new_obj
            
        temp *= cooling
        
    return best_sol, best_unassigned
