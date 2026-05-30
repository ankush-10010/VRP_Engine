from typing import Dict, List, Tuple
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

from .base import BaseVRPSolver
from ...models.schemas import SimulationConfig

class ORToolsSolver(BaseVRPSolver):
    def solve(self, 
              current_routes: Dict[int, List[Dict]], 
              pending_orders: List[Dict],
              time_matrix: List[List[float]], 
              distance_matrix: List[List[float]],
              config: SimulationConfig) -> Tuple[Dict[int, List[Dict]], List[Dict]]:
        
        # Flatten all orders
        all_orders = pending_orders[:]
        for route in current_routes.values():
            all_orders.extend(route)
            
        if not all_orders:
            return {i: [] for i in range(config.num_vehicles)}, []
            
        # Map orders to "solver indices" (Depot=0, Order1=1, Order2=2...)
        map_solver_to_order = {i+1: order for i, order in enumerate(all_orders)}
        num_solver_locs = len(all_orders) + 1
        
        # Build Solver Matrices (Time and Distance)
        time_solver_matrix = [[0] * num_solver_locs for _ in range(num_solver_locs)]
        dist_solver_matrix = [[0] * num_solver_locs for _ in range(num_solver_locs)]
        for i in range(num_solver_locs):
            for j in range(num_solver_locs):
                if i == j: continue
                
                idx_i = 0 if i == 0 else map_solver_to_order[i]['index']
                idx_j = 0 if j == 0 else map_solver_to_order[j]['index']
                
                time_solver_matrix[i][j] = time_matrix[idx_i][idx_j]
                # Scale distance by 100 for OR-Tools integer constraints (e.g. 2.54 km -> 254)
                dist_solver_matrix[i][j] = int(distance_matrix[idx_i][idx_j] * 100)
                
        demands = [0] + [o['demand'] for o in all_orders]
        
        # OR-Tools Setup
        manager = pywrapcp.RoutingIndexManager(num_solver_locs, config.num_vehicles, 0)
        routing = pywrapcp.RoutingModel(manager)
        
        def time_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            # Service time: 1 min per stop (legacy behavior)
            service = 1 if from_node != 0 else 0
            return int(time_solver_matrix[from_node][to_node]) + service
            
        time_idx = routing.RegisterTransitCallback(time_callback)
        
        def distance_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return dist_solver_matrix[from_node][to_node]
            
        dist_idx = routing.RegisterTransitCallback(distance_callback)
        # Set primary objective cost to distance instead of time
        routing.SetArcCostEvaluatorOfAllVehicles(dist_idx)
        
        def demand_callback(from_index):
            return demands[manager.IndexToNode(from_index)]
        
        demand_idx = routing.RegisterUnaryTransitCallback(demand_callback)
        routing.AddDimensionWithVehicleCapacity(
            demand_idx, 0, [config.vehicle_capacity]*config.num_vehicles, True, 'Capacity'
        )
        
        routing.AddDimension(
            time_idx, 30, 999999, False, 'Time' # Large max duration for now
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
        search_params.time_limit.FromSeconds(30)
        
        solution = routing.SolveWithParameters(search_params)
        
        if not solution:
            print(f"[SOLVER] OR-Tools failed to find a solution. Status: {routing.status()}")
            # Inspect Matrix for issues
            max_time = max(max(row) for row in time_solver_matrix)
            print(f"[SOLVER] Max time in matrix: {max_time}")
            
        new_routes = {i: [] for i in range(config.num_vehicles)}
        unassigned = []
        
        if solution:
            print(f"[SOLVER] Solution Found by ORToolsSolver!")
            for v_id in range(config.num_vehicles):
                index = routing.Start(v_id)
                while not routing.IsEnd(index):
                    node = manager.IndexToNode(index)
                    if node != 0:
                        new_routes[v_id].append(map_solver_to_order[node])
                    index = solution.Value(routing.NextVar(index))
                    
            # Proper unassigned logic:
            flat_assigned = []
            for r in new_routes.values(): flat_assigned.extend(r)
            flat_assigned_ids = set(o['id'] for o in flat_assigned)
            
            for order in all_orders:
                if order['id'] not in flat_assigned_ids:
                    unassigned.append(order)
                    
        else:
            unassigned = all_orders
            
        return new_routes, unassigned
