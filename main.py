import sys
import os
import logging
from PyQt5.QtWidgets import QApplication, QStyle, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtCore import QObject, pyqtSignal, QThread

from utils import setup_logging
from settings import SettingsManager
from tts_engine import TTSEngine
from ocr_engine import OCREngine
from dictionary_api import fetch_definition
from popup_ui import PopupUI
from mouse_listener import MouseListener
from tray_icon import TrayIcon

class APIWorker(QThread):
    result_ready = pyqtSignal(dict, int, int)
    
    def __init__(self, word, x, y):
        super().__init__()
        self.word = word
        self.x = x
        self.y = y
        
    def run(self):
        logging.info(f"Fetching definition for: {self.word}")
        result = fetch_definition(self.word)
        self.result_ready.emit(result, self.x, self.y)

class MainController(QObject):
    show_popup_signal = pyqtSignal(dict, int, int)
    
    def __init__(self):
        super().__init__()
        setup_logging()
        logging.info("Starting WordLookup...")
        
        self.settings = SettingsManager()
        self.tts = TTSEngine()
        self.ocr = OCREngine(tesseract_path=self.settings.get("tesseract_path"))
        
        self.workers = []
        
        self.app = QApplication(sys.sys_argv)
        self.app.setQuitOnLastWindowClosed(False)
        
        self.popup = PopupUI(tts_callback=self.tts.speak)
        
        # System Tray Icon
        self.tray = QSystemTrayIcon()
        from PyQt5.QtGui import QIcon
        icon_path = os.path.join(sys._MEIPASS, 'icon.ico') if hasattr(sys, '_MEIPASS') else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icon.ico')
        if os.path.exists(icon_path):
            self.tray.setIcon(QIcon(icon_path))
            self.app.setWindowIcon(QIcon(icon_path))
        else:
            self.tray.setIcon(self.app.style().standardIcon(QStyle.SP_ComputerIcon))
        self.tray.setToolTip("WordLookup")
        
        self.tray_menu = QMenu()
        
        self.toggle_action = QAction("Disable Lookup", self.tray_menu)
        self.toggle_action.triggered.connect(self.toggle_listener)
        self.tray_menu.addAction(self.toggle_action)
        
        self.startup_action = QAction("Run on Startup", self.tray_menu)
        self.startup_action.setCheckable(True)
        self.startup_action.setChecked(self.check_run_on_startup())
        self.startup_action.triggered.connect(self.toggle_startup)
        self.tray_menu.addAction(self.startup_action)
        
        quit_action = QAction("Exit", self.tray_menu)
        quit_action.triggered.connect(self.quit_app)
        self.tray_menu.addAction(quit_action)
        
        self.tray.setContextMenu(self.tray_menu)
        self.tray.show()
        
        # Start Mouse Listener
        self.listener_active = True
        self.mouse_listener = MouseListener(callback=self.on_mouse_click)
        self.mouse_listener.start()
        
        self.show_popup_signal.connect(self._handle_show_popup)

    def check_run_on_startup(self):
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
            winreg.QueryValueEx(key, "WordLookup")
            winreg.CloseKey(key)
            return True
        except Exception:
            return False

    def toggle_startup(self, checked):
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_ALL_ACCESS)
            if checked:
                if getattr(sys, 'frozen', False):
                    exe_path = sys.executable
                else:
                    exe_path = os.path.abspath(sys.argv[0])
                winreg.SetValueEx(key, "WordLookup", 0, winreg.REG_SZ, f'"{exe_path}"')
                logging.info("Enabled run on startup.")
            else:
                try:
                    winreg.DeleteValue(key, "WordLookup")
                    logging.info("Disabled run on startup.")
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
        except Exception as e:
            logging.error(f"Failed to set startup registry key: {e}")
            self.startup_action.setChecked(not checked) # Revert UI if failed

    def toggle_listener(self):
        self.listener_active = not self.listener_active
        self.toggle_action.setText("Enable Lookup" if not self.listener_active else "Disable Lookup")
        
    def toggle_status(self, active):
        self.is_active = active
        
    def on_mouse_click(self, x, y):
        if not self.listener_active:
            return
            
        logging.info(f"Processing click at ({x}, {y})")
        
        # Run OCR in background or fast enough on main thread?
        # OCR might take ~100-300ms. Better not to block completely, but it's okay for now.
        word = self.ocr.extract_word_at(x, y)
        if not word:
            logging.info("No word detected by OCR.")
            return
            
        logging.info(f"OCR extracted word: {word}")
        
        # Hide previous popup
        self.popup.hide()
        
        # Fetch definition in background thread
        worker = APIWorker(word, x, y)
        self.workers.append(worker)
        worker.result_ready.connect(self._handle_show_popup)
        worker.finished.connect(lambda: self.workers.remove(worker) if worker in self.workers else None)
        worker.start()
        
    def _handle_show_popup(self, data, x, y):
        logging.info(f"Received API data, preparing to show popup for: {data.get('word', 'Unknown')}")
        if self.settings.get("auto_pronunciation") and "error" not in data:
            self.tts.speak(data.get("word", ""))
            
        duration = self.settings.get("popup_duration_sec")
        try:
            self.popup.show_data(data, x, y, duration)
        except Exception as e:
            logging.error(f"Error showing popup: {e}")
        
    def quit_app(self):
        logging.info("Exiting application.")
        self.mouse_listener.stop()
        self.tray.hide()
        self.app.quit()
        
    def run(self):
        sys.exit(self.app.exec_())

if __name__ == "__main__":
    import sys
    # Small patch to allow arguments to QApplication
    if not hasattr(sys, 'sys_argv'):
        sys.sys_argv = sys.argv
    controller = MainController()
    controller.run()
