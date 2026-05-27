from .base import BaseVRPSolver
from .alns_solver import ALNSSolver
from .ortools_solver import ORToolsSolver

class SolverFactory:
    @staticmethod
    def create_solver(strategy_name: str) -> BaseVRPSolver:
        solvers = {
            "alns": ALNSSolver(),
            "ortools": ORToolsSolver(),
            # "tabu": TabuSearchSolver(), # To be implemented
        }
        solver = solvers.get(strategy_name.lower())
        if not solver:
            raise ValueError(f"Algorithm {strategy_name} is not supported.")
        return solver
