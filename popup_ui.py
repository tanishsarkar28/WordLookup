from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QApplication
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QRect
from PyQt5.QtGui import QFont, QColor, QPalette

class PopupUI(QWidget):
    def __init__(self, tts_callback=None):
        super().__init__()
        self.tts_callback = tts_callback
        self.current_word = ""
        self.init_ui()
        
        # Timer for auto-dismiss
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.hide_popup)
        self.duration = 4000

    def init_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Main layout
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.layout.setSpacing(8)
        
        # Container for styling
        self.container = QWidget(self)
        self.container.setObjectName("Container")
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(15, 15, 15, 15)
        self.container_layout.setSpacing(8)
        self.layout.addWidget(self.container)
        self.setLayout(self.layout)
        
        # Header (Word + TTS Button)
        header_layout = QHBoxLayout()
        self.word_label = QLabel("Word")
        self.word_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.word_label.setStyleSheet("color: #FFFFFF;")
        header_layout.addWidget(self.word_label)
        
        self.tts_button = QPushButton("🔊")
        self.tts_button.setFixedSize(30, 30)
        self.tts_button.setCursor(Qt.PointingHandCursor)
        self.tts_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #4FC3F7;
                font-size: 16px;
            }
            QPushButton:hover {
                color: #81D4FA;
            }
        """)
        self.tts_button.clicked.connect(self.play_tts)
        header_layout.addWidget(self.tts_button)
        header_layout.addStretch()
        
        self.container_layout.addLayout(header_layout)
        
        # Phonetic
        self.phonetic_label = QLabel("/phonetic/")
        self.phonetic_label.setFont(QFont("Segoe UI", 10, QFont.StyleItalic))
        self.phonetic_label.setStyleSheet("color: #B0BEC5;")
        self.container_layout.addWidget(self.phonetic_label)
        
        # Meaning
        self.meaning_label = QLabel("Meaning text here")
        self.meaning_label.setFont(QFont("Segoe UI", 11))
        self.meaning_label.setStyleSheet("color: #E0E0E0;")
        self.meaning_label.setWordWrap(True)
        self.container_layout.addWidget(self.meaning_label)
        
        # Synonyms
        self.synonyms_label = QLabel("Synonyms: word1, word2")
        self.synonyms_label.setFont(QFont("Segoe UI", 10))
        self.synonyms_label.setStyleSheet("color: #4FC3F7;")
        self.synonyms_label.setWordWrap(True)
        self.container_layout.addWidget(self.synonyms_label)
        
        # Example
        self.example_label = QLabel("Example: example sentence")
        self.example_label.setFont(QFont("Segoe UI", 10, QFont.StyleItalic))
        self.example_label.setStyleSheet("color: #9E9E9E;")
        self.example_label.setWordWrap(True)
        self.container_layout.addWidget(self.example_label)
        
        # Styling
        self.setStyleSheet("""
            #Container {
                background-color: #1E1E1E;
                border-radius: 12px;
                border: 1px solid #333333;
            }
        """)
        
        self.setFixedWidth(320)
        
        # Animation
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(200)

    def play_tts(self):
        if self.tts_callback and self.current_word:
            self.tts_callback(self.current_word)

    def show_data(self, data, x, y, duration_sec):
        self.duration = int(duration_sec * 1000)
        
        if "error" in data:
            self.current_word = ""
            self.word_label.setText(data.get("word", "Unknown"))
            self.phonetic_label.setText("")
            self.meaning_label.setText(data["error"])
            self.synonyms_label.hide()
            self.example_label.hide()
            self.tts_button.hide()
        else:
            self.current_word = data.get("word", "")
            self.word_label.setText(self.current_word)
            self.phonetic_label.setText(data.get("phonetic", ""))
            self.meaning_label.setText(data.get("meaning", "No definition found."))
            
            synonyms = data.get("synonyms", [])
            if synonyms:
                self.synonyms_label.setText(f"Synonyms: {', '.join(synonyms)}")
                self.synonyms_label.show()
            else:
                self.synonyms_label.hide()
                
            example = data.get("example", "")
            if example:
                self.example_label.setText(f'"{example}"')
                self.example_label.show()
            else:
                self.example_label.hide()
                
            self.tts_button.show()
            
        self.adjustSize()
        
        # Positioning logic to prevent going off-screen
        screen = QApplication.primaryScreen().geometry()
        popup_width = self.width()
        popup_height = self.height()
        
        pos_x = x + 15
        pos_y = y + 15
        
        if pos_x + popup_width > screen.width():
            pos_x = x - popup_width - 15
        if pos_y + popup_height > screen.height():
            pos_y = y - popup_height - 15
            
        self.move(pos_x, pos_y)
        
        import logging
        logging.info(f"Displaying popup at ({pos_x}, {pos_y}) with word: {self.current_word}")
        
        # Fade in
        self.setWindowOpacity(0.0)
        self.show()
        self.raise_()
        self.activateWindow()
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.start()
        
        self.timer.start(self.duration)
        logging.info("Popup shown and animation started.")

    def hide_popup(self):
        self.animation.setStartValue(1.0)
        self.animation.setEndValue(0.0)
        self.animation.finished.connect(self._on_hide_finished)
        self.animation.start()
        
    def _on_hide_finished(self):
        self.animation.finished.disconnect(self._on_hide_finished)
        self.hide()
        self.timer.stop()

    def enterEvent(self, event):
        """Called when the mouse enters the popup window."""
        self.timer.stop()  # Stop the auto-dismiss timer so it stays open
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Called when the mouse leaves the popup window."""
        # When mouse leaves, hide it fairly quickly (500ms)
        self.timer.start(500)
        super().leaveEvent(event)
