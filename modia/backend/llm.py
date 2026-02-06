"""Proveedores de LLM externos (OpenAI, Gemini, DeepSeek, etc.)"""

from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.callbacks import CallbackManagerForLLMRun


class LLMProvider(ABC):
    """Clase base para proveedores de LLM"""
    
    @abstractmethod
    def get_llm(self, model: Optional[str] = None, temperature: float = 0.1) -> BaseChatModel:
        """Crea una instancia del LLM"""
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """Retorna lista de modelos disponibles"""
        pass


class OllamaProvider(LLMProvider):
    """Proveedor para Ollama (local)"""
    
    def get_llm(self, model: Optional[str] = None, temperature: float = 0.1) -> BaseChatModel:
        """Crea instancia de Ollama LLM"""
        from langchain_ollama import ChatOllama
        
        return ChatOllama(
            model=model or "llama3.1:8b",
            temperature=temperature
        )
    
    def get_available_models(self) -> List[str]:
        """Retorna modelos de Ollama disponibles"""
        # Por defecto, los modelos comunes de Ollama
        return [
            "llama3.1:8b",
            "llama3.1:70b",
            "mistral",
            "codellama",
            "phi"
        ]


class OpenAIProvider(LLMProvider):
    """Proveedor para OpenAI (ChatGPT)"""
    
    def __init__(self, api_key: str, base_url: Optional[str] = None):
        self.api_key = api_key
        self.base_url = base_url  # Para usar con proxies o servicios compatibles
    
    def get_llm(self, model: Optional[str] = None, temperature: float = 0.1) -> BaseChatModel:
        """Crea instancia de OpenAI LLM"""
        from langchain_openai import ChatOpenAI
        
        kwargs = {
            "model": model or "gpt-4o-mini",
            "temperature": temperature,
            "api_key": self.api_key
        }
        
        if self.base_url:
            kwargs["base_url"] = self.base_url
        
        return ChatOpenAI(**kwargs)
    
    def get_available_models(self) -> List[str]:
        """Retorna modelos de OpenAI disponibles"""
        return [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo"
        ]


class DeepSeekProvider(LLMProvider):
    """Proveedor para DeepSeek (compatible con OpenAI API)"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.deepseek.com/v1"
    
    def get_llm(self, model: Optional[str] = None, temperature: float = 0.1) -> BaseChatModel:
        """Crea instancia de DeepSeek LLM"""
        from langchain_openai import ChatOpenAI
        
        return ChatOpenAI(
            model=model or "deepseek-chat",
            temperature=temperature,
            api_key=self.api_key,
            base_url=self.base_url
        )
    
    def get_available_models(self) -> List[str]:
        """Retorna modelos de DeepSeek disponibles"""
        return [
            "deepseek-chat",
            "deepseek-coder"
        ]


class GeminiProvider(LLMProvider):
    """Proveedor para Google Gemini"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def get_llm(self, model: Optional[str] = None, temperature: float = 0.1) -> BaseChatModel:
        """Crea instancia de Gemini LLM"""
        from langchain_google_genai import ChatGoogleGenerativeAI
        
        return ChatGoogleGenerativeAI(
            model=model or "gemini-pro",
            temperature=temperature,
            google_api_key=self.api_key
        )
    
    def get_available_models(self) -> List[str]:
        """Retorna modelos de Gemini disponibles"""
        return [
            "gemini-pro",
            "gemini-pro-vision",
            "gemini-1.5-pro",
            "gemini-1.5-flash"
        ]


class AnthropicProvider(LLMProvider):
    """Proveedor para Anthropic (Claude)"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def get_llm(self, model: Optional[str] = None, temperature: float = 0.1) -> BaseChatModel:
        """Crea instancia de Anthropic LLM"""
        from langchain_anthropic import ChatAnthropic
        
        return ChatAnthropic(
            model=model or "claude-3-5-sonnet-20241022",
            temperature=temperature,
            api_key=self.api_key
        )
    
    def get_available_models(self) -> List[str]:
        """Retorna modelos de Anthropic disponibles"""
        return [
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229"
        ]


class LLMProviderManager:
    """Gestor de proveedores de LLM"""
    
    def __init__(self):
        self.providers: Dict[str, LLMProvider] = {}
        self.default_provider = "ollama"
        
        # Inicializar Ollama por defecto (no requiere API key)
        self.providers["ollama"] = OllamaProvider()
    
    def register(self, name: str, provider: LLMProvider):
        """Registra un proveedor"""
        self.providers[name] = provider
    
    def get(self, name: Optional[str] = None) -> LLMProvider:
        """Obtiene un proveedor por nombre"""
        provider_name = name or self.default_provider
        if provider_name not in self.providers:
            raise ValueError(f"Proveedor '{provider_name}' no encontrado. Usa 'modia llm list' para ver proveedores disponibles.")
        return self.providers[provider_name]
    
    def set_default(self, name: str):
        """Establece el proveedor por defecto"""
        if name not in self.providers:
            raise ValueError(f"Proveedor '{name}' no encontrado")
        self.default_provider = name
    
    def list_providers(self) -> List[str]:
        """Lista todos los proveedores registrados"""
        return list(self.providers.keys())
    
    def get_llm(
        self,
        provider_name: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.1
    ) -> BaseChatModel:
        """Obtiene una instancia de LLM del proveedor especificado"""
        provider = self.get(provider_name)
        return provider.get_llm(model=model, temperature=temperature)
    
    def configure_openai(self, api_key: str, base_url: Optional[str] = None):
        """Configura el proveedor de OpenAI"""
        self.providers["openai"] = OpenAIProvider(api_key, base_url)
    
    def configure_deepseek(self, api_key: str):
        """Configura el proveedor de DeepSeek"""
        self.providers["deepseek"] = DeepSeekProvider(api_key)
    
    def configure_gemini(self, api_key: str):
        """Configura el proveedor de Gemini"""
        self.providers["gemini"] = GeminiProvider(api_key)
    
    def configure_anthropic(self, api_key: str):
        """Configura el proveedor de Anthropic"""
        self.providers["anthropic"] = AnthropicProvider(api_key)

