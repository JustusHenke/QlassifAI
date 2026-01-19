"""Environment Manager für API-Key-Verwaltung"""

import os
from pathlib import Path
from typing import Optional, List
from dotenv import load_dotenv
from logging_config import get_logger

logger = get_logger("environment_manager")


class MissingAPIKeyError(Exception):
    """Fehler wenn kein API-Key gefunden wird"""
    pass


class EnvironmentManager:
    """Verwaltet Umgebungsvariablen und API-Keys"""
    
    def __init__(self):
        """Initialisiert den EnvironmentManager"""
        self._api_key: Optional[str] = None
        self._env_file_path: Optional[Path] = None
    
    def load_env_file(self, search_paths: Optional[List[Path]] = None) -> Optional[Path]:
        """
        Sucht und lädt .env-Datei aus mehreren möglichen Pfaden.
        WICHTIG: override=False stellt sicher, dass System-Umgebungsvariablen Vorrang haben.
        
        Args:
            search_paths: Liste von Pfaden zum Durchsuchen. 
                         Falls None, werden Standard-Pfade verwendet.
        
        Returns:
            Pfad zur gefundenen .env-Datei oder None
        """
        if search_paths is None:
            # Standard-Suchpfade
            search_paths = [
                Path.cwd() / ".env",  # Aktuelles Verzeichnis
                Path.home() / ".env",  # Home-Verzeichnis
                Path.cwd().parent / ".env",  # Parent-Verzeichnis
            ]
        
        for path in search_paths:
            if path.exists() and path.is_file():
                logger.info(f".env-Datei gefunden: {path}")
                # override=False: System-Umgebungsvariablen haben Vorrang
                load_dotenv(path, override=False)
                self._env_file_path = path
                return path
        
        logger.warning("Keine .env-Datei gefunden.")
        return None
    
    def get_api_key(self, provider: str = "openai") -> str:
        """
        Holt API-Key aus Umgebungsvariablen basierend auf Provider.
        Prüft zuerst System-Umgebungsvariablen, dann .env-Datei.
        
        Args:
            provider: "openai" oder "openrouter"
        
        Returns:
            API-Key als String
            
        Raises:
            MissingAPIKeyError: Wenn kein API-Key gefunden wird
        """
        # Bestimme Umgebungsvariablen-Namen
        if provider == "openrouter":
            env_var_name = "OPENROUTER_API_KEY"
        else:
            env_var_name = "OPENAI_API_KEY"
        
        # Prüfe zuerst System-Umgebungsvariablen (Windows, Linux, Mac)
        api_key = os.environ.get(env_var_name)
        
        if api_key:
            logger.info(f"{env_var_name} aus System-Umgebungsvariablen geladen")
        else:
            # Falls nicht in System-Umgebungsvariablen, versuche .env-Datei
            logger.info(f"{env_var_name} nicht in System-Umgebungsvariablen gefunden, versuche .env-Datei")
            self.load_env_file()
            api_key = os.getenv(env_var_name)
            
            if api_key:
                logger.info(f"{env_var_name} aus .env-Datei geladen")
        
        if not api_key:
            error_msg = (
                f"{env_var_name} nicht gefunden!\n"
                f"Bitte setzen Sie die Umgebungsvariable oder erstellen Sie eine .env-Datei "
                f"mit dem Inhalt: {env_var_name}=your-api-key-here"
            )
            logger.error(error_msg)
            raise MissingAPIKeyError(error_msg)
        
        # Validiere API-Key
        if not self.validate_api_key(api_key, provider):
            error_msg = f"API-Key für {provider} hat ungültiges Format"
            logger.error(error_msg)
            raise MissingAPIKeyError(error_msg)
        
        self._api_key = api_key
        logger.info(f"API-Key für {provider} erfolgreich geladen")
        
        # Zeige Pfad zur .env-Datei an, falls vorhanden
        if self._env_file_path:
            logger.info(f"API-Key geladen aus: {self._env_file_path}")
        
        return api_key
    
    def validate_api_key(self, api_key: str, provider: str = "openai") -> bool:
        """
        Validiert das Format des API-Keys.
        
        Args:
            api_key: Zu validierender API-Key
            provider: "openai" oder "openrouter"
            
        Returns:
            True wenn Format gültig, sonst False
        """
        if not api_key:
            return False
        
        # Entferne Whitespace
        api_key = api_key.strip()
        
        if provider == "openrouter":
            # OpenRouter API-Keys haben eigenes Format
            if len(api_key) < 20:
                logger.warning("OpenRouter API-Key ist zu kurz")
                return False
        else:
            # OpenAI API-Keys beginnen typischerweise mit "sk-"
            if not api_key.startswith("sk-"):
                logger.warning("OpenAI API-Key beginnt nicht mit 'sk-'")
                return False
            
            if len(api_key) < 20:
                logger.warning("OpenAI API-Key ist zu kurz")
                return False
        
        return True
    
    @property
    def api_key(self) -> Optional[str]:
        """Gibt den geladenen API-Key zurück"""
        return self._api_key
    
    @property
    def env_file_path(self) -> Optional[Path]:
        """Gibt den Pfad zur geladenen .env-Datei zurück"""
        return self._env_file_path
