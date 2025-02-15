import tkinter as tk
from tkinter import ttk, messagebox, font
import threading
import requests
import json
import sys

class ResponseWindow:
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("DeepSeek Chat - TEST VERSION")
        
        # Make window bright red to prove changes
        self.window.configure(bg='#FF0000')
        
        # Create text widget with red theme
        self.text = tk.Text(
            self.window,
            wrap=tk.WORD,
            bg='#FF2222',  # Bright red background
            fg='white',    # White text
            font=('Segoe UI', 16, 'bold'),  # Bigger, bolder font
            padx=20,
            pady=20,
            relief=tk.RAISED,
            borderwidth=5
        )
        self.text.pack(fill=tk.BOTH, expand=True)
        
        # Add a test label
        test_label = tk.Label(
            self.window,
            text="THIS IS A TEST - BRIGHT RED VERSION",
            bg='#FF0000',
            fg='white',
            font=('Arial', 14, 'bold')
        )
        test_label.pack(pady=10)
        
        # Keep window on top
        self.window.wm_attributes('-topmost', True)
        self.window.focus_force()

    def append_text(self, text):
        """Add new text and scroll to end"""
        self.text.configure(state='normal')
        self.text.insert('end', text)
        self.text.see('end')
        self.text.configure(state='disabled')

class LocalAISearch:
    def __init__(self):
        print("Initializing Local AI Search...")
        
        # Set model to deepseek
        self.model_name = "deepseek-r1:14b"
        print(f"Using model: {self.model_name}")
        
        # Verify Ollama is running
        try:
            response = requests.get('http://localhost:11434/api/tags')
            if not any(model['name'] == self.model_name for model in response.json()['models']):
                print(f"Warning: {self.model_name} not found. Please run: ollama pull {self.model_name}")
                exit(1)
        except Exception as e:
            print("Error connecting to Ollama. Is it running?")
            print(f"Error: {e}")
            exit(1)
        
        # Create main window
        self.root = tk.Tk()
        self.root.title("DeepSeek Search")
        
        # Configure style
        style = ttk.Style()
        style.configure('Search.TEntry', padding=5)
        
        # Make window appear on taskbar
        self.root.wm_attributes('-topmost', True)
        self.root.overrideredirect(True)
        
        # Create search box with dark theme
        self.frame = ttk.Frame(self.root)
        self.frame.pack(fill='x')
        
        self.search_var = tk.StringVar()
        self.search_box = ttk.Entry(
            self.frame, 
            textvariable=self.search_var,
            width=50,
            style='Search.TEntry'
        )
        self.search_box.pack(side='left', fill='x', expand=True)
        
        # Bind events
        self.search_box.bind('<Return>', self.handle_search)
        self.search_box.bind('<Escape>', lambda e: self.root.withdraw())
        
        # Position window
        self.position_window()
        
        # Hide window initially
        self.root.withdraw()
        
        print("Registering hotkey (Win + Space)...")
        self.register_hotkey()
        print("Initialization complete!")

    def position_window(self):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = 500
        window_height = 30
        
        x = (screen_width - window_width) // 2
        y = screen_height - window_height - 40
        
        self.root.geometry(f'{window_width}x{window_height}+{x}+{y}')

    def register_hotkey(self):
        def hotkey_thread():
            try:
                import keyboard
                print("Registering Win+Space hotkey...")
                keyboard.add_hotkey('windows+space', self.toggle_window)
                print("Hotkey registered successfully!")
                keyboard.wait()
            except Exception as e:
                print(f"Error registering hotkey: {e}")
        
        threading.Thread(target=hotkey_thread, daemon=True).start()

    def toggle_window(self):
        print("Toggle window called")
        if self.root.state() == 'withdrawn':
            self.root.deiconify()
            self.search_box.focus_set()
            print("Window shown")
        else:
            self.root.withdraw()
            print("Window hidden")

    def handle_search(self, event):
        query = self.search_var.get()
        print(f"Handling search query: {query}")
        if query.strip():
            threading.Thread(target=self.generate_response, args=(query,), daemon=True).start()
        self.search_var.set('')
        self.root.withdraw()

    def generate_response(self, query):
        print(f"\n=== Starting response generation ===")
        print(f"Query: {query}")
        try:
            print("Creating response window...")
            response_window = ResponseWindow(self.root)
            print("Response window created")
            
            print("Sending request to Ollama...")
            response = requests.post(
                'http://localhost:11434/api/generate',
                json={
                    'model': self.model_name,
                    'prompt': query,
                    'stream': True
                },
                stream=True
            )
            print("Request sent, processing response...")
            
            # Process the streaming response
            for line in response.iter_lines():
                if line:
                    print(f"Raw line: {line}")
                    data = json.loads(line)
                    print(f"Parsed data: {data}")
                    
                    if 'response' in data:
                        chunk = data['response']
                        print(f"Got chunk: {chunk}")
                        # Update the response window with new text
                        self.root.after(0, lambda t=chunk: response_window.append_text(t))
                        print("Chunk added to window")
                        
                    if data.get('done', False):
                        print("Response complete")
                        break
                        
        except Exception as e:
            print(f"\n!!! Error in generate_response !!!")
            print(f"Error type: {type(e)}")
            print(f"Error message: {str(e)}")
            print(f"Full error: {e}")
            error_msg = str(e)
            self.root.after(0, lambda: messagebox.showerror("Error", error_msg))

        print("=== Response generation complete ===\n")

    def run(self):
        print("Starting main loop...")
        self.root.mainloop()
        print("Main loop ended")

if __name__ == "__main__":
    app = LocalAISearch()
    app.run() 