"""Gestor de configuración persistente para Modia"""

import json
import os
from pathlib import Path
from typing import Optional, Dict, List
from getpass import getpass


class ConfigManager:
    """Gestor de configuración persistente"""
    
    def __init__(self, config_file: Optional[str] = None):
        if config_file is None:
            # Usar directorio home del usuario
            config_dir = Path.home() / ".modia"
            config_dir.mkdir(exist_ok=True)
            config_file = str(config_dir / "config.json")
        
        self.config_file = Path(config_file)
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        self._config = self._load_config()
    
    def _load_config(self) -> Dict:
        """Carga la configuración desde el archivo"""
        if not self.config_file.exists():
            return {
                "default_provider": "ollama",
                "api_keys": {},
                "provider_configs": {}
            }
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {
                "default_provider": "ollama",
                "api_keys": {},
                "provider_configs": {}
            }
    
    def _save_config(self):
        """Guarda la configuración en el archivo"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
        except IOError as e:
            raise RuntimeError(f"Error al guardar configuración: {e}")
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """Obtiene la API key de un proveedor"""
        return self._config.get("api_keys", {}).get(provider.lower())
    
    def set_api_key(self, provider: str, api_key: str):
        """Establece la API key de un proveedor"""
        if "api_keys" not in self._config:
            self._config["api_keys"] = {}
        self._config["api_keys"][provider.lower()] = api_key
        self._save_config()
    
    def remove_api_key(self, provider: str):
        """Elimina la API key de un proveedor"""
        if "api_keys" in self._config:
            self._config["api_keys"].pop(provider.lower(), None)
            self._save_config()
    
    def get_provider_config(self, provider: str) -> Dict:
        """Obtiene la configuración adicional de un proveedor"""
        return self._config.get("provider_configs", {}).get(provider.lower(), {})
    
    def set_provider_config(self, provider: str, config: Dict):
        """Establece la configuración adicional de un proveedor"""
        if "provider_configs" not in self._config:
            self._config["provider_configs"] = {}
        self._config["provider_configs"][provider.lower()] = config
        self._save_config()
    
    def get_default_provider(self) -> str:
        """Obtiene el proveedor por defecto"""
        return self._config.get("default_provider", "ollama")
    
    def set_default_provider(self, provider: str):
        """Establece el proveedor por defecto"""
        self._config["default_provider"] = provider.lower()
        self._save_config()
    
    def list_configured_providers(self) -> List[str]:
        """Lista los proveedores configurados (con API keys)"""
        return list(self._config.get("api_keys", {}).keys())

