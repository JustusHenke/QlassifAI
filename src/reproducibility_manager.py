"""Reproducibility Manager fuer wissenschaftliche Reproduzierbarkeit"""

import json
import hashlib
import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from logging_config import get_logger

logger = get_logger("reproducibility_manager")


@dataclass
class AuditEntry:
    """Einzelner Audit-Eintrag fuer Reproduzierbarkeit"""
    timestamp: str
    model: str
    provider: str
    temperature: float = 0.3
    prompt_hash: str = ""
    response_hash: str = ""
    seed: Optional[int] = None
    input_text_hash: str = ""
    result_summary: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass
class MethodologyMetadata:
    """Metadaten fuer das Methodenprotokoll"""
    project_name: str = "Qlassif-AI"
    version: str = "2.0"
    analysis_date: str = ""
    model: str = ""
    provider: str = ""
    temperature: float = 0.3
    seed: Optional[int] = None
    research_question: str = ""
    check_attributes: List[Dict[str, Any]] = field(default_factory=list)
    multi_coder: bool = False
    coder_models: List[str] = field(default_factory=list)
    confidence_threshold: int = 70
    total_items: int = 0
    total_successful: int = 0
    total_failed: int = 0
    total_tokens: int = 0


class ReproducibilityManager:
    """
    Verwaltet Reproduzierbarkeit und Audit Trail fuer wissenschaftliche Analysen.
    
    Speichert alle Dateien flach in das angegebene Ausgabeverzeichnis.
    """
    
    def __init__(self, output_dir: Path):
        """
        Initialisiert ReproducibilityManager.
        
        Args:
            output_dir: Ausgabeverzeichnis (flach, keine Unterordner)
        """
        self.output_dir = Path(output_dir)
        self.audit_entries: List[AuditEntry] = []
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def hash_content(content: str) -> str:
        """Erstellt SHA256-Hash fuer Inhalt"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def add_audit_entry(self, entry: AuditEntry) -> None:
        """Fuegt einen Audit-Eintrag hinzu"""
        self.audit_entries.append(entry)
        logger.info(f"Audit-Eintrag hinzugefuegt: {entry.timestamp}")
    
    def record_analysis(self, model: str, provider: str, prompt: str, 
                        response: str, seed: Optional[int] = None,
                        input_text: str = "", temperature: float = 0.3) -> AuditEntry:
        """Zeichnet eine Analyse-Einheit im Audit Trail auf."""
        entry = AuditEntry(
            timestamp=datetime.now().isoformat(),
            model=model,
            provider=provider,
            temperature=temperature,
            prompt_hash=self.hash_content(prompt),
            response_hash=self.hash_content(response),
            seed=seed,
            input_text_hash=self.hash_content(input_text),
            result_summary=response[:200] if response else ""
        )
        self.add_audit_entry(entry)
        return entry
    
    def save_audit_trail(self, filepath: Path) -> Path:
        """
        Speichert den Audit Trail als JSON-Datei.
        
        Args:
            filepath: Vollstaendiger Pfad zur Audit-Trail-Datei
        """
        data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_entries": len(self.audit_entries)
            },
            "entries": [
                {
                    "timestamp": e.timestamp,
                    "model": e.model,
                    "provider": e.provider,
                    "temperature": e.temperature,
                    "prompt_hash": e.prompt_hash,
                    "response_hash": e.response_hash,
                    "seed": e.seed,
                    "input_text_hash": e.input_text_hash,
                    "result_summary": e.result_summary
                }
                for e in self.audit_entries
            ]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Audit Trail gespeichert: {filepath}")
        return filepath
    
    def generate_methodology(self, filepath: Path, metadata: MethodologyMetadata) -> Path:
        """Generiert eine methodology.md Datei."""
        content = f"""# Methodenprotokoll: {metadata.project_name}

## Ueberblick

| Feld | Wert |
|------|------|
| Projekt | {metadata.project_name} |
| Version | {metadata.version} |
| Analysedatum | {metadata.analysis_date} |
| Modell | {metadata.model} |
| Provider | {metadata.provider} |
| Temperatur | {metadata.temperature} |
| Seed | {metadata.seed if metadata.seed is not None else "nicht gesetzt"} |

## Untersuchungsfrage

{metadata.research_question if metadata.research_question else "Keine Untersuchungsfrage definiert."}

## Pruefmerkmale

| # | Pruefmerkmal | Antworttyp | Kategorien |
|---|-------------|------------|------------|
"""
        
        for idx, attr in enumerate(metadata.check_attributes, start=1):
            question = attr.get("question", "")
            answer_type = attr.get("answer_type", "")
            categories = ", ".join(attr.get("categories", []))
            content += f"| {idx} | {question} | {answer_type} | {categories} |\n"
        
        content += f"""
## Wissenschaftliche Parameter

| Parameter | Wert |
|-----------|------|
| Multi-Coder | {metadata.multi_coder} |
"""
        
        if metadata.multi_coder:
            content += f"| Kodierer-Modelle | {', '.join(metadata.coder_models)} |\n"
        
        content += f"| Konfidenz-Schwellwert | {metadata.confidence_threshold}% |\n"
        
        content += f"""
## Verarbeitungsstatistiken

| Metrik | Wert |
|--------|------|
| Gesamt Items | {metadata.total_items} |
| Erfolgreich | {metadata.total_successful} |
| Fehlgeschlagen | {metadata.total_failed} |
| Gesamt Tokens | {metadata.total_tokens:,} |

## Reproduzierbarkeit

- Alle Prompt-Templates sind in der audit_trail-Datei gespeichert
- API-Responses werden mit SHA256-Hashes referenziert
- Modell-Parameter und Seed sind dokumentiert

---
Erstellt am {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} von {metadata.project_name} v{metadata.version}
"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Methodology generiert: {filepath}")
        return filepath
    
    def export_codebook(self, filepath: Path, check_attributes: List[Dict[str, Any]]) -> Path:
        """Exportiert Pruefmerkmale als maschinenlesbares codebook.json."""
        codebook = {
            "version": "2.0",
            "generated_at": datetime.now().isoformat(),
            "project": "Qlassif-AI",
            "check_attributes": []
        }
        
        for attr in check_attributes:
            entry = {
                "question": attr.get("question", ""),
                "answer_type": attr.get("answer_type", ""),
                "definition": attr.get("definition", ""),
            }
            if attr.get("categories"):
                entry["categories"] = attr["categories"]
            codebook["check_attributes"].append(entry)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(codebook, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Codebook exportiert: {filepath}")
        return filepath
    
    def export_frequency_tables(self, filepath: Path, results: List[Dict[str, Any]], 
                                 check_attributes: List[Dict[str, Any]]) -> Path:
        """Exportiert Frequenztabelle als CSV fuer R/SPSS-Import."""
        header = ["Pruefmerkmal", "Wert", "Haeufigkeit", "Prozent"]
        rows = [header]
        total = len(results)
        
        for attr in check_attributes:
            question = attr.get("question", "")
            answer_type = attr.get("answer_type", "")
            value_counts = {}
            
            for result in results:
                value = result.get("custom_checks", {}).get(question)
                if value is not None:
                    if answer_type == "boolean":
                        display_value = "Ja" if value else "Nein"
                        value_counts[display_value] = value_counts.get(display_value, 0) + 1
                    elif answer_type == "multi_categorical" and isinstance(value, list):
                        for v in value:
                            display_value = str(v)
                            value_counts[display_value] = value_counts.get(display_value, 0) + 1
                    else:
                        display_value = str(value)
                        value_counts[display_value] = value_counts.get(display_value, 0) + 1
            
            sorted_values = sorted(value_counts.items(), key=lambda x: x[1], reverse=True)
            for value, count in sorted_values:
                percent = (count / total * 100) if total > 0 else 0
                rows.append([question, value, count, f"{percent:.1f}"])
        
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(rows)
        
        logger.info(f"Frequenztabelle exportiert: {filepath}")
        return filepath
    
    def save_all(self, output_dir: Path,
                 metadata: MethodologyMetadata, 
                 check_attributes: List[Dict[str, Any]],
                 results: List[Dict[str, Any]] = None) -> Dict[str, Path]:
        """
        Speichert alle Reproduzierbarkeitsdateien in ein flaches Verzeichnis.
        
        Returns:
            Dict mit Dateinamen -> Pfad
        """
        output_files = {}
        
        output_files["methodology"] = self.generate_methodology(
            output_dir / "methodology.md", metadata
        )
        output_files["codebook"] = self.export_codebook(
            output_dir / "codebook.json", check_attributes
        )
        
        if results:
            output_files["frequency_tables"] = self.export_frequency_tables(
                output_dir / "frequency_tables.csv", results, check_attributes
            )
        
        output_files["audit_trail"] = self.save_audit_trail(
            output_dir / f"audit_trail_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        logger.info(f"Alle Reproduzierbarkeitsdateien gespeichert: {list(output_files.keys())}")
        return output_files
