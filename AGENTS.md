# 📋 AGENTS.md - Guía de Referencia Rápida para Modia

> **Propósito**: Este documento permite entender rápidamente el proyecto Modia sin tener que releer todo el código cada vez.

---

## 🎯 ¿Qué es Modia?

**Modia** es un **copiloto técnico local** para desarrollo de plugins de **Hytale**, basado en **RAG (Retrieval-Augmented Generation)** con memoria conversacional explícita.

**Objetivo**: Responder rápido, directo y con criterio técnico sobre el código de HytaleServer, sin tener que releer el código del servidor repetidamente.

**Estado**: Early Access (el juego Hytale está en early access, el proyecto también).

---

## 🏗️ Arquitectura y Stack

### Stack Tecnológico
- **Python 3.10+**
- **Ollama** (LLM + embeddings)
- **LangChain** (orquestación)
- **ChromaDB** (base de datos vectorial)

### Modelos Recomendados
- **LLM**: `llama3.1:8b`
- **Embeddings**: `nomic-embed-text`

### Componentes Principales

1. **`modia-chat.py`**: Script principal del chat interactivo
2. **`utils/extractChunks.py`**: Extrae chunks relevantes del código descompilado
3. **`utils/buildDB.py`**: Construye la base de datos vectorial con ChromaDB
4. **`Makefile`** / **`build.ps1`**: Scripts de build para Linux/Mac y Windows

---

## 🔄 Flujo de Trabajo

### 1. Setup Inicial (Indexación)

**Proceso completo**:
```
HytaleServer.jar → Descompilación (CFR) → Extracción de chunks → Base vectorial
```

**Pasos detallados**:

1. **Colocar JAR**: `server/HytaleServer.jar`
2. **Descompilar**: Usa CFR (Java Decompiler) para extraer código fuente Java
   - Linux/Mac: `make decompile`
   - Windows: `./build.ps1` (incluye descompilación)
3. **Extraer chunks**: Filtra archivos `.java` relevantes (keywords: "event", "plugin", "api", "player", "server")
   - Script: `utils/extractChunks.py`
   - Output: `chunks.txt`
   - Límite: 6000 caracteres por archivo
4. **Construir DB**: Crea base vectorial con ChromaDB
   - Script: `utils/buildDB.py`
   - Chunk size: 800 caracteres
   - Overlap: 200 caracteres
   - Output: `./hytale_db/`

### 2. Uso del Chat

**Ejecución**:
- Linux/Mac: `python modia-chat.py`
- Windows: `python ./modia-chat.py`

**Flujo de cada pregunta**:
1. Usuario escribe pregunta
2. Búsqueda semántica en ChromaDB (top 5 documentos)
3. Construcción de prompt con:
   - System prompt (reglas estrictas)
   - Memoria conversacional (últimos mensajes relevantes)
   - Contexto técnico (documentos encontrados)
   - Pregunta del usuario
4. Invocación del LLM
5. Almacenamiento selectivo en memoria (si es relevante)
6. Resumen automático cuando memoria alcanza MAX_MEMORY (6 mensajes)

---

## 📁 Estructura de Archivos

```
Modia/
├── modia-chat.py          # Script principal del chat
├── utils/
│   ├── extractChunks.py   # Extrae chunks relevantes del código
│   └── buildDB.py         # Construye la base vectorial
├── server/
│   └── HytaleServer.jar   # JAR a descompilar (debe estar presente)
├── hytale_src/            # Código descompilado (generado)
├── hytale_db/             # Base de datos vectorial (generada)
├── chunks.txt             # Chunks extraídos (generado)
├── libs/
│   └── cfr.jar            # Java decompiler (descargado automáticamente)
├── Makefile               # Build para Linux/Mac
├── build.ps1              # Build para Windows
├── requirements.txt       # Dependencias Python
└── venv/                  # Entorno virtual Python
```

---

## 🧠 Características Técnicas Clave

### Memoria Conversacional

- **NO depende de memoria implícita del modelo**
- **Almacenamiento selectivo**: Solo mensajes técnicos relevantes (keywords: "entity", "trigger", "event", "api", "server", "engine", "lifecycle", "mod", "hook")
- **Límite**: MAX_MEMORY = 6 mensajes
- **Resumen automático**: Cuando se alcanza el límite, se genera un resumen técnico de 5 puntos y se reemplaza la memoria

### Modo Explicación (Natural)

- **Sin comandos especiales**: Detecta automáticamente cuando el usuario pide explicaciones
- **Triggers**: "explicame", "cómo funciona", "no entiendo", "qué hace", "explain", "how does it work", etc.
- **Comportamiento**: Activa modo explicación con más detalle, pero sin revelar contexto interno

### System Prompt

**Reglas absolutas**:
- Responder SOLO con la salida final
- NO revelar historia, contexto o razonamiento interno
- NO repetir o describir el contexto proporcionado
- NO usar títulos, secciones o headers
- NO usar calificadores como "según el contexto"

**Comportamiento**:
- Proporcionar respuesta incluso si la información es parcial
- Inferir detalles usando patrones comunes de game engines
- Si una característica no existe, decirlo claramente
- Lenguaje técnico, directo y conciso
- Enfoque orientado a modding

---

## 🗺️ Roadmap (Tareas Pendientes)

Según README.md líneas 130-137:

- [ ] **Convertir el chat en CLI**: Actualmente es un script Python interactivo básico
- [ ] **Agregar comandos útiles**: Como `/explain` o `/raw` (aunque ya hay modo explicación natural)
- [ ] **Persistencia de memoria en disco**: Actualmente la memoria es solo en memoria (se pierde al cerrar)
- [ ] **Autocompletado de comandos**: Mejorar UX del CLI
- [ ] **Flags `--no-rag` / `--rag-only`**: Permitir desactivar RAG o usar solo RAG
- [ ] **Perfiles por proyecto**: Múltiples configuraciones/base de datos por proyecto
- [ ] **Empaquetado como binario**: Distribución más fácil (probablemente con PyInstaller o similar)

---

## 🔧 Detalles de Implementación

### Extracción de Chunks (`utils/extractChunks.py`)

- **Filtrado**: Solo archivos `.java` que contengan keywords en la ruta
- **Keywords**: `["event", "plugin", "api", "player", "server"]`
- **Límite por archivo**: 6000 caracteres (primeros 6000)
- **Output**: Formato `--- FILE: {path} ---\n{code}`

### Construcción de DB (`utils/buildDB.py`)

- **Loader**: `TextLoader` para `chunks.txt`
- **Splitter**: `RecursiveCharacterTextSplitter`
  - Chunk size: 800
  - Overlap: 200
- **Embeddings**: `OllamaEmbeddings` con `nomic-embed-text`
- **Vector Store**: `Chroma` con persistencia en `./hytale_db`

### Chat Principal (`modia-chat.py`)

- **Búsqueda**: `db.similarity_search(q, k=5)` - top 5 documentos
- **LLM**: `ChatOllama` con `llama3.1:8b`, temperature=0.1
- **Memoria**: Lista de dicts `[{"role": "user/assistant", "content": "..."}]`
- **Normalización**: Maneja diferentes formatos de respuesta del LLM (string, list, dict)

### Función `should_store(text)`

- **Filtros**: 
  - Texto debe tener al menos 40 caracteres
  - Debe contener keywords técnicos relevantes
- **Keywords**: `["entity", "entidad", "trigger", "evento", "api", "event", "server", "engine", "lifecycle", "mod", "hook"]`

---

## ⚠️ Notas Importantes

1. **Ollama debe estar corriendo**: El proyecto depende de Ollama local
2. **Modelos deben estar descargados**: `llama3.1:8b` y `nomic-embed-text`
3. **Java requerido**: Para descompilar el JAR con CFR
4. **Proyecto no oficial**: No afiliado con Hypixel Studios, uso educativo/desarrollo
5. **Memoria no persistente**: Actualmente se pierde al cerrar el chat

---

## 🚀 Comandos Útiles

### Setup Completo (Windows)
```powershell
./build.ps1
```

### Setup Completo (Linux/Mac)
```bash
make install  # Instala dependencias
make decompile  # Descompila JAR
make chunks    # Extrae chunks
make db        # Construye DB
```

### Ejecutar Chat
```bash
python modia-chat.py
```

### Limpiar
```bash
make clean  # Elimina venv y hytale_src
```

---

## 📝 Convenciones del Código

- **Español**: Comentarios y mensajes en español
- **Tipo hints**: Uso de `typing` para tipos (List, Dict)
- **Funciones puras**: `should_store()`, `format_memory()`, `is_explain_mode()`, `normalize_llm_output()`
- **Variables globales**: `memory`, `embeddings`, `db`, `llm` (configuración compartida)

---

## 🔍 Puntos de Extensión Futuros

1. **CLI mejorado**: Usar `click` o `typer` para comandos estructurados
2. **Persistencia**: Guardar memoria en JSON/Pickle en disco
3. **Configuración**: Archivo de config (modelos, paths, parámetros)
4. **Múltiples DBs**: Soporte para diferentes versiones de HytaleServer
5. **Streaming**: Respuestas en tiempo real del LLM
6. **Logging**: Sistema de logs para debugging

---

*Última actualización: Basado en análisis del código actual (2024)*


