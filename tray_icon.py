from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSignal, QObject
import logging

class TraySignals(QObject):
    toggle_status = pyqtSignal(bool)
    open_settings = pyqtSignal()
    exit_app = pyqtSignal()

class TrayIcon(QSystemTrayIcon):
    def __init__(self, app_icon, parent=None):
        super().__init__(app_icon, parent)
        self.signals = TraySignals()
        self.is_active = True
        
        self.menu = QMenu()
        
        self.toggle_action = QAction("Disable Lookup")
        self.toggle_action.triggered.connect(self._toggle_status)
        self.menu.addAction(self.toggle_action)
        
        # self.settings_action = QAction("Settings")
        # self.settings_action.triggered.connect(self.signals.open_settings.emit)
        # self.menu.addAction(self.settings_action)
        
        self.menu.addSeparator()
        
        self.exit_action = QAction("Exit")
        self.exit_action.triggered.connect(self.signals.exit_app.emit)
        self.menu.addAction(self.exit_action)
        
        self.setContextMenu(self.menu)
        self.setToolTip("WordLookup - Active")

    def _toggle_status(self):
        self.is_active = not self.is_active
        if self.is_active:
            self.toggle_action.setText("Disable Lookup")
            self.setToolTip("WordLookup - Active")
            logging.info("WordLookup enabled via tray.")
        else:
            self.toggle_action.setText("Enable Lookup")
            self.setToolTip("WordLookup - Disabled")
            logging.info("WordLookup disabled via tray.")
        self.signals.toggle_status.emit(self.is_active)
