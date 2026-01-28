"""
LP Solver - Aplikace pro řešení lineárního programování.

Tento balíček obsahuje kompletní řešení pro lineární programování s GUI.
"""

from models import Variable, Constraint, Objective, LPProblem, SolverResult
from solver_base import AbstractLPSolver
from solver_pulp import PuLPSolver
from solver_scipy import SciPySolver
from solver_ortools import ORToolsSolver
from solver_thread import SolverThread
from main_window import LPWindow

__all__ = [
    "Variable",
    "Constraint",
    "Objective",
    "LPProblem",
    "SolverResult",
    "AbstractLPSolver",
    "PuLPSolver",
    "SciPySolver",
    "ORToolsSolver",
    "SolverThread",
    "LPWindow",
]

__version__ = "1.0.0"
