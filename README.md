# LP Solver – GUI pro řešení lineárního programování

Moderní aplikace s grafickým rozhraním pro řešení problémů lineárního programování (LP) s podporou více řešičů.

## Funkce

- **Více řešičů**: PuLP (CBC), SciPy (HiGHS), OR-Tools (Google)  
- **Intuitivní GUI** s tabulkami pro snadné zadávání problému  
- **Asynchronní řešení** – GUI zůstává responzivní během výpočtu  
- **Ukládání a načítání** problémů do/z JSON souborů  
- **Interpretace výsledků** s detailním popisem řešení  
- **Rozšiřitelnost řešičů** – snadné přidání vlastního řešiče implementací abstraktní třídy  

---

## Instalace

### Základní závislosti
```bash
pip install requirements.txt
```

## Spuštění

```bash
python main.py
```

## Struktura projektu

```
__init__.py            # Inicializace balíčku
main_window.py         # Hlavní GUI okno
main.py                # Spouštěcí soubor
models.py              # Datové třídy (Variable, Constraint, LPProblem, atd.)
solver_base.py         # Abstraktní třída pro řešiče
solver_pulp.py         # Implementace pro PuLP
solver_scipy.py        # Implementace pro SciPy
solver_ortools.py      # Implementace pro OR-Tools
solver_thread.py       # Asynchronní řešení
requirements.txt       # Seznam Python závislostí
README.md              # Dokumentace
optimal.json           # Ukázkový problém LP
optimal2.json          # Náročnější ukázkový problém
infeasible.json        # Nesplinitelný problém
unbounded.json         # Neomezený problém
requirements.txt       # Základní závislosti
```

## Použití

1. **Nastavte počet proměnných a omezení v horním panelu, případně načtěte jeden z přiložených souborů pro rychlé odzkoušení funkcionality** (optimal.json, infeasible.json, unbounded.json, nebo optimal2.json)
2. **Vyberte řešič**
3. **Zvolte počet proměnných a omezení**
4. **Vyplňte tabulky**:
   - **Proměnné**: název, dolní/horní mez, typ
   - **Účelová funkce**: koeficienty
   - **Omezení**: koeficienty, relace (≤/≥/=), pravá strana
5. **Stav tabulek lze kdykoliv uložit.**
6. **Klikněte na Řešit**
7. **V případě, že by řešení trvalo příliš dlouho lze kliknout na tlačítko Nový pro kompletní restart, nebo libovolně upravit hodnoty a zahájit řešení znovu.**
8. **Zobrazí se výsledky v novém samostatném tabu**

## Přidání vlastního řešiče

Nový řešič lze snadno přidat implementací abstraktní třídy AbstractLPSolver. Tím se zachová jednotné rozhraní pro GUI a ostatní funkce programu:

```python
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
```

