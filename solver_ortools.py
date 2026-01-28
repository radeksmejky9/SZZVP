import time
from solver_base import AbstractLPSolver
from models import LPProblem, SolverResult


class ORToolsSolver(AbstractLPSolver):
    """Implementace pomocí Google OR-Tools"""

    def solve(self, problem: LPProblem) -> SolverResult:
        try:
            from ortools.linear_solver import pywraplp
        except ImportError:
            return SolverResult(
                status="Error",
                objective_value=None,
                variable_values={},
                error_message="OR-Tools není nainstalováno. Spusťte: pip install ortools",
            )

        start_time = time.time()

        try:
            # Vytvoření solveru
            # GLOP = LP solver, SCIP = MIP solver (podporuje celočíselné)
            has_integers = any(v.vtype == "Integer" for v in problem.variables)
            solver_type = "SCIP" if has_integers else "GLOP"

            solver = pywraplp.Solver.CreateSolver(solver_type)
            if not solver:
                raise Exception(f"Nepodařilo se vytvořit {solver_type} solver")

            # Vytvoření proměnných
            vars_dict = {}
            for v in problem.variables:
                lb = v.low if v.low is not None else -solver.infinity()
                ub = v.up if v.up is not None else solver.infinity()

                if v.vtype == "Integer":
                    vars_dict[v.name] = solver.IntVar(lb, ub, v.name)
                else:
                    vars_dict[v.name] = solver.NumVar(lb, ub, v.name)

            # Účelová funkce
            objective = solver.Objective()
            for i, var in enumerate(problem.variables):
                objective.SetCoefficient(
                    vars_dict[var.name], problem.objective.coeffs[i]
                )

            if problem.objective.sense == "Minimalizovat":
                objective.SetMinimization()
            else:
                objective.SetMaximization()

            # Omezení
            for constraint in problem.constraints:
                if constraint.rel == "≤":
                    ct = solver.Constraint(-solver.infinity(), constraint.rhs)
                elif constraint.rel == "≥":
                    ct = solver.Constraint(constraint.rhs, solver.infinity())
                else:  # =
                    ct = solver.Constraint(constraint.rhs, constraint.rhs)

                for i, var in enumerate(problem.variables):
                    ct.SetCoefficient(vars_dict[var.name], constraint.coeffs[i])

            # Řešení
            status = solver.Solve()
            solve_time = time.time() - start_time

            # Mapování statusů
            status_map = {
                pywraplp.Solver.OPTIMAL: "Optimal",
                pywraplp.Solver.FEASIBLE: "Feasible",
                pywraplp.Solver.INFEASIBLE: "Infeasible",
                pywraplp.Solver.UNBOUNDED: "Unbounded",
                pywraplp.Solver.ABNORMAL: "Abnormal",
                pywraplp.Solver.NOT_SOLVED: "Not Solved",
            }

            variable_values = {
                name: var.solution_value() for name, var in vars_dict.items()
            }

            return SolverResult(
                status=status_map.get(status, "Unknown"),
                objective_value=(
                    objective.Value()
                    if status in [pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE]
                    else None
                ),
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
