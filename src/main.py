import os
import sys
import ctypes
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from src.gui.main_window import MainWindow

def main():
    # Set explicit AppUserModelID on Windows to ensure the custom taskbar icon is rendered correctly
    if sys.platform == "win32":
        try:
            myappid = "opensourcedev.ghostcutoffline.bgremover.v1"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception as e:
            print(f"Failed to set AppUserModelID: {e}")

    # Setup PyQt6 Application context
    app = QApplication(sys.argv)
    
    # Force modern Fusion style for consistent QSS theme representation
    app.setStyle("Fusion")
    
    # System identification details
    app.setApplicationName("GhostCut Offline")
    app.setOrganizationName("OpenSourceDev")

    # Load custom modern dark stylesheet if exists
    if hasattr(sys, '_MEIPASS'):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
    qss_path = os.path.join(base_dir, "src", "gui", "styles", "modern_dark.qss")
    if not os.path.exists(qss_path):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        qss_path = os.path.join(current_dir, "gui", "styles", "modern_dark.qss")

    if os.path.exists(qss_path):
        try:
            with open(qss_path, "r", encoding="utf-8") as f:
                app.setStyleSheet(f.read())
        except Exception as e:
            print(f"Failed loading stylesheet: {e}")
    else:
        print(f"Stylesheet not found at: {qss_path}")

    # Set application-wide window and taskbar icon
    icon_name = "app_icon.ico" if sys.platform == "win32" else "app_icon.png"
    icon_path = os.path.join(base_dir, "src", "gui", "assets", icon_name)
    if not os.path.exists(icon_path):
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gui", "assets", icon_name)
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # Bootstrap the primary shell UI
    main_win = MainWindow()
    main_win.show()
    
    # Start execution loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
