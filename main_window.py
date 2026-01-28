import json
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QSpinBox,
    QLabel,
    QComboBox,
    QHeaderView,
    QMessageBox,
    QFileDialog,
)
from PySide6.QtCore import Qt
from typing import List
from models import Variable, Constraint, Objective, LPProblem, SolverResult
from solver_pulp import PuLPSolver
from solver_scipy import SciPySolver
from solver_ortools import ORToolsSolver
from solver_thread import SolverThread


class LPWindow(QMainWindow):
    """Hlavní okno aplikace"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Řešič lineárního programování")
        self.resize(1100, 700)

        self.solver_thread = None

        main = QWidget()
        main_layout = QVBoxLayout(main)
        self.setCentralWidget(main)

        # ========== TOP PANEL ==========
        top_panel = QHBoxLayout()

        self.new_btn = QPushButton("📁 Nový")
        self.load_btn = QPushButton("📂 Načíst")
        self.save_btn = QPushButton("💾 Uložit")
        self.solve_btn = QPushButton("Řešit")

        self.new_btn.clicked.connect(self.new_problem)
        self.load_btn.clicked.connect(self.load_problem)
        self.save_btn.clicked.connect(self.save_problem)
        self.solve_btn.clicked.connect(self.solve_problem)

        top_panel.addWidget(self.new_btn)
        top_panel.addWidget(self.load_btn)
        top_panel.addWidget(self.save_btn)
        top_panel.addWidget(self.solve_btn)
        top_panel.addStretch()

        # Výběr řešiče
        top_panel.addWidget(QLabel("Řešič:"))
        self.solver_combo = QComboBox()
        self.solver_combo.addItems(["PuLP (CBC)", "SciPy (HiGHS)", "OR-Tools (Google)"])
        self.solver_combo.setCurrentIndex(0)
        top_panel.addWidget(self.solver_combo)

        # Cílová funkce
        top_panel.addWidget(QLabel("Cíl:"))
        self.obj_sense = QComboBox()
        self.obj_sense.addItems(["Minimalizovat", "Maximalizovat"])
        top_panel.addWidget(self.obj_sense)

        # Počet proměnných
        top_panel.addWidget(QLabel("Proměnné:"))
        self.var_spin = QSpinBox()
        self.var_spin.setRange(1, 100)
        self.var_spin.setValue(3)
        self.var_spin.valueChanged.connect(self.rebuild_tables)
        top_panel.addWidget(self.var_spin)

        # Počet omezení
        top_panel.addWidget(QLabel("Omezení:"))
        self.con_spin = QSpinBox()
        self.con_spin.setRange(1, 100)
        self.con_spin.setValue(3)
        self.con_spin.valueChanged.connect(self.rebuild_tables)
        top_panel.addWidget(self.con_spin)

        main_layout.addLayout(top_panel)

        # ========== TABY ==========
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        self.tab_vars = QTableWidget()
        self.tabs.addTab(self.tab_vars, "Proměnné")

        self.tab_obj = QTableWidget()
        self.tabs.addTab(self.tab_obj, "Účelová funkce")

        self.tab_cons = QTableWidget()
        self.tabs.addTab(self.tab_cons, "Omezení")

        # Tab nápověda
        self.tab_help = QWidget()
        help_layout = QVBoxLayout(self.tab_help)
        help_label = QLabel(
            "NÁVOD K POUŽITÍ:\n\n"
            "Nastavte počet proměnných a omezení\n"
            "Vyberte řešič\n"
            "Vyplňte tabulky:\n"
            " • Proměnné: název, meze, typ (Reálné/Celočíselné)\n"
            " • Účelová funkce: koeficienty pro min/max\n"
            " • Omezení: koeficienty, relace (≤/≥/=), pravá strana\n"
            "Klikněte 'Řešit'\n"
        )
        help_label.setWordWrap(True)
        help_layout.addWidget(help_label)
        help_layout.addStretch()
        self.tabs.addTab(self.tab_help, "Nápověda")

        # Interpretace
        self.interpret_label = QLabel("")
        self.interpret_label.setStyleSheet("background-color:#f4f4f4; padding:5px;")
        self.interpret_label.setWordWrap(True)
        main_layout.addWidget(self.interpret_label)

        # Status
        self.status_label = QLabel("Status: Připraveno")
        self.status_label.setStyleSheet("color: #666; padding: 5px;")
        main_layout.addWidget(self.status_label)

        self.rebuild_tables()

    def rebuild_tables(self):
        """Přestavení tabulek podle počtu proměnných a omezení"""
        n_vars = self.var_spin.value()
        n_cons = self.con_spin.value()

        # ========== VARS ==========
        self.tab_vars.setColumnCount(4)
        self.tab_vars.setHorizontalHeaderLabels(
            ["Název", "Dolní mez", "Horní mez", "Typ"]
        )
        self.tab_vars.setRowCount(n_vars)

        for i in range(n_vars):
            if self.tab_vars.item(i, 0) is None:
                self.tab_vars.setItem(i, 0, QTableWidgetItem(f"x{i+1}"))
            if self.tab_vars.item(i, 1) is None:
                self.tab_vars.setItem(i, 1, QTableWidgetItem("0"))
            if self.tab_vars.item(i, 2) is None:
                self.tab_vars.setItem(i, 2, QTableWidgetItem(""))
            if self.tab_vars.cellWidget(i, 3) is None:
                combo = QComboBox()
                combo.addItems(["Reálné", "Celočíselné"])
                self.tab_vars.setCellWidget(i, 3, combo)

        self.tab_vars.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # ========== OBJECTIVE ==========
        self.tab_obj.setRowCount(1)
        self.tab_obj.setColumnCount(n_vars)
        self.tab_obj.setHorizontalHeaderLabels([f"x{i+1}" for i in range(n_vars)])
        for j in range(n_vars):
            if self.tab_obj.item(0, j) is None:
                self.tab_obj.setItem(0, j, QTableWidgetItem("0"))
        self.tab_obj.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # ========== CONSTRAINTS ==========
        for r in range(self.tab_cons.rowCount()):
            for c in range(self.tab_cons.columnCount()):
                widget = self.tab_cons.cellWidget(r, c)
                if widget is not None:
                    self.tab_cons.removeCellWidget(r, c)

        self.tab_cons.setRowCount(n_cons)
        self.tab_cons.setColumnCount(n_vars + 2)
        self.tab_cons.setHorizontalHeaderLabels(
            [f"x{i+1}" for i in range(n_vars)] + ["Relace", "Pravá strana"]
        )

        for r in range(n_cons):
            # Koeficienty proměnných
            for c in range(n_vars):
                self.tab_cons.setItem(r, c, QTableWidgetItem("0"))

            # Předposlední sloupec = combobox pro relaci
            combo_rel = QComboBox()
            combo_rel.addItems(["≤", "≥", "="])
            self.tab_cons.setCellWidget(r, n_vars, combo_rel)

            # Poslední sloupec = pravá strana
            self.tab_cons.setItem(r, n_vars + 1, QTableWidgetItem("0"))

        self.tab_cons.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.status_label.setText("Status: Tabulky aktualizovány")

    def validate_tables(self):
        """Validace vstupních dat v tabulkách"""
        errors = []

        def reset_bg(table):
            for r in range(table.rowCount()):
                for c in range(table.columnCount()):
                    item = table.item(r, c)
                    if item:
                        item.setBackground(Qt.white)

        reset_bg(self.tab_vars)
        reset_bg(self.tab_obj)
        reset_bg(self.tab_cons)

        # ========== VARS ==========
        for r in range(self.tab_vars.rowCount()):
            name = self.tab_vars.item(r, 0).text().strip()
            if not name:
                self.tab_vars.item(r, 0).setBackground(Qt.red)
                errors.append(f"Proměnná {r+1}: prázdné jméno")

            low_txt = self.tab_vars.item(r, 1).text().strip()
            up_txt = self.tab_vars.item(r, 2).text().strip()

            if low_txt:
                try:
                    float(low_txt)
                except:
                    self.tab_vars.item(r, 1).setBackground(Qt.red)
                    errors.append(f"Proměnná {name}: chybná dolní mez")
            if up_txt:
                try:
                    float(up_txt)
                except:
                    self.tab_vars.item(r, 2).setBackground(Qt.red)
                    errors.append(f"Proměnná {name}: chybná horní mez")

        # ========== OBJECTIVE ==========
        for c in range(self.tab_obj.columnCount()):
            txt = self.tab_obj.item(0, c).text().strip()
            if txt:
                try:
                    float(txt)
                except:
                    self.tab_obj.item(0, c).setBackground(Qt.red)
                    errors.append(f"Účelová funkce: neplatný koef. u x{c+1}")

        # ========== CONSTRAINTS ==========
        n_vars = self.var_spin.value()
        for r in range(self.tab_cons.rowCount()):
            for c in range(n_vars):
                txt = self.tab_cons.item(r, c).text().strip()
                if txt:
                    try:
                        float(txt)
                    except:
                        self.tab_cons.item(r, c).setBackground(Qt.red)
                        errors.append(f"Omezení {r+1}: neplatný koef. u x{c+1}")

            rhs_txt = self.tab_cons.item(r, n_vars + 1).text().strip()
            if rhs_txt:
                try:
                    float(rhs_txt)
                except:
                    self.tab_cons.item(r, n_vars + 1).setBackground(Qt.red)
                    errors.append(f"Omezení {r+1}: neplatná pravá strana")

        return errors

    def get_variables(self) -> List[Variable]:
        """Získání proměnných z tabulky"""
        data = []
        for r in range(self.tab_vars.rowCount()):
            name = self.tab_vars.item(r, 0).text()
            low_txt = self.tab_vars.item(r, 1).text().strip()
            up_txt = self.tab_vars.item(r, 2).text().strip()

            low = float(low_txt) if low_txt != "" else None
            up = float(up_txt) if up_txt != "" else None

            combo = self.tab_vars.cellWidget(r, 3)
            gui_type = combo.currentText()
            vtype = "Continuous" if gui_type == "Reálné" else "Integer"

            data.append(Variable(name, low, up, vtype))
        return data

    def get_objective(self) -> Objective:
        """Získání účelové funkce z tabulky"""
        coeffs = []
        for c in range(self.tab_obj.columnCount()):
            try:
                coeffs.append(float(self.tab_obj.item(0, c).text()))
            except:
                coeffs.append(0.0)
        return Objective(self.obj_sense.currentText(), coeffs)

    def get_constraints(self) -> List[Constraint]:
        """Získání omezení z tabulky"""
        cons = []
        n_vars = self.var_spin.value()
        for r in range(self.tab_cons.rowCount()):
            coeffs = [
                float(self.tab_cons.item(r, c).text() or "0") for c in range(n_vars)
            ]
            rel = self.tab_cons.cellWidget(r, n_vars).currentText()
            rhs = float(self.tab_cons.item(r, n_vars + 1).text() or "0")
            cons.append(Constraint(coeffs, rel, rhs))
        return cons

    def solve_problem(self):
        """Řešení LP problému"""
        errors = self.validate_tables()
        if errors:
            QMessageBox.critical(self, "Chyba vstupu", "\n".join(errors))
            return

        try:
            variables = self.get_variables()
            objective = self.get_objective()
            constraints = self.get_constraints()

            problem = LPProblem(
                variables=variables, objective=objective, constraints=constraints
            )

            # Výběr řešiče
            solver_name = self.solver_combo.currentText()
            if "SciPy" in solver_name:
                solver = SciPySolver()
                has_integer = any(v.vtype == "Integer" for v in variables)
                if has_integer:
                    QMessageBox.warning(
                        self, "Upozornění", "SciPy nepodporuje celočíselné proměnné.\n"
                    )
            elif "OR-Tools" in solver_name:
                solver = ORToolsSolver()
            else:
                solver = PuLPSolver()

            self.solve_btn.setEnabled(False)
            self.status_label.setText("Status: Řešení probíhá...")

            self.solver_thread = SolverThread(problem, solver)
            self.solver_thread.finished.connect(self.on_solve_finished)
            self.solver_thread.error.connect(self.on_solve_error)
            self.solver_thread.progress.connect(self.on_solve_progress)
            self.solver_thread.start()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", str(e))
            self.solve_btn.setEnabled(True)
            self.status_label.setText("Status: Chyba")

    def on_solve_progress(self, message: str):
        """Handler pro aktualizaci průběhu řešení"""
        self.status_label.setText(f"Status: {message}")

    def on_solve_error(self, error_message: str):
        """Handler pro chyby při řešení"""
        QMessageBox.critical(self, "Chyba při řešení", error_message)
        self.solve_btn.setEnabled(True)
        self.status_label.setText("Status: Chyba")

    def on_solve_finished(self, result: SolverResult):
        """Handler pro dokončení řešení"""
        self.solve_btn.setEnabled(True)

        if result.error_message:
            QMessageBox.critical(self, "Chyba", result.error_message)
            self.status_label.setText("Status: Chyba při řešení")
            return

        self.display_results(result)
        self.status_label.setText(
            f"Status: Hotovo ({result.solve_time:.3f}s) - {result.status}"
        )

    def display_results(self, result: SolverResult):
        """Zobrazení výsledků řešení"""
        if not hasattr(self, "tab_result"):
            self.tab_result = QTableWidget()
            self.tabs.insertTab(3, self.tab_result, "Výsledky")

        self.tabs.setCurrentWidget(self.tab_result)
        self.tab_result.clear()
        self.tab_result.setRowCount(len(result.variable_values) + 2)
        self.tab_result.setColumnCount(2)
        self.tab_result.setHorizontalHeaderLabels(["Název", "Hodnota"])

        row = 0
        self.tab_result.setItem(row, 0, QTableWidgetItem("Status"))
        self.tab_result.setItem(row, 1, QTableWidgetItem(result.status))
        row += 1

        for name, value in result.variable_values.items():
            self.tab_result.setItem(row, 0, QTableWidgetItem(name))
            value_str = f"{value:.6f}" if value is not None else "N/A"
            self.tab_result.setItem(row, 1, QTableWidgetItem(value_str))
            row += 1

        self.tab_result.setItem(row, 0, QTableWidgetItem("Z"))
        obj_str = (
            f"{result.objective_value:.6f}"
            if result.objective_value is not None
            else "N/A"
        )
        self.tab_result.setItem(row, 1, QTableWidgetItem(obj_str))

        self.tab_result.resizeColumnsToContents()

        # Interpretace
        interpretace = "Interpretace řešení:\n"
        if result.status == "Optimal":
            interpretace += "Nalezeno optimální řešení\n"
            interpretace += f"Čas řešení: {result.solve_time:.3f} sekund\n"
            interpretace += f" Hodnota účelové funkce: {result.objective_value:.6f}\n"
        elif result.status == "Infeasible":
            interpretace += "Problém nemá přípustné řešení\n"
            interpretace += "Zkontrolujte, zda nejsou omezení v rozporu\n"
        elif result.status == "Unbounded":
            interpretace += "Problém je neomezený\n"
            interpretace += "Přidejte další omezení pro ohraničení řešení\n"
        else:
            interpretace += f"Status: {result.status}\n"

        self.interpret_label.setText(interpretace)

    def save_problem(self):
        """Uložení problému do JSON souboru"""
        fname, _ = QFileDialog.getSaveFileName(self, "Uložit", "", "JSON (*.json)")
        if not fname:
            return
        try:
            data = {
                "n_vars": self.var_spin.value(),
                "n_cons": self.con_spin.value(),
                "obj_sense": self.obj_sense.currentText(),
                "solver": self.solver_combo.currentText(),
                "variables": [v.__dict__ for v in self.get_variables()],
                "objective": self.get_objective().__dict__,
                "constraints": [c.__dict__ for c in self.get_constraints()],
            }
            with open(fname, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            QMessageBox.information(self, "Hotovo", "Úloha uložena.")
        except Exception as e:
            QMessageBox.critical(self, "Chyba", str(e))

    def load_problem(self):
        """Načtení problému z JSON souboru"""
        fname, _ = QFileDialog.getOpenFileName(self, "Načíst", "", "JSON (*.json)")
        if not fname:
            return
        try:
            with open(fname, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.var_spin.setValue(data["n_vars"])
            self.con_spin.setValue(data["n_cons"])
            self.obj_sense.setCurrentText(data["obj_sense"])

            if "solver" in data:
                self.solver_combo.setCurrentText(data["solver"])

            self.rebuild_tables()

            for i, v in enumerate(data["variables"]):
                self.tab_vars.item(i, 0).setText(v["name"])
                self.tab_vars.item(i, 1).setText(
                    "" if v["low"] is None else str(v["low"])
                )
                self.tab_vars.item(i, 2).setText(
                    "" if v["up"] is None else str(v["up"])
                )
                combo = self.tab_vars.cellWidget(i, 3)
                combo.setCurrentText(
                    "Reálné" if v["vtype"] == "Continuous" else "Celočíselné"
                )

            for i, coef in enumerate(data["objective"]["coeffs"]):
                self.tab_obj.item(0, i).setText(str(coef))

            for r, c in enumerate(data["constraints"]):
                for j, coef in enumerate(c["coeffs"]):
                    self.tab_cons.item(r, j).setText(str(coef))
                rel_combo = self.tab_cons.cellWidget(r, len(c["coeffs"]))
                rel_combo.setCurrentText(c["rel"])
                self.tab_cons.item(r, len(c["coeffs"]) + 1).setText(str(c["rhs"]))

            QMessageBox.information(self, "Hotovo", "Úloha načtena.")

        except Exception as e:
            QMessageBox.critical(self, "Chyba", str(e))

    def new_problem(self):
        """Vytvoření nového prázdného problému"""
        if (
            QMessageBox.question(
                self,
                "Nová úloha",
                "Vytvořit novou úlohu?",
                QMessageBox.Yes | QMessageBox.No,
            )
            == QMessageBox.Yes
        ):
            self.var_spin.setValue(3)
            self.con_spin.setValue(3)
            self.obj_sense.setCurrentIndex(0)
            self.rebuild_tables()
