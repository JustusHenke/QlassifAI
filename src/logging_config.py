"""Logging-Konfiguration für Qlassif-AI"""

import logging
from pathlib import Path


def setup_logging(log_file: str = "qlassif-ai.log", level: int = logging.INFO,
                  console_level: int = logging.WARNING) -> logging.Logger:
    """
    Richtet Logging für die Anwendung ein.
    
    Args:
        log_file: Pfad zur Log-Datei
        level: Logging-Level fuer die Log-Datei (default: INFO)
        console_level: Logging-Level fuer die Konsole (default: WARNING),
            damit Fortschrittsanzeigen nicht durch INFO-Logs ueberlagert werden
        
    Returns:
        Konfigurierter Logger
    """
    logger = logging.getLogger("qlassif-ai")
    logger.setLevel(level)
    
    # Verhindere doppelte Handler
    if logger.handlers:
        return logger
    
    # Format: [TIMESTAMP] [LEVEL] [MODULE] Message
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
    )
    
    # Console Handler - nur Warnungen und Fehler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(console_level)
    logger.addHandler(console_handler)
    
    # File Handler - vollstaendiges Log
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Holt einen Logger für ein spezifisches Modul.
    
    Args:
        name: Name des Moduls
        
    Returns:
        Logger-Instanz
    """
    return logging.getLogger(f"qlassif-ai.{name}")
