"""Operaciones con ChromaDB"""

from typing import List, Dict, Optional, Any
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_core.documents import Document
from backend.config import DEFAULT_EMBEDDING_MODEL, DEFAULT_TOP_K


class ModiaDB:
    """Clase para operaciones con ChromaDB"""
    
    def __init__(self, db_path: str, embedding_model: str = DEFAULT_EMBEDDING_MODEL):
        self.db_path = db_path
        self.embeddings = OllamaEmbeddings(model=embedding_model)
        self.db = Chroma(
            persist_directory=db_path,
            embedding_function=self.embeddings
        )
    
    def search(
        self,
        query: str,
        k: int = DEFAULT_TOP_K,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """Búsqueda semántica en la base de datos"""
        return self.db.similarity_search(query, k=k, filter=filter)
    
    def search_with_scores(
        self,
        query: str,
        k: int = DEFAULT_TOP_K,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[tuple]:
        """Búsqueda semántica con scores de similitud"""
        return self.db.similarity_search_with_score(query, k=k, filter=filter)
    
    def add_documents(
        self,
        documents: List[Document],
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """Agrega documentos a la base de datos"""
        return self.db.add_documents(documents, ids=ids)
    
    def add_texts(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """Agrega textos a la base de datos"""
        return self.db.add_texts(texts, metadatas=metadatas, ids=ids)
    
    def delete(self, ids: Optional[List[str]] = None):
        """Elimina documentos por IDs"""
        if ids:
            self.db.delete(ids=ids)
        else:
            # Eliminar todos (cuidado!)
            collection = self.db._collection
            all_ids = collection.get()["ids"]
            if all_ids:
                self.db.delete(ids=all_ids)
    
    def get_all(self, limit: Optional[int] = None) -> List[Document]:
        """Obtiene todos los documentos (o hasta un límite)"""
        collection = self.db._collection
        results = collection.get(limit=limit)
        
        documents = []
        if results and "ids" in results:
            for i, doc_id in enumerate(results["ids"]):
                content = results["documents"][i] if "documents" in results else ""
                metadata = results["metadatas"][i] if "metadatas" in results else {}
                documents.append(Document(page_content=content, metadata=metadata))
        
        return documents
    
    def count(self) -> int:
        """Cuenta el número de documentos en la base de datos"""
        collection = self.db._collection
        results = collection.get()
        return len(results["ids"]) if results and "ids" in results else 0
    
    def stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de la base de datos"""
        collection = self.db._collection
        results = collection.get()
        
        total = len(results["ids"]) if results and "ids" in results else 0
        
        # Contar por metadata si existe
        metadata_counts = {}
        if results and "metadatas" in results:
            for metadata in results["metadatas"]:
                if metadata:
                    for key, value in metadata.items():
                        if key not in metadata_counts:
                            metadata_counts[key] = {}
                        if value not in metadata_counts[key]:
                            metadata_counts[key][value] = 0
                        metadata_counts[key][value] += 1
        
        return {
            "total_documents": total,
            "db_path": self.db_path,
            "embedding_model": self.embeddings.model,
            "metadata_counts": metadata_counts
        }
    
    def persist(self):
        """Persiste los cambios en disco"""
        self.db.persist()

