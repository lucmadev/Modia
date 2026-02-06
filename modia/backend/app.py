"""API REST para Modia - Backend de la aplicación web"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import sys
import subprocess
from pathlib import Path

from backend.config import ModiaConfig, DEFAULT_DB_PATH
from backend.chat import ModiaChat
from backend.db import ModiaDB
from backend.llm import LLMProviderManager
from backend.configManager import ConfigManager
from langchain_core.documents import Document

# Inicializar FastAPI
app = FastAPI(
    title="Modia API",
    description="API REST para Modia - Hytale Modding Copilot",
    version="0.1.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instancias globales
_config: Optional[ModiaConfig] = None
_db: Optional[ModiaDB] = None
_chat: Optional[ModiaChat] = None
_llm_manager = LLMProviderManager()
_config_manager = ConfigManager()


# ==================== MODELOS PYDANTIC ====================

class QueryRequest(BaseModel):
    """Request para hacer una pregunta"""
    message: str
    top_k: Optional[int] = 5
    provider: Optional[str] = None
    model: Optional[str] = None
    explain_mode: Optional[bool] = None


class QueryResponse(BaseModel):
    """Response de una pregunta"""
    answer: str
    provider: str
    model: str


class DBAddRequest(BaseModel):
    """Request para agregar documentos a la DB"""
    text: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class DBAddResponse(BaseModel):
    """Response de agregar documentos"""
    id: str
    message: str


class DBDeleteRequest(BaseModel):
    """Request para eliminar documentos"""
    ids: Optional[List[str]] = None
    delete_all: bool = False


class LLMConfigureRequest(BaseModel):
    """Request para configurar un proveedor LLM"""
    provider: str
    api_key: str
    base_url: Optional[str] = None


# ==================== MODELOS PARA OPS (REPOS / DB) ====================

class RepoAddRequest(BaseModel):
    """Request para añadir un repositorio git a repository/repos.txt"""
    url: str


class DBRebuildRequest(BaseModel):
    """Request para reconstruir la base vectorial"""
    sync_repos: bool = True


class StepResult(BaseModel):
    """Resultado de un paso de operación"""
    name: str
    ok: bool
    logs: str
    duration_ms: int


# ==================== FUNCIONES AUXILIARES ====================

def get_config() -> ModiaConfig:
    """Obtiene o crea la configuración"""
    global _config
    if _config is None:
        _config = ModiaConfig.from_env()
    return _config


def get_db() -> ModiaDB:
    """Obtiene o crea la instancia de DB"""
    global _db
    if _db is None:
        config = get_config()
        _db = ModiaDB(str(config.db_path), config.embedding_model)
    return _db


def get_chat(
    provider: Optional[str] = None,
    model: Optional[str] = None
) -> ModiaChat:
    """Obtiene o crea la instancia de chat"""
    global _chat
    
    config = get_config()
    db = get_db()
    
    # Usar proveedor especificado o el por defecto
    provider_name = provider or _config_manager.get_default_provider()
    
    # Configurar proveedores desde configuración si es necesario
    _setup_providers_from_config()
    
    # Obtener LLM del proveedor
    llm_model = model or config.llm_model
    llm = _llm_manager.get_llm(
        provider_name=provider_name,
        model=llm_model,
        temperature=config.temperature
    )
    
    _chat = ModiaChat(db.db, llm, config.max_memory)
    return _chat


def _setup_providers_from_config():
    """Configura los proveedores desde la configuración guardada"""
    # OpenAI
    openai_key = _config_manager.get_api_key("openai")
    if openai_key:
        provider_config = _config_manager.get_provider_config("openai")
        base_url = provider_config.get("base_url")
        _llm_manager.configure_openai(openai_key, base_url)
    
    # DeepSeek
    deepseek_key = _config_manager.get_api_key("deepseek")
    if deepseek_key:
        _llm_manager.configure_deepseek(deepseek_key)
    
    # Gemini
    gemini_key = _config_manager.get_api_key("gemini")
    if gemini_key:
        _llm_manager.configure_gemini(gemini_key)
    
    # Anthropic
    anthropic_key = _config_manager.get_api_key("anthropic")
    if anthropic_key:
        _llm_manager.configure_anthropic(anthropic_key)


# ==================== OPS: REPOS / DB (UTILS) ====================

ROOT_DIR = Path(__file__).resolve().parents[2]
REPO_DIR = ROOT_DIR / "repository"
REPOS_FILE = REPO_DIR / "repos.txt"
UTILS_DIR = ROOT_DIR / "utils"

_ops_busy: bool = False


def _read_repos_file() -> List[str]:
    if not REPOS_FILE.exists():
        return []
    try:
        lines = REPOS_FILE.read_text(encoding="utf-8").splitlines()
    except Exception:
        return []

    urls: List[str] = []
    for line in lines:
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        urls.append(s)
    return urls


def _write_repos_file(urls: List[str]) -> None:
    REPO_DIR.mkdir(parents=True, exist_ok=True)
    content = "\n".join(urls) + ("\n" if urls else "")
    REPOS_FILE.write_text(content, encoding="utf-8")


def _run_script(script_path: Path) -> str:
    """
    Ejecuta un script Python de utils en el ROOT_DIR y devuelve logs combinados.
    Lanza HTTPException si falla.
    """
    if not script_path.exists():
        raise HTTPException(status_code=404, detail=f"Script no encontrado: {script_path}")

    try:
        proc = subprocess.run(
            [sys.executable, "-u", str(script_path)],
            cwd=str(ROOT_DIR),
            capture_output=True,
            text=True
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"No se pudo ejecutar {script_path.name}: {e}")

    logs = (proc.stdout or "") + ("\n" if proc.stdout and proc.stderr else "") + (proc.stderr or "")
    logs = logs.strip() or f"{script_path.name}: (sin salida)"

    if proc.returncode != 0:
        raise HTTPException(
            status_code=500,
            detail=f"{script_path.name} falló (exit={proc.returncode}).\n{logs}"
        )

    return logs


def _run_script_step(name: str, script_path: Path) -> Dict[str, Any]:
    """Ejecuta un script y devuelve estructura de step con duración y logs."""
    import time

    start = time.time()
    try:
        logs = _run_script(script_path)
        ok = True
    except HTTPException as e:
        ok = False
        logs = str(e.detail)
    duration_ms = int((time.time() - start) * 1000)
    return {"name": name, "ok": ok, "logs": logs, "duration_ms": duration_ms}


# ==================== ENDPOINTS DE CHAT ====================

@app.post("/api/ask", response_model=QueryResponse)
async def ask(request: QueryRequest):
    """Hace una pregunta a Modia"""
    config = get_config()
    
    if not config.validate():
        raise HTTPException(
            status_code=404,
            detail=f"Base de datos no encontrada en {config.db_path}"
        )
    
    try:
        # Resetear chat para usar nuevo proveedor/modelo si es necesario
        global _chat
        if request.provider or request.model:
            _chat = None
        
        chat_instance = get_chat(provider=request.provider, model=request.model)
        current_provider = request.provider or _config_manager.get_default_provider()
        current_model = request.model or config.llm_model
        
        answer = chat_instance.ask(
            request.message, 
            top_k=request.top_k,
            explain_mode=request.explain_mode
        )
        
        return QueryResponse(
            answer=answer,
            provider=current_provider,
            model=current_model
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@app.get("/api/memory")
async def get_memory():
    """Obtiene la memoria conversacional actual"""
    global _chat
    if _chat is None:
        return {"memory": []}
    return {"memory": _chat.get_memory()}


@app.delete("/api/memory")
async def clear_memory():
    """Limpia la memoria conversacional"""
    global _chat
    if _chat is not None:
        _chat.clear_memory()
    return {"message": "Memoria limpiada"}


# ==================== ENDPOINTS DE DB ====================

@app.get("/api/db/search")
async def db_search(
    query: str,
    k: int = 5,
    with_scores: bool = False
):
    """Búsqueda semántica en la base de datos"""
    db = get_db()
    
    if with_scores:
        results = db.search_with_scores(query, k=k)
        return {
            "results": [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": float(score)
                }
                for doc, score in results
            ]
        }
    else:
        results = db.search(query, k=k)
        return {
            "results": [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata
                }
                for doc in results
            ]
        }


@app.post("/api/db/add", response_model=DBAddResponse)
async def db_add(request: DBAddRequest):
    """Agrega documentos a la base de datos"""
    if not request.text:
        raise HTTPException(status_code=400, detail="El campo 'text' es requerido")
    
    db = get_db()
    metadatas = [request.metadata] if request.metadata else None
    ids = db.add_texts([request.text], metadatas=metadatas)
    db.persist()
    
    return DBAddResponse(
        id=ids[0],
        message="Documento agregado correctamente"
    )


@app.get("/api/db/list")
async def db_list(limit: int = 10):
    """Lista documentos en la base de datos"""
    db = get_db()
    docs = db.get_all(limit=limit)
    
    return {
        "documents": [
            {
                "content": doc.page_content,
                "metadata": doc.metadata
            }
            for doc in docs
        ],
        "total": len(docs)
    }


@app.get("/api/db/stats")
async def db_stats():
    """Muestra estadísticas de la base de datos"""
    db = get_db()
    stats_data = db.stats()
    return stats_data


@app.post("/api/db/rebuild")
async def db_rebuild(request: DBRebuildRequest):
    """
    Reconstruye la base:
    - (opcional) sync repos (git clone/pull)
    - extractChunks.py (genera chunks.txt)
    - buildDB.py (genera/persiste hytale_db)
    """
    global _ops_busy, _db, _chat
    if _ops_busy:
        raise HTTPException(status_code=409, detail="Hay una operación en curso. Intenta de nuevo en unos segundos.")

    _ops_busy = True
    try:
        steps: List[Dict[str, Any]] = []

        if request.sync_repos:
            steps.append(_run_script_step("Clone/Pull repos", UTILS_DIR / "cloneRepos.py"))
            if not steps[-1]["ok"]:
                raise HTTPException(status_code=500, detail=steps[-1]["logs"])

        steps.append(_run_script_step("Extract chunks", UTILS_DIR / "extractChunks.py"))
        if not steps[-1]["ok"]:
            raise HTTPException(status_code=500, detail=steps[-1]["logs"])

        steps.append(_run_script_step("Build DB", UTILS_DIR / "buildDB.py"))
        if not steps[-1]["ok"]:
            raise HTTPException(status_code=500, detail=steps[-1]["logs"])

        # Resetear instancias para que lean la DB nueva
        _db = None
        _chat = None

        all_logs = []
        for s in steps:
            all_logs.append(f"== {s['name']} ==")
            all_logs.append(s["logs"])

        return {
            "message": "Rebuild completado",
            "logs": "\n\n".join(all_logs),
            "steps": steps
        }
    finally:
        _ops_busy = False


@app.delete("/api/db/delete")
async def db_delete(request: DBDeleteRequest):
    """Elimina documentos de la base de datos"""
    db = get_db()
    
    if request.delete_all:
        db.delete()
        message = "Todos los documentos eliminados"
    elif request.ids:
        db.delete(ids=request.ids)
        message = f"{len(request.ids)} documento(s) eliminado(s)"
    else:
        raise HTTPException(
            status_code=400,
            detail="Debes proporcionar 'ids' o 'delete_all=true'"
        )
    
    db.persist()
    return {"message": message}


# ==================== ENDPOINTS DE LLM ====================

@app.post("/api/llm/configure")
async def llm_configure(request: LLMConfigureRequest):
    """Configura un proveedor de LLM"""
    provider_lower = request.provider.lower()
    
    if provider_lower not in ["openai", "deepseek", "gemini", "anthropic"]:
        raise HTTPException(
            status_code=400,
            detail=f"Proveedor '{request.provider}' no soportado"
        )
    
    # Guardar API key
    _config_manager.set_api_key(provider_lower, request.api_key)
    
    # Guardar configuración adicional si existe
    if request.base_url:
        _config_manager.set_provider_config(
            provider_lower, 
            {"base_url": request.base_url}
        )
    
    # Configurar en el manager
    if provider_lower == "openai":
        _llm_manager.configure_openai(request.api_key, request.base_url)
    elif provider_lower == "deepseek":
        _llm_manager.configure_deepseek(request.api_key)
    elif provider_lower == "gemini":
        _llm_manager.configure_gemini(request.api_key)
    elif provider_lower == "anthropic":
        _llm_manager.configure_anthropic(request.api_key)
    
    return {"message": f"Proveedor '{request.provider}' configurado correctamente"}


@app.get("/api/llm/providers")
async def llm_list_providers():
    """Lista todos los proveedores disponibles y su estado"""
    # Asegurar que los providers configurados en disco queden registrados en runtime
    _setup_providers_from_config()

    # Listar SIEMPRE todos los providers soportados aunque no estén configurados
    # (si no, el frontend no puede seleccionar OpenAI/Gemini/etc. para pegar API key)
    supported_providers = ["ollama", "openai", "deepseek", "gemini", "anthropic"]
    registered_providers = set(_llm_manager.list_providers())
    configured = _config_manager.list_configured_providers()
    default = _config_manager.get_default_provider()

    def _known_models(provider_name: str) -> List[str]:
        """Modelos conocidos para mostrar aunque el provider aún no esté configurado."""
        name = provider_name.lower()
        if name == "ollama":
            try:
                return _llm_manager.get("ollama").get_available_models()
            except Exception:
                return ["llama3.1:8b", "mistral", "codellama"]
        if name == "openai":
            return ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"]
        if name == "deepseek":
            return ["deepseek-chat", "deepseek-coder"]
        if name == "gemini":
            return ["gemini-pro", "gemini-pro-vision", "gemini-1.5-pro", "gemini-1.5-flash"]
        if name == "anthropic":
            return [
                "claude-3-5-sonnet-20241022",
                "claude-3-5-haiku-20241022",
                "claude-3-opus-20240229",
                "claude-3-sonnet-20240229"
            ]
        return []
    
    providers_info = []
    for provider_name in supported_providers:
        is_configured = provider_name in configured
        is_default = provider_name == default
        
        try:
            # Solo va a existir si está registrado (ollama o configurado)
            if provider_name in registered_providers:
                provider = _llm_manager.get(provider_name)
                models = provider.get_available_models()
            else:
                models = _known_models(provider_name)
        except Exception:
            models = _known_models(provider_name)
        
        providers_info.append({
            "name": provider_name,
            "configured": is_configured,
            "default": is_default,
            "registered": provider_name in registered_providers,
            "models": models
        })
    
    return {"providers": providers_info}


@app.post("/api/llm/set-default")
async def llm_set_default(provider: str):
    """Establece el proveedor por defecto"""
    provider_lower = provider.lower()
    
    if provider_lower not in _llm_manager.list_providers():
        raise HTTPException(
            status_code=400,
            detail=f"Proveedor '{provider}' no encontrado"
        )
    
    # Verificar que esté configurado (excepto Ollama)
    if provider_lower != "ollama" and provider_lower not in _config_manager.list_configured_providers():
        raise HTTPException(
            status_code=400,
            detail=f"Proveedor '{provider}' no está configurado"
        )
    
    _config_manager.set_default_provider(provider_lower)
    _llm_manager.set_default(provider_lower)
    
    return {"message": f"Proveedor por defecto establecido: {provider}"}


@app.delete("/api/llm/remove/{provider}")
async def llm_remove(provider: str):
    """Elimina la configuración de un proveedor"""
    provider_lower = provider.lower()
    
    if provider_lower == "ollama":
        raise HTTPException(
            status_code=400,
            detail="No se puede eliminar Ollama (proveedor por defecto)"
        )
    
    if provider_lower not in _config_manager.list_configured_providers():
        raise HTTPException(
            status_code=404,
            detail=f"Proveedor '{provider}' no está configurado"
        )
    
    _config_manager.remove_api_key(provider_lower)
    return {"message": f"Configuración de '{provider}' eliminada"}


# ==================== ENDPOINTS DE CONFIGURACIÓN ====================

@app.get("/api/config")
async def get_config_endpoint():
    """Obtiene la configuración actual"""
    config = get_config()
    return {
        "db_path": str(config.db_path),
        "llm_model": config.llm_model,
        "embedding_model": config.embedding_model,
        "temperature": config.temperature,
        "max_memory": config.max_memory,
        "top_k": config.top_k,
        "valid": config.validate()
    }


@app.get("/api/health")
async def health():
    """Endpoint de salud"""
    config = get_config()
    return {
        "status": "ok",
        "db_exists": config.db_path.exists(),
        "db_path": str(config.db_path)
    }


# ==================== ENDPOINTS DE REPOS ====================

@app.get("/api/repos")
async def repos_list():
    """Lista las URLs en repository/repos.txt"""
    return {
        "path": str(REPOS_FILE),
        "urls": _read_repos_file()
    }


@app.post("/api/repos")
async def repos_add(request: RepoAddRequest):
    """Agrega una URL git a repository/repos.txt (si no existe)"""
    url = (request.url or "").strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL requerida")

    urls = _read_repos_file()
    if url not in urls:
        urls.append(url)
        _write_repos_file(urls)

    return {"message": "Repo agregado", "urls": urls}


@app.post("/api/repos/sync")
async def repos_sync():
    """Clona/actualiza repositorios usando utils/cloneRepos.py"""
    global _ops_busy
    if _ops_busy:
        raise HTTPException(status_code=409, detail="Hay una operación en curso. Intenta de nuevo en unos segundos.")

    _ops_busy = True
    try:
        step = _run_script_step("Clone/Pull repos", UTILS_DIR / "cloneRepos.py")
        if not step["ok"]:
            raise HTTPException(status_code=500, detail=step["logs"])
        return {"message": "Sync completado", "logs": step["logs"], "steps": [step]}
    finally:
        _ops_busy = False


# ==================== SERVIR UI ESTÁTICA ====================

# Obtener ruta de la UI
UI_DIR = Path(__file__).parent.parent / "ui"
UI_DIST_DIR = UI_DIR / "dist"

# Montar archivos estáticos (CSS, JS, etc.) desde la carpeta ui
# IMPORTANTE: Esto debe ir ANTES de la ruta "/" para que funcione correctamente
app.mount("/css", StaticFiles(directory=str(UI_DIR / "css")), name="css")
app.mount("/js", StaticFiles(directory=str(UI_DIR / "js")), name="js")
app.mount("/svg", StaticFiles(directory=str(UI_DIR / "svg")), name="svg")

# Montar carpeta dist si existe
if UI_DIST_DIR.exists():
    app.mount("/dist", StaticFiles(directory=str(UI_DIST_DIR)), name="dist")

# Servir index.html en la raíz (debe ir al final para no interceptar otras rutas)
@app.get("/")
async def serve_index():
    """Sirve el archivo index.html de la UI"""
    index_path = UI_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    else:
        raise HTTPException(status_code=404, detail="UI no encontrada")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
