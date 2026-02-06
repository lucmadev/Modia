import requests
import subprocess
import os
import shutil


def is_ollama_installed():
    return shutil.which("ollama") is not None

def pull_model(model: str):
    print("Descargando modelo...")
    subprocess.run(["ollama", "pull", model])
    print("Modelo descargado")

def download_ollama():
    print("Descargando Ollama...")
    r = requests.get("https://ollama.com/download/OllamaSetup.exe")
    with open("installer/OllamaSetup.exe", "wb") as f:
        f.write(r.content)

def install_ollama():
    if not is_ollama_installed():
        download_ollama()
        subprocess.run(["installer/OllamaSetup.exe"], shell=True)
        os.remove("installer/OllamaSetup.exe")
    else:
        print("Ollama ya está instalado")
