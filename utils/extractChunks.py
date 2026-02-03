import os

BASE_DIR = "hytale_src"
REPOSITORY_DIR = "repository"
OUT_FILE = "chunks.txt"

# Keywords para identificar archivos relevantes para modding
KEYWORDS = [
    # Core de plugins y eventos
    "event", "plugin", "api", "player", "server",
    # Sistema ECS (Entity Component System)
    "component", "system", "entity",
    # Comandos y registros
    "command", "registry",
    # Serialización y configuración
    "codec",
    # Plugins built-in (ejemplos útiles)
    "builtin"
]

# Límite de caracteres por archivo
# Archivos pequeños se incluyen completos, grandes se truncan
MAX_CHARS_PER_FILE = 10000

# Solo incluir archivos de Hytale (excluir librerías externas)
HYTALE_PACKAGE_PREFIX = "com" + os.sep + "hypixel" + os.sep + "hytale"

def is_hytale_file(path):
    """Verifica si el archivo pertenece al código de Hytale (no librerías externas)"""
    # Normalizar separadores de ruta para compatibilidad cross-platform
    normalized_path = path.replace("\\", "/")
    return HYTALE_PACKAGE_PREFIX.replace("\\", "/") in normalized_path

def is_interesting(path):
    """Verifica si el archivo es relevante para modding basado en keywords"""
    path_lower = path.lower()
    return any(keyword in path_lower for keyword in KEYWORDS)

def get_file_priority(path, is_repository=False):
    """
    Retorna una prioridad numérica para ordenar archivos.
    Mayor número = mayor prioridad.
    """
    path_lower = path.lower()
    priority = 0
    
    # Archivos de repository (mods reales) tienen máxima prioridad
    if is_repository:
        priority += 150
    
    # Archivos del core del servidor tienen máxima prioridad
    if "server" + os.sep + "core" in path_lower:
        priority += 100
    
    # Archivos de plugin tienen alta prioridad
    if "plugin" in path_lower:
        priority += 50
    
    # Archivos de eventos tienen alta prioridad
    if "event" in path_lower:
        priority += 40
    
    # Archivos de componentes/sistemas tienen prioridad media-alta
    if "component" in path_lower or "system" in path_lower:
        priority += 30
    
    # Archivos de comandos tienen prioridad media
    if "command" in path_lower:
        priority += 20
    
    # Archivos built-in tienen prioridad baja (son ejemplos)
    if "builtin" in path_lower:
        priority += 10
    
    return priority

def process_directory(directory, is_repository=False):
    """
    Procesa un directorio y retorna lista de archivos con prioridades.
    
    Args:
        directory: Ruta del directorio a procesar
        is_repository: Si True, no aplica filtro de Hytale (son mods externos)
    """
    files_with_priority = []
    
    if not os.path.exists(directory):
        return files_with_priority
    
    for root, _, files in os.walk(directory):
        for f in files:
            if not f.endswith(".java"):
                continue
            
            full_path = os.path.join(root, f)
            
            # Para archivos de Hytale, aplicar filtro de paquete
            if not is_repository:
                if not is_hytale_file(full_path):
                    continue
            
            # Solo archivos relevantes
            if not is_interesting(full_path):
                continue
            
            priority = get_file_priority(full_path, is_repository=is_repository)
            files_with_priority.append((priority, full_path))
    
    return files_with_priority

# Recopilar todos los archivos relevantes con sus prioridades
files_with_priority = []

# Procesar código fuente de Hytale
print("Procesando código fuente de Hytale...")
hytale_files = process_directory(BASE_DIR, is_repository=False)
files_with_priority.extend(hytale_files)
print(f"  Encontrados {len(hytale_files)} archivos de Hytale")

# Procesar mods del repository
print("Procesando mods del repository...")
repository_files = process_directory(REPOSITORY_DIR, is_repository=True)
files_with_priority.extend(repository_files)
print(f"  Encontrados {len(repository_files)} archivos del repository")

# Ordenar por prioridad (mayor primero)
files_with_priority.sort(key=lambda x: x[0], reverse=True)

# Escribir archivos ordenados por prioridad
with open(OUT_FILE, "w", encoding="utf-8") as out:
    for priority, full_path in files_with_priority:
        try:
            with open(full_path, "r", encoding="utf-8", errors="ignore") as src:
                code = src.read()
            
            # Para archivos pequeños, incluir completo; para grandes, truncar
            original_length = len(code)
            if len(code) > MAX_CHARS_PER_FILE:
                code = code[:MAX_CHARS_PER_FILE]
                code += f"\n\n... [Archivo truncado, total: {original_length} caracteres] ..."
            
            out.write(f"\n--- FILE: {full_path} ---\n")
            out.write(code)
            out.write("\n")
        except Exception as e:
            # Continuar si hay error leyendo un archivo
            print(f"Error procesando {full_path}: {e}")
            continue

print(f"\nExtracción completada: {len(files_with_priority)} archivos procesados")
print(f"  - {len(hytale_files)} archivos de Hytale")
print(f"  - {len(repository_files)} archivos del repository")
