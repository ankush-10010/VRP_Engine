from abc import ABC, abstractmethod
from typing import Dict, List, Tuple
from ...models.schemas import SimulationConfig

class BaseVRPSolver(ABC):
    @abstractmethod
    def solve(self, 
              current_routes: Dict[int, List[Dict]], 
              pending_orders: List[Dict],
              time_matrix: List[List[float]], 
              distance_matrix: List[List[float]],
              config: SimulationConfig) -> Tuple[Dict[int, List[Dict]], List[Dict]]:
        """
        Executes the optimization algorithm.
        
        Returns:
            Tuple containing:
            - A dictionary of optimized routes mapped by vehicle ID.
            - A list of unassigned orders.
        """
        pass
