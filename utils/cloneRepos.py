import os
import subprocess

REPOS_FILE = "repository/repos.txt"
REPOS_DIR = "repository"

def get_repo_name(url):
    """Extrae el nombre del repositorio de la URL"""
    # Ejemplo: https://github.com/user/repo.git -> repo
    name = url.rstrip('/').split('/')[-1]
    if name.endswith('.git'):
        name = name[:-4]
    return name

def clone_repository(url, target_dir):
    """Clona un repositorio en el directorio objetivo"""
    repo_name = get_repo_name(url)
    repo_path = os.path.join(target_dir, repo_name)
    
    # Si ya existe, hacer pull en lugar de clonar
    if os.path.exists(repo_path) and os.path.isdir(repo_path):
        print(f"  Repositorio '{repo_name}' ya existe. Actualizando...")
        try:
            subprocess.run(
                ["git", "pull"],
                cwd=repo_path,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            print(f"  ✓ '{repo_name}' actualizado")
            return True
        except subprocess.CalledProcessError:
            print(f"  ⚠ Error actualizando '{repo_name}'. Continuando...")
            return False
        except FileNotFoundError:
            print(f"  ⚠ Git no encontrado. Saltando '{repo_name}'...")
            return False
    else:
        # Clonar nuevo repositorio
        print(f"  Clonando '{repo_name}'...")
        try:
            subprocess.run(
                ["git", "clone", url, repo_path],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            print(f"  ✓ '{repo_name}' clonado")
            return True
        except subprocess.CalledProcessError:
            print(f"  ✗ Error clonando '{repo_name}'")
            return False
        except FileNotFoundError:
            print(f"  ✗ Git no encontrado. Instala Git para clonar repositorios.")
            return False

def main():
    """Función principal que lee repos.txt y clona los repositorios"""
    # Verificar que existe el archivo repos.txt
    if not os.path.exists(REPOS_FILE):
        print(f"Archivo {REPOS_FILE} no encontrado. Saltando clonado de repositorios.")
        return
    
    # Crear directorio repository si no existe
    os.makedirs(REPOS_DIR, exist_ok=True)
    
    # Leer URLs de repositorios
    print(f"Leyendo {REPOS_FILE}...")
    try:
        with open(REPOS_FILE, "r", encoding="utf-8") as f:
            urls = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]
    except Exception as e:
        print(f"Error leyendo {REPOS_FILE}: {e}")
        return
    
    if not urls:
        print("No se encontraron URLs en repos.txt")
        return
    
    print(f"Encontradas {len(urls)} URLs de repositorios")
    print("Clonando/actualizando repositorios...\n")
    
    success_count = 0
    for url in urls:
        if clone_repository(url, REPOS_DIR):
            success_count += 1
    
    print(f"\nProceso completado: {success_count}/{len(urls)} repositorios procesados correctamente")

if __name__ == "__main__":
    main()

