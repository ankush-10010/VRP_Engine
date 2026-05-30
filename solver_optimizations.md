# Solver Optimizations

This document explains the root causes of the optimization algorithms behaving like greedy heuristics, and the specific code changes implemented to solve them.

## The Problem
You reported that your Greedy algorithm was performing similarly or even outperforming OR-Tools and ALNS, making it hard to justify using the advanced algorithms on your resume (e.g. showing a cost reduction). 

Upon inspecting the codebase, two massive logic flaws were discovered:

1. **OR-Tools Time Constraint:** `ORToolsSolver` was limited to exactly 3 seconds (`search_params.time_limit.FromSeconds(3)`). OR-Tools first generates a greedy initial solution (using `PATH_CHEAPEST_ARC`), but because it only had 3 seconds, it immediately returned this initial greedy route without running any local search optimizations. Effectively, OR-Tools *was* a greedy algorithm.
2. **Objective Function Mismatch:** Your final simulation score evaluates `Cost = Distance + Fixed Truck Cost`. However, both OR-Tools and ALNS were evaluating route insertions strictly by `Time`. They were finding the *fastest* routes rather than the *shortest/cheapest* routes. 

## The Solutions Implemented

### 1. OR-Tools Enhancements (`app/core_engine/solvers/ortools_solver.py`)
- **Proper Optimization Metric:** Modified the codebase to build both a `time_solver_matrix` and a `dist_solver_matrix`.
- **Primary Objective Change:** Updated `SetArcCostEvaluatorOfAllVehicles` to optimize based on the scaled distance matrix (multiplying by 100 to maintain integer precision).
- **Time Constraint Dimension:** Changed the `Time` dimension to strictly use the `time_idx` callback, preserving the 200-minute constraint logic without polluting the objective.
- **Sufficient Processing Time:** Increased the time limit from 3 seconds to 30 seconds (`search_params.time_limit.FromSeconds(30)`), giving the Guided Local Search algorithm actual time to explore edge cases and find cost reductions.

### 2. ALNS Enhancements (`app/core_engine/solvers/alns_solver.py`)
- **Metric Import:** Imported `calculate_raw_route_distance` from `services.solver`.
- **Distance-Based Greedy Insertions:** Rewrote `_repair_greedy` so that it calculates the cost difference `diff = new_cost - orig_cost` using the `distance_matrix`. It now successfully searches for the best distance improvement instead of time improvement.
- **Time Constraints Preserved:** Kept the time evaluation strictly as a feasible constraint (`if (new_time/60.0) <= 200:`), ensuring we don't build mathematically impossible routes. 

With these changes in place, both OR-Tools and ALNS are equipped to actively search for distance reductions and minimize the fleet cost footprint!
