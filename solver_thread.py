from PySide6.QtCore import QThread, Signal
from models import LPProblem, SolverResult
from solver_base import AbstractLPSolver
from solver_pulp import PuLPSolver


class SolverThread(QThread):
    """Thread pro asynchronní řešení LP problému"""

    finished = Signal(SolverResult)
    error = Signal(str)
    progress = Signal(str)

    def __init__(self, problem: LPProblem, solver: AbstractLPSolver = None):
        super().__init__()
        self.problem = problem
        self.solver = solver if solver is not None else PuLPSolver()

    def run(self):
        try:
            self.progress.emit("Řešení probíhá...")
            result = self.solver.solve(self.problem)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))
