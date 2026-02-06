# 🧠 Modia – Hytale Modding Copilot

> **⚠️ Warning: Early Access**    
> The game Hytale is in early access, and so is this project! Features may be
> incomplete, unstable, or change frequently. Please be patient and understanding as development
> continues.

Modia es un **copiloto técnico local** para desarrollo de plugins de **Hytale**, basado en **RAG (Retrieval-Augmented Generation)**, memoria conversacional explícita.

Está pensado para responder **rápido, directo y con criterio técnico**, sin tener que releer el código del server una y otra vez y asi impulsar el coding de **plugins** para **Hytale**.

---

## Características

### App Mode (Web)
*  **Interfaz web moderna** con TailwindCSS
*  **API REST completa** para integración
*  **Gestión de proveedores LLM** (Ollama, OpenAI, DeepSeek, Gemini, Anthropic)
*  **Gestión de repositorios Git** (clonar y sincronizar repos)
*  **Rebuild de base de datos** desde la UI
*  **Configuración persistente** de API keys y proveedores

### Consola Mode
*  **RAG sobre el código de HytaleServer** (indexado desde `.jar`) y **Repositorios añadibles**
*  **Memoria conversacional ligera** (contexto entre preguntas)
*  **Modo explicación natural** 
*  **100% controlable y local**

---

##  Stack

* **Python 3.10+**
* **Ollama** (LLM + embeddings local)
* **LangChain** (orquestación)
* **ChromaDB** (base de datos vectorial)
* **FastAPI** (API REST)
* **TailwindCSS** (UI)
* **PyWebView** (App Mode desktop)

### Proveedores de LLM soportados

* **Ollama** (local, por defecto)
* **OpenAI** (ChatGPT, GPT-4, etc.)
* **DeepSeek** (DeepSeek Chat, Coder)
* **Google Gemini** (Gemini Pro, Gemini 1.5)
* **Anthropic** (Claude 3.5 Sonnet, Haiku, Opus)

### Modelos recomendados (Ollama)

* LLM: `llama3.1:8b`
* Embeddings: `nomic-embed-text`

---

## Instalación

### App Mode (Web)

Ir a RELEASES y descargar la utima version, instalar y finalmente ejecutar!

### Consola Mode

```bash
make install
```

Asegurate de tener **Ollama corriendo** y los modelos descargados:

```bash
ollama pull llama3.1:8b
ollama pull nomic-embed-text
```

---

## Indexación del código (previo)

Antes de usar Modia necesitás:

1. Colocar el `HytaleServer.jar` en la carpeta `server/`

2. Descompilar el `HytaleServer.jar` con:

```bash
make decompile
```

3. Extraer chunks con:

```bash
make chunks
```

4. Crear la base vectorial con:

```bash
make db
```

**En Windows:**

```powershell
./build.ps1
```

**Nota:** También puedes usar la UI de App Mode para reconstruir la base de datos desde `/api/db/rebuild`.

---

## Uso

### App Mode

Ejecutar la aplicación web:

```bash
python modia/launcher.py
```

O iniciar solo el servidor API:

```bash
cd modia
python -m uvicorn backend.app:app --host 0.0.0.0 --port 7860
```

Luego acceder a `http://localhost:7860` en el navegador.

### Consola Mode

**Linux & Mac OS:**

```bash
python modia-chat.py
```

**Windows:**

```bash
python ./modia-chat.py
```

---

## Gestión de Repositorios

Modia permite agregar repositorios Git adicionales para indexar su código junto con HytaleServer.

### Desde la UI (App Mode)

1. Ir a la sección de Repositorios
2. Agregar URLs de repositorios Git
3. Sincronizar repositorios (clonar/actualizar)
4. Reconstruir la base de datos para incluir el nuevo código

### Desde archivo

Editar `repository/repos.txt` y agregar una URL por línea:

```
https://github.com/usuario/repo1.git
https://github.com/usuario/repo2.git
```

Luego ejecutar:

```bash
python utils/cloneRepos.py
python utils/extractChunks.py
python utils/buildDB.py
```

---

## Configuración de Proveedores LLM

### App Mode

Desde la UI puedes configurar proveedores externos:

1. Ir a Configuración
2. Seleccionar un proveedor (OpenAI, DeepSeek, Gemini, Anthropic)
3. Ingresar tu API key
4. Establecer como proveedor por defecto si lo deseas

### Consola Mode / API

Las API keys se guardan en `~/.modia/config.json` (configuración persistente).

Para configurar desde la API:

```bash
curl -X POST http://localhost:7860/api/llm/configure \
  -H "Content-Type: application/json" \
  -d '{"provider": "openai", "api_key": "tu-api-key"}'
```

---

## Memoria conversacional

Modia **no depende de memoria implícita del modelo**.

En su lugar:

* Guarda solo mensajes técnicos relevantes
* Limita el tamaño
* Resume automáticamente cuando se llena

Esto permite conversaciones largas **sin perder coherencia ni explotar tokens**.

---

## Modo explicación (natural)

No hay `/explain`.

Si escribís:

* "explicá"
* "cómo funciona"
* "no entiendo este método"

Modia entra automáticamente en **modo explicación**, sin mostrar contexto ni razonamiento interno.

---

## API REST

Modia expone una API REST completa para integración:

### Endpoints principales

- `POST /api/ask` - Hacer una pregunta
- `GET /api/memory` - Obtener memoria conversacional
- `DELETE /api/memory` - Limpiar memoria
- `GET /api/db/search` - Búsqueda semántica
- `POST /api/db/rebuild` - Reconstruir base de datos
- `GET /api/llm/providers` - Listar proveedores LLM
- `POST /api/llm/configure` - Configurar proveedor LLM
- `GET /api/repos` - Listar repositorios
- `POST /api/repos` - Agregar repositorio
- `POST /api/repos/sync` - Sincronizar repositorios

Ver `modia/backend/app.py` para la documentación completa de la API.

---

## Roadmap

* [x] Convertir el chat en Web App
* [x] Agregar modos útiles como **Explain** (modo explicación natural)
* [x] Permitir usar API externas como ChatGPT, Claude, DeepSeek, etc
* [x] Gestión de repositorios Git
* [ ] Persistencia de memoria en disco
* [ ] Agregar tools y CRUD a la IA
* [ ] Perfiles por proyecto
* [ ] Empaquetado como binario

---

## Disclaimer

Este proyecto es **no oficial** y no está afiliado con Hypixel Studios.

Uso educativo y de desarrollo.

---

