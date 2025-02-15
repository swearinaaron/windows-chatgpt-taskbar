import sys
import json
from pathlib import Path
import requests
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QTextEdit, QLineEdit, QPushButton, QScrollArea, QGraphicsOpacityEffect)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QRect, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPalette, QColor, QFont, QShortcut, QKeySequence, QScreen
import keyboard  # For global hotkey

class OllamaThread(QThread):
    """Thread for handling Ollama API requests"""
    response_received = pyqtSignal(str)
    
    def __init__(self, prompt):
        super().__init__()
        self.prompt = prompt
        
    def run(self):
        try:
            response = requests.post(
                'http://localhost:11434/api/generate',
                json={
                    'model': 'deepseek-r1:14b',
                    'prompt': self.prompt,
                    'stream': True
                },
                stream=True
            )
            
            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    if 'response' in data:
                        self.response_received.emit(data['response'])
                        
        except Exception as e:
            self.response_received.emit(f"\nError: {str(e)}")

class ChatBubble(QWidget):
    """Custom widget for chat messages"""
    def __init__(self, text, is_user=False, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        
        # Message text with improved styling
        message = QTextEdit()
        message.setReadOnly(True)
        message.setPlainText(text)
        message.setFont(QFont("Segoe UI", 12))  # Larger, more readable font
        message.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        message.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Dynamic height based on content
        doc_height = message.document().size().height()
        message.setFixedHeight(min(doc_height + 20, 300))
        
        # Improved styling with animations
        if is_user:
            message.setStyleSheet("""
                QTextEdit {
                    background-color: #0078D4;
                    color: white;
                    border-radius: 15px;
                    padding: 12px 16px;
                    border: none;
                    selection-background-color: #005A9E;
                }
                QScrollBar:vertical {
                    border: none;
                    background: transparent;
                    width: 8px;
                }
                QScrollBar::handle:vertical {
                    background: rgba(255, 255, 255, 0.3);
                    border-radius: 4px;
                }
            """)
        else:
            message.setStyleSheet("""
                QTextEdit {
                    background-color: #2D2D2D;
                    color: white;
                    border-radius: 15px;
                    padding: 12px 16px;
                    border: none;
                    selection-background-color: #404040;
                }
                QScrollBar:vertical {
                    border: none;
                    background: transparent;
                    width: 8px;
                }
                QScrollBar::handle:vertical {
                    background: rgba(255, 255, 255, 0.1);
                    border-radius: 4px;
                }
            """)
        
        # Add margins to position bubbles
        layout.addWidget(message)
        if is_user:
            layout.setContentsMargins(100, 5, 20, 5)  # Right-aligned
        else:
            layout.setContentsMargins(20, 5, 100, 5)  # Left-aligned

class OverlayWidget(QWidget):
    """Semi-transparent overlay to dim background"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setStyleSheet("background-color: rgba(0, 0, 0, 0.5);")
        self.hide()

class ChatWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DeepSeek Chat")
        
        # Remove window frame but keep taskbar entry
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        
        # Create overlay for background dimming
        self.overlay = OverlayWidget()
        
        # Set up animations
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.opacity_anim.setDuration(200)
        self.opacity_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Set up the main widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        
        # Chat history area
        self.scroll_area = QScrollArea()
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_area.setWidgetResizable(True)
        
        # Input area with BRIGHT RED background
        self.input_field = QTextEdit()
        self.input_field.setPlaceholderText("Type your message... (YES, IT'S RED!)")
        self.input_field.setFixedHeight(100)
        self.input_field.setStyleSheet("""
            QTextEdit {
                background-color: #FF0000;  /* Bright red! */
                color: white;
                font-size: 16px;
                border: 3px solid #FF4444;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        
        # Test button
        self.test_button = QPushButton("Click to Test!")
        self.test_button.setStyleSheet("""
            QPushButton {
                background-color: #FF4444;
                color: white;
                padding: 10px;
                font-size: 14px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #FF6666;
            }
        """)
        self.test_button.clicked.connect(lambda: self.add_message("This is a test message!", True))
        
        # Style the window
        self.setup_styles()
        
        # Add widgets to layout
        self.layout.addWidget(self.scroll_area)
        self.layout.addWidget(self.input_field)
        self.layout.addWidget(self.test_button)
        
        # Setup shortcuts
        self.setup_shortcuts()
        
        # Initialize empty response for streaming
        self.current_response = ""
        self.current_response_bubble = None
        
    def setup_styles(self):
        # Set dark theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1A1A1A;
            }
            QScrollArea {
                border: none;
                background-color: #1A1A1A;
            }
            QWidget {
                background-color: #1A1A1A;
                color: white;
            }
            QTextEdit {
                background-color: #2D2D2D;
                border-radius: 5px;
                padding: 10px;
                color: white;
                font-family: 'Segoe UI';
                font-size: 11pt;
            }
        """)
        
        # Set window size to 90% of screen
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(QRect(
            screen.width() * 0.05,
            screen.height() * 0.05,
            screen.width() * 0.9,
            screen.height() * 0.9
        ))
        
    def setup_shortcuts(self):
        # Send message shortcut (Ctrl+Enter)
        self.send_shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        self.send_shortcut.activated.connect(self.send_message)
        
        # Close window shortcut (Escape)
        self.close_shortcut = QShortcut(QKeySequence("Escape"), self)
        self.close_shortcut.activated.connect(self.hide)
        
    def send_message(self):
        message = self.input_field.toPlainText().strip()
        if not message:
            return
            
        # Add user message
        self.add_message(message, is_user=True)
        
        # Clear input
        self.input_field.clear()
        
        # Start Ollama thread
        self.ollama_thread = OllamaThread(message)
        self.ollama_thread.response_received.connect(self.handle_response)
        self.ollama_thread.start()
        
    def add_message(self, text, is_user=False):
        bubble = ChatBubble(text, is_user)
        self.scroll_layout.addWidget(bubble)
        self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        )
        
    def handle_response(self, text):
        if self.current_response_bubble is None:
            self.current_response = text
            self.current_response_bubble = ChatBubble(text)
            self.scroll_layout.addWidget(self.current_response_bubble)
        else:
            self.current_response += text
            self.current_response_bubble.findChild(QTextEdit).setPlainText(
                self.current_response
            )
            
        # Scroll to bottom
        self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        )

    def show(self):
        # Show overlay first
        screen = QApplication.primaryScreen().geometry()
        self.overlay.setGeometry(screen)
        self.overlay.show()
        
        # Animate window appearance
        self.opacity_effect.setOpacity(0)
        super().show()
        self.opacity_anim.setStartValue(0)
        self.opacity_anim.setEndValue(1)
        self.opacity_anim.start()
        
        # Focus input
        self.input_field.setFocus()
        
    def hide(self):
        # Animate window disappearance
        self.opacity_anim.setStartValue(1)
        self.opacity_anim.setEndValue(0)
        self.opacity_anim.finished.connect(self._finish_hide)
        self.opacity_anim.start()
        
    def _finish_hide(self):
        super().hide()
        self.overlay.hide()
        self.opacity_anim.finished.disconnect(self._finish_hide)

def main():
    app = QApplication(sys.argv)
    window = ChatWindow()
    
    def toggle_window():
        if window.isVisible():
            window.hide()
        else:
            window.show()
    
    # Register global hotkey
    keyboard.add_hotkey('ctrl+space', toggle_window)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 