import sys
from PySide6.QtWidgets import QApplication
from main_window import LPWindow


def main():
    """Hlavní funkce aplikace"""
    app = QApplication(sys.argv)
    win = LPWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
