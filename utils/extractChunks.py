import os

BASE_DIR = "hytale_src"
OUT_FILE = "chunks.txt"

def is_interesting(path):
    keywords = ["event", "plugin", "api", "player", "server"]
    return any(k in path.lower() for k in keywords)

with open(OUT_FILE, "w", encoding="utf-8") as out:
    for root, _, files in os.walk(BASE_DIR):
        for f in files:
            if not f.endswith(".java"):
                continue

            full_path = os.path.join(root, f)
            if not is_interesting(full_path):
                continue

            with open(full_path, "r", encoding="utf-8", errors="ignore") as src:
                code = src.read()

            out.write(f"\n--- FILE: {full_path} ---\n")
            out.write(code[:6000])  # límite por chunk
