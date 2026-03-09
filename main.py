"""
16-bit RISC Processor Simulator - Main Entry Point
5-Stage Pipeline Architecture
Computer Architecture Course Project
"""

import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont
from processor_frontend import ProcessorSimulatorGUI

def main():
    # Suppress Qt warnings and debug messages
    import os
    os.environ["QT_LOGGING_RULES"] = "qt.qpa.fonts.warning=false;qt.style.warning=false;*.debug=false"
    
    app = QApplication(sys.argv)
    
    # Set application-wide font
    app.setFont(QFont("Segoe UI", 10))
    
    window = ProcessorSimulatorGUI()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
