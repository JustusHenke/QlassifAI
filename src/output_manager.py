"""Output Manager für strukturierte Ausgabeverzeichnisse"""

from pathlib import Path
from datetime import datetime
from typing import Optional, Dict
from logging_config import get_logger

logger = get_logger("output_manager")


class OutputManager:
    """
    Verwaltet die Ausgabestruktur für Qlassif-AI Analysen.
    
    Erstellt:
    - {output_dir}/                      → Hauptausgabe
    - {output_dir}/analyzed/             → Analysedateien (Excel)
    - {output_dir}/reproducibility/      → Methodenprotokoll, Codebook, CSV
    - {output_dir}/audit_trail/          → Audit Trail JSONs
    - {output_dir}/intercoder/           → Intercoder-Vergleich (nur bei multi_coder)
    """
    
    def __init__(self, base_dir: Path, timestamp: Optional[str] = None):
        """
        Initialisiert OutputManager.
        
        Args:
            base_dir: Basis-Verzeichnis (z.B. Input-Ordner)
            timestamp: Optionaler Zeitstempel für Verzeichnisname
        """
        self.base_dir = Path(base_dir)
        self.timestamp = timestamp or datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Verzeichnisse erstellen
        self.dirs = self._create_directories()
    
    def _create_directories(self) -> Dict[str, Path]:
        """Erstellt die Ausgabeverzeichnisse"""
        dirs = {}
        
        dirs["analyzed"] = self.base_dir / "analyzed"
        dirs["reproducibility"] = self.base_dir / "reproducibility"
        dirs["audit_trail"] = self.base_dir / "audit_trail"
        dirs["intercoder"] = self.base_dir / "intercoder"
        
        for key, path in dirs.items():
            path.mkdir(parents=True, exist_ok=True)
        
        return dirs
    
    def get_analyzed_path(self, filename: str, suffix: str = "analyzed") -> Path:
        """Gibt Pfad für Analysedatei zurück"""
        return self.dirs["analyzed"] / f"{filename}_{suffix}_{self.timestamp}.xlsx"
    
    def get_intercoder_path(self, filename: str) -> Path:
        """Gibt Pfad für Intercoder-Datei zurück"""
        return self.dirs["intercoder"] / f"{filename}_intercoder_{self.timestamp}.xlsx"
    
    def get_methodology_path(self) -> Path:
        """Gibt Pfad für methodology.md zurück"""
        return self.dirs["reproducibility"] / "methodology.md"
    
    def get_codebook_path(self) -> Path:
        """Gibt Pfad für codebook.json zurück"""
        return self.dirs["reproducibility"] / "codebook.json"
    
    def get_frequency_tables_path(self) -> Path:
        """Gibt Pfad für frequency_tables.csv zurück"""
        return self.dirs["reproducibility"] / "frequency_tables.csv"
    
    def get_audit_trail_path(self) -> Path:
        """Gibt Pfad für Audit Trail zurück"""
        return self.dirs["audit_trail"] / f"audit_{self.timestamp}.json"
    
    def get_statistics_path(self, filename: str) -> Path:
        """Gibt Pfad für Statistik-Datei zurück"""
        return self.dirs["analyzed"] / f"{filename}_statistics_{self.timestamp}.xlsx"
    
    def get_output_summary(self) -> Dict[str, Path]:
        """Gibt eine Zusammenfassung aller Ausgabepfade zurück"""
        return self.dirs.copy()
    
    def print_summary(self) -> None:
        """Druckt eine Zusammenfassung der Ausgabestruktur"""
        print("\n" + "=" * 60)
        print("Ausgabestruktur:")
        print("=" * 60)
        for key, path in self.dirs.items():
            print(f"  {key:20s} → {path}")
        print("=" * 60)
