import math
import random
import copy
from typing import Dict, List, Tuple

from .base import BaseVRPSolver
from ...models.schemas import SimulationConfig
from ...services.solver import calculate_raw_route_time, calculate_total_fleet_cost, calculate_raw_route_distance

class ALNSSolver(BaseVRPSolver):
    def _repair_greedy(self, partial_routes: Dict[int, List[Dict]], request_bank: List[Dict], time_matrix: List[List[float]], distance_matrix: List[List[float]], config: SimulationConfig) -> Tuple[Dict[int, List[Dict]], List[Dict]]:
        """ALNS Repair: Insert orders greedily based on distance cost, constrained by time."""
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
                orig_cost = calculate_raw_route_distance(indices, distance_matrix)
                
                for i in range(len(route)+1):
                    temp = route[:i] + [order] + route[i:]
                    new_inds = list(dict.fromkeys([o['index'] for o in temp]))
                    new_time = calculate_raw_route_time(new_inds, time_matrix)
                    
                    if (new_time/60.0) <= 200:
                        new_cost = calculate_raw_route_distance(new_inds, distance_matrix)
                        diff = new_cost - orig_cost
                        if diff < best_increase:
                            best_increase = diff
                            best_v, best_i = v_id, i
                            
            if best_v != -1:
                repaired[best_v].insert(best_i, order)
            else:
                # Try new route
                new_time = calculate_raw_route_time([order['index']], time_matrix)
                if (order['demand'] <= config.vehicle_capacity) and ((new_time/60.0) <= 200):
                     for v in range(config.num_vehicles):
                         if not repaired[v]:
                             repaired[v].append(order)
                             break
                     else:
                         uninserted.append(order)
                else:
                    uninserted.append(order)
                    
        return repaired, uninserted
        
    def _destroy_random(self, routes: Dict[int, List[Dict]], num_remove: int) -> Tuple[Dict[int, List[Dict]], List[Dict]]:
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

    def solve(self, 
              current_routes: Dict[int, List[Dict]], 
              pending_orders: List[Dict],
              time_matrix: List[List[float]], 
              distance_matrix: List[List[float]],
              config: SimulationConfig) -> Tuple[Dict[int, List[Dict]], List[Dict]]:
        
        # Initial Solution: Greedy repair of everything
        initial_full_pending = pending_orders[:]
        for r in current_routes.values(): initial_full_pending.extend(r)
        
        start_routes = {i: [] for i in range(config.num_vehicles)}
        curr_sol, curr_unassigned = self._repair_greedy(start_routes, initial_full_pending, time_matrix, distance_matrix, config)
        
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
            partial, bank = self._destroy_random(curr_sol, num_rem)
            bank.extend(curr_unassigned)
            
            # Repair
            new_sol, new_un = self._repair_greedy(partial, bank, time_matrix, distance_matrix, config)
            
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
