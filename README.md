# 🧠 Modia – Hytale Modding Copilot

> **⚠️ Warning: Early Access**    
> The game Hytale is in early access, and so is this project! Features may be
> incomplete, unstable, or change frequently. Please be patient and understanding as development
> continues.

Modia es un **copiloto técnico local** para desarrollo de plugins de **Hytale**, basado en **RAG (Retrieval-Augmented Generation)**, memoria conversacional explícita.

Está pensado para responder **rápido, directo y con criterio técnico**, sin tener que releer el código del server una y otra vez y asi impulsar el coding de **plugins** para **Hytale**.

---

## Características (Consola mode)
 
*  **RAG sobre el código de HytaleServer** (indexado desde `.jar`) y **Repositorios añadibles**
*  **Memoria conversacional ligera** (contexto entre preguntas)
*  **Modo explicación natural** 
*  **100% controlable y local**

---

##  Stack

* **Python 3.10+**
* **Ollama** (LLM + embeddings)
* **LangChain**
* **ChromaDB**
* **FastAPI**
* **TailwindCSS**
* ****

Modelos recomendados:

* LLM: `llama3.1:8b`
* Embeddings: `nomic-embed-text`

---

## **PROXIMAMENTE**

Instalacion (App mode) 

Descargar la ultima version de Release y instalar!

---

## Instalación (Consola Mode)

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

1 - Colocar el HytaleServer.jar en la carpeta Server

2 - Descompilar el HytaleServer.jar con:

```bash
make descompile
```
3 - Extraer chunks con:

```bash
make chunks
```

4 - Crear la base vectorial con:

```bash
make db
```


---

**En Windows:**

```powershell
./build.ps1
```

## Uso

**(Linux & Mac OS):**

```bash
python modia-chat.py
```

**(Windows):**

```bash
python ./modia-chat.py
```


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

## Roadmap


* [ ] Convertir el chat en Web App
* [ ] Agregar modos utiles como **Explain** y **Raw**
* [ ] Persistencia de memoria en disco
* [ ] Permitir usar API externas como ChatGPT, Claude, DeepSeek, etc
* [ ] Agregar tools y CRUD a la IA
* [ ] Perfiles por proyecto
* [ ] Empaquetado como binario

---

## Disclaimer

Este proyecto es **no oficial** y no está afiliado con Hypixel Studios.

Uso educativo y de desarrollo.

---

