"""
Datové třídy pro reprezentaci LP problému a výsledků.
"""
from dataclasses import dataclass
from typing import List, Optional, Dict


@dataclass
class Variable:
    """Reprezentace proměnné v LP problému"""
    name: str
    low: Optional[float] = 0
    up: Optional[float] = None
    vtype: str = "Continuous"  # Continuous / Integer


@dataclass
class Constraint:
    """Reprezentace omezení v LP problému"""
    coeffs: List[float]
    rel: str
    rhs: float


@dataclass
class Objective:
    """Reprezentace účelové funkce"""
    sense: str
    coeffs: List[float]


@dataclass
class LPProblem:
    """Kontejner pro kompletní LP problém"""
    variables: List[Variable]
    objective: Objective
    constraints: List[Constraint]


@dataclass
class SolverResult:
    """Výsledek řešení LP problému"""
    status: str
    objective_value: Optional[float]
    variable_values: Dict[str, float]
    solve_time: float = 0.0
    error_message: Optional[str] = None
