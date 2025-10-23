import copy
import random
from collections import deque
from optimization_solver_new import solve_vrp_with_capacity # We import our new engine

# --- Helper Function ---

def calculate_raw_route_time(stop_indices, time_matrix):
    """
    Calculates the total travel time (in seconds) for a list of stop indices.
    Assumes depot is start (0) and end (0).
    e.g., [5, 3] -> time(0,5) + time(5,3) + time(3,0)
    """
    if not stop_indices:
        return 0
    
    total_time = 0
    last_idx = 0 # Start at depot
    
    for stop_idx in stop_indices:
        total_time += time_matrix[last_idx][stop_idx]
        last_idx = stop_idx
        
    total_time += time_matrix[last_idx][0] # Return to depot
    return total_time

# --- Main Cost Calculation Functions ---

def calculate_route_cost(route_orders, time_matrix):
    """
    Calculates the travel time (in minutes) for a route
    represented by a list of order objects.
    """
    if not route_orders:
        return 0
        
    # Get unique stop indices, preserving insertion order
    stop_indices = list(dict.fromkeys([order['index'] for order in route_orders]))
    
    # Use the helper to get time in seconds
    time_seconds = calculate_raw_route_time(stop_indices, time_matrix)
    
    return time_seconds / 60.0 # Convert to minutes

def calculate_total_cost(routes_dict, time_matrix):
    """
    Calculates the total fleet cost (in minutes) for a dictionary
    of routes (represented by lists of order objects).
    """
    total_cost = 0
    for route_orders in routes_dict.values():
        total_cost += calculate_route_cost(route_orders, time_matrix)
    return total_cost

# --- LAYER 1: IMMEDIATE ASSIGNMENT (Greedy + Tabu) ---

def _greedy_insert_capacity(new_order, current_routes, time_matrix, 
                           vehicle_capacity, max_route_duration_mins):
    """
    (This was the old assign_new_order_realtime function)
    Finds the best single insertion point (or new vehicle) for a new order.
    """
    best_cost_increase = float('inf')
    best_vehicle = -1
    best_insertion_idx = -1 # We don't use this for simple append, but good to have
    
    new_order_idx = new_order['index']
    new_order_demand = new_order['demand']

    # 1. Try to find the "cheapest" insertion in an EXISTING route
    for v_id, route_orders in current_routes.items():
        
        current_load = sum(o['demand'] for o in route_orders)
        
        # --- Constraint 1: Check Capacity ---
        if current_load + new_order_demand > vehicle_capacity:
            continue # This vehicle is too full

        # Get current unique stops
        stop_indices = list(dict.fromkeys([o['index'] for o in route_orders]))
        original_cost = calculate_raw_route_time(stop_indices, time_matrix)
        
        # ---
        # Note: A true "best insertion" would try inserting at every *index*.
        # For a fast L1, we often just check "appending" to the route.
        # Let's adapt your original logic which tried every index.
        # ---
        
        # Try inserting the new order at every possible position in the *order list*
        for i in range(len(route_orders) + 1):
            
            # Create a potential new list of *orders*
            temp_route_orders = route_orders[:i] + [new_order] + route_orders[i:]
            
            # Get the *unique stop indices* from this new order list
            new_unique_stops = list(dict.fromkeys([o['index'] for o in temp_route_orders]))
            
            new_cost = calculate_raw_route_time(new_unique_stops, time_matrix)
            
            # --- Constraint 2: Check Duration ---
            if (new_cost / 60.0) > max_route_duration_mins:
                continue # This new route would be too long
                
            cost_increase = new_cost - original_cost
            
            if cost_increase < best_cost_increase:
                best_cost_increase = cost_increase
                best_vehicle = v_id
                best_insertion_idx = i # Now we store the index

    # 2. If we found a good insertion, return the new state
    if best_vehicle != -1:
        new_routes_state = copy.deepcopy(current_routes)
        new_routes_state[best_vehicle].insert(best_insertion_idx, new_order)
        return new_routes_state, "Best Insertion"

    # 3. If no insertion worked, try to put it in an EMPTY vehicle
    cost_of_new_route = calculate_raw_route_time([new_order_idx], time_matrix)
    duration_mins = cost_of_new_route / 60.0
    
    if (new_order_demand <= vehicle_capacity) and (duration_mins <= max_route_duration_mins):
        # Find the first empty vehicle
        for v_id, route_orders in current_routes.items():
            if not route_orders:
                new_routes_state = copy.deepcopy(current_routes)
                new_routes_state[v_id].append(new_order)
                return new_routes_state, "New Vehicle"

    # 4. If all else fails, return None
    return None, "Failed"


def log_vehicle_changes(old_routes, new_routes, assigned_order, method, timestamp, time_matrix , all_locations , global_route_log):
    """
    Compares route states and logs completed/changed trips to the global log.
    This is a simplified logger.
    """
    # global global_route_log
    
    # This logic assumes a route is "changed" if the list of orders is different.
    # We log the *new* route that was created.
    
    # Find which vehicle was changed
    vehicle_id = -1
    for v_id, new_route_orders in new_routes.items():
        if not new_route_orders:
            continue
        
        # Check if this order is in the new route
        if assigned_order['id'] in [o['id'] for o in new_route_orders]:
            vehicle_id = v_id
            
            # Optimization: only log if the route is *new* or *different*
            old_route_ids = [o['id'] for o in old_routes.get(v_id, [])]
            new_route_ids = [o['id'] for o in new_route_orders]
            
            if old_route_ids != new_route_ids:
                route_cost = calculate_route_cost(new_route_orders, time_matrix)
                total_demand = sum(o['demand'] for o in new_route_orders)
                unique_stops = list(dict.fromkeys([o['index'] for o in new_route_orders]))
                
                # Log this new/updated trip
                global_route_log.append({
                    "vehicle_id": v_id,
                    "timestamp": timestamp,
                    "trigger_order": assigned_order['id'],
                    "method": method,
                    "stops": len(unique_stops),
                    "demand": total_demand,
                    "duration_min": route_cost,
                    "stop_names": [all_locations[idx]['original_address'].split(',')[0] for idx in unique_stops]
                })
            break # Stop after finding the vehicle that changed
def _tabu_search_capacity(initial_solution, time_matrix, 
                         vehicle_capacity, max_route_duration_mins,
                         iterations=50, tabu_tenure=10):
    """
    (Adapted from your v1)
    Performs a Tabu Search (2-opt swap) on routes made of *order objects*.
    It swaps *orders* in the list, and calculate_route_cost handles the
    change in path cost automatically.
    """
    if not initial_solution: 
        return None
        
    best_solution = copy.deepcopy(initial_solution)
    best_cost = calculate_total_cost(best_solution, time_matrix)
    current_solution = copy.deepcopy(initial_solution)
    tabu_list = deque(maxlen=tabu_tenure)
    
    for _ in range(iterations):
        neighborhood = []
        
        # Find all valid swaps
        for vehicle_id, route_orders in current_solution.items():
            if len(route_orders) > 1:
                for i in range(len(route_orders)):
                    for j in range(i + 1, len(route_orders)):
                        
                        # Get the *location indices* of the orders
                        order_i_idx = route_orders[i]['index']
                        order_j_idx = route_orders[j]['index']
                        
                        # Don't swap orders for the same location
                        if order_i_idx == order_j_idx:
                            continue
                        
                        # Check tabu list (uses location indices)
                        if (order_i_idx, order_j_idx) in tabu_list or (order_j_idx, order_i_idx) in tabu_list:
                            continue
                            
                        # Create neighbor by swapping *orders*
                        neighbor_route_orders = route_orders[:]
                        neighbor_route_orders[i], neighbor_route_orders[j] = neighbor_route_orders[j], neighbor_route_orders[i]
                        
                        # Check duration constraint
                        if calculate_route_cost(neighbor_route_orders, time_matrix) <= max_route_duration_mins:
                            # (Capacity is unchanged by a swap)
                            neighborhood.append((vehicle_id, neighbor_route_orders, (order_i_idx, order_j_idx)))
        
        if not neighborhood:
            break # No valid moves found

        # Find the best move in the neighborhood
        best_neighbor_vehicle, best_neighbor_route, best_neighbor_cost_change, best_tabu_move = -1, None, float('inf'), None
        
        for vehicle_id, neighbor_route_orders, tabu_move in neighborhood:
            cost_change = calculate_route_cost(neighbor_route_orders, time_matrix) - calculate_route_cost(current_solution[vehicle_id], time_matrix)
            
            if cost_change < best_neighbor_cost_change:
                best_neighbor_cost_change = cost_change
                best_neighbor_vehicle = vehicle_id
                best_neighbor_route = neighbor_route_orders
                best_tabu_move = tabu_move
                
        if best_neighbor_vehicle != -1:
            # Apply the best move
            current_solution[best_neighbor_vehicle] = best_neighbor_route
            tabu_list.append(best_tabu_move)
            
            current_cost = calculate_total_cost(current_solution, time_matrix)
            if current_cost < best_cost:
                best_solution = copy.deepcopy(current_solution)
                best_cost = current_cost
                
    return best_solution

# --- NEW MAIN L1 Function ---
def assign_new_order_realtime(new_order, current_routes, time_matrix, 
                            vehicle_capacity, max_route_duration_mins):
    """
    (Adapted from your v1)
    Orchestrator for Layer 1 assignment.
    1. Runs a greedy insertion.
    2. Runs a Tabu Search refinement.
    3. Returns the best solution found.
    """
    
    # 1. Find initial solution with Greedy Insertion
    greedy_solution, method = _greedy_insert_capacity(
        new_order, current_routes, time_matrix, 
        vehicle_capacity, max_route_duration_mins
    )
    
    if greedy_solution is None:
        return None, "Failed"
        
    greedy_total_cost = calculate_total_cost(greedy_solution, time_matrix)
    
    # 2. Refine the greedy solution with Tabu Search
    tabu_solution = _tabu_search_capacity(
        greedy_solution, time_matrix, 
        vehicle_capacity, max_route_duration_mins,
        iterations=50, tabu_tenure=7 # L1 should be fast
    )
    
    if tabu_solution:
        tabu_total_cost = calculate_total_cost(tabu_solution, time_matrix)
        
        # Compare costs and return the best
        if tabu_total_cost < greedy_total_cost - 0.1: # Use 0.1 min threshold
            return tabu_solution, "Tabu Search"
    
    # If tabu failed or wasn't better, return the greedy one
    return greedy_solution, method # "Best Insertion" or "New Vehicle"
    

# --- Main Function 3: Layer 2 (Batch VRP Optimization) ---

def batch_optimization_vrp(current_routes, pending_orders, time_matrix, 
                         num_vehicles, vehicle_capacity, max_route_duration_mins):
    """
    Re-optimizes all current routes AND tries to include pending orders.
    This is the main Layer 2 function.
    (Unchanged from previous capacity-aware version)
    """
    
    # 1. Combine all orders (from routes + pending) into one big list
    all_orders_to_assign = pending_orders[:]
    for route in current_routes.values():
        all_orders_to_assign.extend(route)
        
    if not all_orders_to_assign:
        # Nothing to do
        return {i: [] for i in range(num_vehicles)}, []

    # 2. Create the "Solver Data Model"
    
    # We need to map our "original" location indices (e.g., 3, 5, 20)
    # to "solver" indices (e.g., 1, 2, 3). Depot is always index 0.
    
    # Get all unique "original" stop indices
    original_stop_indices = sorted(list(set([o['index'] for o in all_orders_to_assign])))
    
    # Create the list of all locations for the solver (Depot + Stops)
    solver_locations = [0] + original_stop_indices 
    
    # Create mapping dictionaries
    # {orig_idx: solver_idx} e.g., {0:0, 3:1, 5:2, 20:3}
    map_orig_to_solver = {orig_idx: i for i, orig_idx in enumerate(solver_locations)}
    # {solver_idx: orig_idx} e.g., {0:0, 1:3, 2:5, 3:20}
    map_solver_to_orig = {i: orig_idx for i, orig_idx in enumerate(solver_locations)}

    num_solver_locs = len(solver_locations)

    # 3. Build the inputs for the solver engine
    
    # a) Solver Time Matrix (a smaller matrix)
    solver_time_matrix = [[0] * num_solver_locs for _ in range(num_solver_locs)]
    for i in range(num_solver_locs):
        for j in range(num_solver_locs):
            orig_i = map_solver_to_orig[i]
            orig_j = map_solver_to_orig[j]
            solver_time_matrix[i][j] = time_matrix[orig_i][orig_j]
            
    # b) Solver Demands List (one entry for each solver location)
    solver_demands = [0] * num_solver_locs
    # This holds orders grouped by their *original* index
    order_pool = {idx: [] for idx in original_stop_indices}
    
    for order in all_orders_to_assign:
        order_orig_idx = order['index']
        solver_idx = map_orig_to_solver[order_orig_idx]
        
        # Add demand to the solver demand list
        solver_demands[solver_idx] += order['demand']
        # Add the full order object to our pool, to rebuild routes later
        order_pool[order_orig_idx].append(order)

    # c) Vehicle Capacities & Durations
    vehicle_capacities = [vehicle_capacity] * num_vehicles
    # Solver needs duration in seconds
    vehicle_max_durations_sec = [int(max_route_duration_mins * 60)] * num_vehicles

    # 4. Call the Solver Engine!
    solution_routes_solver, unassigned_solver_indices = solve_vrp_with_capacity(
        solver_time_matrix,
        solver_demands,
        vehicle_capacities,
        vehicle_max_durations_sec,
        num_vehicles
    )
    
    # 5. Parse the solution (convert solver indices back to order objects)
    
    new_optimized_routes = {i: [] for i in range(num_vehicles)}
    
    for v_id, vehicle_route_solver in enumerate(solution_routes_solver):
        for solver_stop_idx in vehicle_route_solver:
            # Convert solver index (e.g., 2) back to original index (e.g., 5)
            original_stop_idx = map_solver_to_orig[solver_stop_idx]
            
            # Get all orders for this stop from our pool
            # .pop() ensures we don't assign the same orders twice
            orders_for_this_stop = order_pool.pop(original_stop_idx, [])
            
            if orders_for_this_stop:
                new_optimized_routes[v_id].extend(orders_for_this_stop)

    # 6. Find any orders that were *not* assigned
    # Any orders left in the pool (or returned by solver) are unassigned
    final_unassigned_orders = []
    for orig_idx_solver in unassigned_solver_indices:
        # Convert solver index back to original index
        original_stop_idx = map_solver_to_orig.get(orig_idx_solver)
        if original_stop_idx:
            orders = order_pool.pop(original_stop_idx, [])
            final_unassigned_orders.extend(orders)
        
    # Also add any remaining in the pool (should be empty, but good practice)
    for orders in order_pool.values():
        final_unassigned_orders.extend(orders)

    return new_optimized_routes, final_unassigned_orders

