import time
from solver_base import AbstractLPSolver
from models import LPProblem, SolverResult


class SciPySolver(AbstractLPSolver):
    """Implementace pomocí scipy.optimize.linprog"""

    def solve(self, problem: LPProblem) -> SolverResult:
        try:
            import numpy as np
            from scipy.optimize import linprog
        except ImportError:
            return SolverResult(
                status="Error",
                objective_value=None,
                variable_values={},
                error_message="SciPy není nainstalováno. Spusťte: pip install scipy",
            )

        start_time = time.time()

        try:
            c = np.array(problem.objective.coeffs)
            if problem.objective.sense == "Maximalizovat":
                c = -c

            A_ub = []
            b_ub = []
            A_eq = []
            b_eq = []

            for constraint in problem.constraints:
                if constraint.rel == "≤":
                    A_ub.append(constraint.coeffs)
                    b_ub.append(constraint.rhs)
                elif constraint.rel == "≥":
                    A_ub.append([-x for x in constraint.coeffs])
                    b_ub.append(-constraint.rhs)
                else:
                    A_eq.append(constraint.coeffs)
                    b_eq.append(constraint.rhs)

            bounds = [(v.low, v.up) for v in problem.variables]

            result = linprog(
                c=c,
                A_ub=A_ub if A_ub else None,
                b_ub=b_ub if b_ub else None,
                A_eq=A_eq if A_eq else None,
                b_eq=b_eq if b_eq else None,
                bounds=bounds,
                method="highs",
            )

            solve_time = time.time() - start_time

            obj_value = result.fun
            if problem.objective.sense == "Maximalizovat":
                obj_value = -obj_value

            variable_values = {
                v.name: result.x[i] for i, v in enumerate(problem.variables)
            }

            return SolverResult(
                status="Optimal" if result.success else "Infeasible",
                objective_value=obj_value if result.success else None,
                variable_values=variable_values,
                solve_time=solve_time,
            )

        except Exception as e:
            return SolverResult(
                status="Error",
                objective_value=None,
                variable_values={},
                solve_time=time.time() - start_time,
                error_message=str(e),
            )
