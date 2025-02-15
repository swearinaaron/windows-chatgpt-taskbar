# Windows ChatGPT Taskbar

A native Windows chat interface for DeepSeek running locally via Ollama, featuring a global hotkey and native window management.

## Features
- Native Windows interface using PyQt6
- Gradio-powered chat UI
- Global hotkey (Ctrl+Space) to show/hide
- Streaming responses from local Ollama instance
- Dark theme
- Persistent chat history during session
- Frameless window design

## Prerequisites
- Python 3.8+
- Ollama running locally with DeepSeek model installed
- Windows OS

## Installation
1. Clone the repository
2. Install dependencies: \pip install -r requirements.txt\
3. Make sure Ollama is running with DeepSeek model
4. Run: \python deepseek_native.py\

## Usage
- Press \Ctrl+Space\ to show/hide the chat window
- Type your message and press Enter to send
- Chat history is maintained during the session
