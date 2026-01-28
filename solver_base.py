from abc import ABC, abstractmethod
from models import LPProblem, SolverResult


class AbstractLPSolver(ABC):
    """
    Abstraktní třída pro LP řešiče.
    Pokud chcete použít jiný řešič, stačí implementovat tuto třídu.
    """

    @abstractmethod
    def solve(self, problem: LPProblem) -> SolverResult:
        """Řeší LP problém a vrací výsledek"""
        pass
