"""Configuración compartida para Modia"""

import os
from pathlib import Path
from typing import Optional

# Configuración por defecto
DEFAULT_DB_PATH = "./hytale_db"
DEFAULT_LLM_MODEL = "llama3.1:8b"
DEFAULT_EMBEDDING_MODEL = "nomic-embed-text"
DEFAULT_TEMPERATURE = 0.1
DEFAULT_MAX_MEMORY = 6
DEFAULT_TOP_K = 5

# Keywords para almacenamiento selectivo en memoria
MEMORY_KEYWORDS = [
    "entity", "entidad", "trigger", "evento", "api", "event",
    "server", "engine", "lifecycle", "mod", "hook"
]

# Keywords para modo explicación
EXPLAIN_TRIGGERS = [
    "explicame", "explica", "no entiendo", "qué hace", "que hace",
    "para qué sirve", "como funciona", "cómo funciona",
    "ayudame a entender", "ayuda con este método", "ayuda con esta clase",
    "explain", "explain to me", "I don't understand", "what does this do",
    "what does it do", "what is this for", "what is the purpose",
    "how does it work", "how does this work", "help me understand",
    "help with this method", "help with this class"
]

SYSTEM_PROMPT = """
You are an expert assistant on the HytaleServer internal codebase. Your name is Modia. You act as a technical co-pilot for mod development.

ABSOLUTE RULES:
Respond ONLY with the final output for the user.
DO NOT reveal history, context, or internal reasoning.
DO NOT repeat or describe the provided context.
DO NOT use titles, sections, or headers.
DO NOT explain what information is available to you.
DO NOT use qualifiers like "according to the context" or similar phrases.

BEHAVIOR:
Provide an answer even if the information is partial.
If specific details are not explicit, infer them using common game engine patterns.
If a feature does not exist, state it clearly and explain the actual technical alternative.
Use technical, direct, and concise language.
Maintain a modding-oriented focus.
EXPLANATION MODE: If the user asks to explain or understand a concept, respond with greater detail, but ALWAYS without revealing context, history, or internal structure.
"""

EXPLAIN_MODE_PROMPT = """
ACTIVE EXPLANATION MODE:

Explain the purpose of the code.
Indicate when it is executed.
Explain interactions with other systems.
Clarify its relevance to mod development.
"""


class ModiaConfig:
    """Configuración de Modia"""
    
    def __init__(
        self,
        db_path: str = DEFAULT_DB_PATH,
        llm_model: str = DEFAULT_LLM_MODEL,
        embedding_model: str = DEFAULT_EMBEDDING_MODEL,
        temperature: float = DEFAULT_TEMPERATURE,
        max_memory: int = DEFAULT_MAX_MEMORY,
        top_k: int = DEFAULT_TOP_K
    ):
        self.db_path = Path(db_path)
        self.llm_model = llm_model
        self.embedding_model = embedding_model
        self.temperature = temperature
        self.max_memory = max_memory
        self.top_k = top_k
    
    
    def validate(self) -> bool:
        """Valida que la configuración sea correcta"""
        if not self.db_path.exists():
            return False
        return True
    
    @classmethod
    def from_env(cls) -> "ModiaConfig":
        """Crea configuración desde variables de entorno"""
        return cls(
            db_path=os.getenv("MODIA_DB_PATH", DEFAULT_DB_PATH),
            llm_model=os.getenv("MODIA_LLM_MODEL", DEFAULT_LLM_MODEL),
            embedding_model=os.getenv("MODIA_EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL),
            temperature=float(os.getenv("MODIA_TEMPERATURE", str(DEFAULT_TEMPERATURE))),
            max_memory=int(os.getenv("MODIA_MAX_MEMORY", str(DEFAULT_MAX_MEMORY))),
            top_k=int(os.getenv("MODIA_TOP_K", str(DEFAULT_TOP_K)))
        )

