"""Clase ModiaChat para manejar conversaciones con Modia"""

from typing import List, Dict, Optional
from langchain_chroma import Chroma
from langchain_core.language_models import BaseChatModel
from langchain_core.documents import Document
from backend.config import (
    SYSTEM_PROMPT, EXPLAIN_MODE_PROMPT, 
    MEMORY_KEYWORDS, EXPLAIN_TRIGGERS,
    DEFAULT_TOP_K
)


def should_store(text: str) -> bool:
    """Determina si un texto debe almacenarse en memoria"""
    if not text or len(text) < 40:
        return False
    t = text.lower()
    return any(k in t for k in MEMORY_KEYWORDS)


def format_memory(mem: List[Dict[str, str]]) -> str:
    """Formatea la memoria para incluir en el prompt"""
    if not mem:
        return ""
    return "\n".join(
        f"{m['role'].upper()}: {m['content']}"
        for m in mem
    )


def is_explain_mode(question: str) -> bool:
    """Detecta si la pregunta requiere modo explicación"""
    q = question.lower()
    return any(t in q for t in EXPLAIN_TRIGGERS)


def normalize_llm_output(resp) -> str:
    """Normaliza la respuesta del LLM a string"""
    content = resp.content
    
    if isinstance(content, str):
        return content.strip()
    
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and "text" in item:
                parts.append(str(item["text"]))
        return "\n".join(parts).strip()
    
    return str(content).strip()


class ModiaChat:
    """Clase para manejar conversaciones con Modia"""
    
    def __init__(self, db: Chroma, llm: BaseChatModel, max_memory: int = 6):
        self.db = db
        self.llm = llm
        self.max_memory = max_memory
        self.memory: List[Dict[str, str]] = []
    
    def ask(
        self, 
        question: str, 
        top_k: int = DEFAULT_TOP_K,
        explain_mode: Optional[bool] = None
    ) -> str:
        """Hace una pregunta a Modia"""
        # Detectar modo explicación si no se especifica
        if explain_mode is None:
            explain_mode = is_explain_mode(question)
        
        # Búsqueda semántica
        docs = self.db.similarity_search(question, k=top_k)
        context = "\n\n".join(d.page_content for d in docs)
        
        # Formatear memoria
        memory_block = format_memory(self.memory)
        
        # Construir prompt base
        system_prompt = SYSTEM_PROMPT
        if explain_mode:
            system_prompt += "\n\n" + EXPLAIN_MODE_PROMPT
        
        prompt = f"""{system_prompt}

--- RECENT HISTORY ---
{memory_block}

--- TECHNICAL CONTEXT ---
{context}

--- QUESTION ---
{question}
"""
        
        # Invocar LLM
        response = self.llm.invoke(prompt)
        answer = normalize_llm_output(response)
        
        # Almacenar en memoria si es relevante
        if should_store(question):
            self.memory.append({"role": "user", "content": question})
        
        if should_store(answer):
            self.memory.append({"role": "assistant", "content": answer})
        
        # Limitar memoria
        self.memory = self.memory[-self.max_memory:]
        
        # Resumir si se alcanza el límite
        if len(self.memory) >= self.max_memory:
            self._summarize_memory()
        
        return answer
    
    def _summarize_memory(self):
        """Genera un resumen de la memoria cuando se alcanza el límite"""
        summary_prompt = f"""
Generate a 5-point technical summary of the current history, 
strictly related to Hytale Server and modding. 
{format_memory(self.memory)}
"""
        summary_resp = self.llm.invoke(summary_prompt)
        summary_text = normalize_llm_output(summary_resp)
        
        self.memory = [{
            "role": "system",
            "content": summary_text
        }]
    
    def clear_memory(self):
        """Limpia la memoria conversacional"""
        self.memory = []
    
    def get_memory(self) -> List[Dict[str, str]]:
        """Obtiene la memoria actual"""
        return self.memory.copy()

