import webview
import threading
import uvicorn
from backend.app import app
from installer.installOllama import install_ollama, pull_model
from backend.config import DEFAULT_EMBEDDING_MODEL

def start_api():
    uvicorn.run(app, host="127.0.0.1", port=7860)

threading.Thread(target=start_api, daemon=True).start()

install_ollama()
pull_model(DEFAULT_EMBEDDING_MODEL)


webview.create_window(
    "Modia",
    "http://127.0.0.1:7860",
    width=1200,
    height=800
)
webview.start()
