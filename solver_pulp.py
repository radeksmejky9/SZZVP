"""
Implementace řešiče pomocí PuLP knihovny.
"""

import time
from solver_base import AbstractLPSolver
from models import LPProblem, SolverResult


class PuLPSolver(AbstractLPSolver):
    """Implementace řešiče pomocí PuLP knihovny"""

    def solve(self, problem: LPProblem) -> SolverResult:
        try:
            import pulp
        except ImportError:
            return SolverResult(
                status="Error",
                objective_value=None,
                variable_values={},
                error_message="PuLP není nainstalováno. Spusťte: pip install pulp",
            )

        start_time = time.time()

        try:
            sense = (
                pulp.LpMinimize
                if problem.objective.sense == "Minimalizovat"
                else pulp.LpMaximize
            )

            model = pulp.LpProblem("GUI_LP_Model", sense)

            var_dict = {}
            for v in problem.variables:
                var_dict[v.name] = pulp.LpVariable(
                    v.name, lowBound=v.low, upBound=v.up, cat=v.vtype
                )

            model += pulp.lpSum(
                problem.objective.coeffs[i] * var_dict[problem.variables[i].name]
                for i in range(len(problem.variables))
            )

            for c in problem.constraints:
                lhs = pulp.lpSum(
                    c.coeffs[i] * var_dict[problem.variables[i].name]
                    for i in range(len(problem.variables))
                )
                if c.rel == "≤":
                    model += lhs <= c.rhs
                elif c.rel == "≥":
                    model += lhs >= c.rhs
                else:
                    model += lhs == c.rhs

            status = model.solve()
            solve_time = time.time() - start_time

            variable_values = {name: var.value() for name, var in var_dict.items()}

            return SolverResult(
                status=pulp.LpStatus[status],
                objective_value=pulp.value(model.objective),
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
