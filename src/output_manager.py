"""Output Manager fuer strukturierte Ausgabeverzeichnisse"""

from pathlib import Path
from datetime import datetime
from typing import Optional
from logging_config import get_logger

logger = get_logger("output_manager")


class OutputManager:
    """
    Verwaltet die Ausgabestruktur fuer Qlassif-AI Analysen.
    
    Erstellt ein flaches Verzeichnis:
    {BasisVerzeichnis}/{InputDateiName}_analyzed/
    """
    
    def __init__(self, base_dir: Path, input_name: str, timestamp: Optional[str] = None):
        """
        Initialisiert OutputManager.
        
        Args:
            base_dir: Basis-Verzeichnis (z.B. Input-Ordner)
            input_name: Name der Eingabedatei (ohne Endung)
            timestamp: Optionaler Zeitstempel fuer Verzeichnisname
        """
        self.base_dir = Path(base_dir)
        self.input_name = input_name
        self.timestamp = timestamp or datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Flaches Ausgabeverzeichnis: {input_name}_analyzed
        self.output_dir = self.base_dir / f"{input_name}_analyzed"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Output-Verzeichnis erstellt: {self.output_dir}")
    
    def get_analyzed_path(self) -> Path:
        """Gibt Pfad fuer die Ergebnis-Excel-Datei zurueck (alle Sheets in einer Datei)"""
        return self.output_dir / f"{self.input_name}_analyzed_{self.timestamp}.xlsx"
    
    def get_methodology_path(self) -> Path:
        """Gibt Pfad fuer methodology.md zurueck"""
        return self.output_dir / "methodology.md"
    
    def get_codebook_path(self) -> Path:
        """Gibt Pfad fuer codebook.json zurueck"""
        return self.output_dir / "codebook.json"
    
    def get_frequency_tables_path(self) -> Path:
        """Gibt Pfad fuer frequency_tables.csv zurueck"""
        return self.output_dir / "frequency_tables.csv"
    
    def get_audit_trail_path(self) -> Path:
        """Gibt Pfad fuer Audit Trail zurueck"""
        return self.output_dir / f"audit_trail_{self.timestamp}.json"
