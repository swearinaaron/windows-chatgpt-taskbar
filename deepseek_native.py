import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import Qt, QUrl
import gradio as gr
import keyboard

class ChatWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DeepSeek Chat")
        
        # Set up window properties
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        
        # Create web view
        self.web = QWebEngineView()
        self.setCentralWidget(self.web)
        
        # Set up Gradio interface
        with gr.Blocks(theme=gr.themes.Soft(primary_hue="zinc", neutral_hue="zinc")) as demo:
            self.chatbot = gr.Chatbot(
                height=600,
                type='messages',
                show_label=False
            )
            self.msg = gr.Textbox(
                placeholder="Type your message...",
                show_label=False,
                container=False
            )
            
            def chat(message, history):
                history = history or []
                history.append({"role": "user", "content": message})
                
                # Start streaming response
                response = ""
                for chunk in self.stream_ollama(message):
                    response += chunk
                    history_copy = history.copy()
                    history_copy.append({"role": "assistant", "content": response})
                    yield history_copy
            
            self.msg.submit(
                chat,
                [self.msg, self.chatbot],
                [self.chatbot],
                api_name=None
            ).then(
                lambda: "",  # Clear input after sending
                None,
                [self.msg]
            )
        
        # Launch Gradio
        self.server = demo.queue().launch(
            server_port=7861,
            prevent_thread_lock=True,
            show_error=True
        )
        
        # Load the Gradio interface in our window
        self.web.setUrl(QUrl("http://localhost:7861"))
        
        # Set window size to 90% of screen
        screen = QApplication.primaryScreen().availableGeometry()
        width = int(screen.width() * 0.9)
        height = int(screen.height() * 0.9)
        x = int((screen.width() - width) / 2)
        y = int((screen.height() - height) / 2)
        self.setGeometry(x, y, width, height)

    def stream_ollama(self, prompt):
        import requests
        import json
        
        try:
            response = requests.post(
                'http://localhost:11434/api/generate',
                json={
                    'model': 'deepseek-r1:14b',
                    'prompt': prompt,
                    'stream': True
                },
                stream=True
            )
            
            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    if 'response' in data:
                        yield data['response']
                        
        except Exception as e:
            yield f"\nError: {str(e)}"

    def closeEvent(self, event):
        self.server.close()
        super().closeEvent(event)

def main():
    app = QApplication(sys.argv)
    window = ChatWindow()
    
    # Register global hotkey
    keyboard.add_hotkey('ctrl+space', lambda: window.show() if not window.isVisible() else window.hide())
    
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 