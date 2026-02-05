"""Data Models für Qlassif-AI"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Union
from pathlib import Path


@dataclass
class SheetInfo:
    """Informationen über ein kompatibles Excel-Sheet"""
    name: str
    sheet: object  # openpyxl.worksheet.worksheet.Worksheet
    text_column_index: int
    header_row_index: int
    data_rows: List[int]
    
    def __post_init__(self):
        """Validiert die Daten nach Initialisierung"""
        if self.text_column_index < 0:
            raise ValueError("text_column_index muss >= 0 sein")
        if self.header_row_index < 0:
            raise ValueError("header_row_index muss >= 0 sein")
        if not self.data_rows:
            raise ValueError("data_rows darf nicht leer sein")


@dataclass
class CheckAttribute:
    """Benutzerdefiniertes Prüfmerkmal"""
    question: str
    answer_type: str  # "boolean" | "categorical" | "multi_categorical"
    categories: Optional[List[str]] = None
    definition: Optional[str] = None  # Kontext/Regeln für die Entscheidung
    
    def __post_init__(self):
        """Validiert die Daten nach Initialisierung"""
        # Validiere answer_type
        if self.answer_type not in ["boolean", "categorical", "multi_categorical"]:
            raise ValueError(
                f"answer_type muss 'boolean', 'categorical' oder 'multi_categorical' sein, nicht '{self.answer_type}'"
            )
        
        # Validiere question
        if not self.question or not self.question.strip():
            raise ValueError("question darf nicht leer sein")
        
        # Validiere categories für categorical und multi_categorical type
        if self.answer_type in ["categorical", "multi_categorical"]:
            if not self.categories:
                raise ValueError(
                    f"categories muss für answer_type '{self.answer_type}' angegeben werden"
                )
            if len(self.categories) < 2:
                raise ValueError(
                    "categories muss mindestens 2 Kategorien enthalten"
                )
        
        # Für boolean sollten keine categories angegeben werden
        if self.answer_type == "boolean" and self.categories is not None:
            raise ValueError(
                "categories sollte für answer_type 'boolean' None sein"
            )


@dataclass
class Config:
    """Konfiguration mit Prüfmerkmalen"""
    check_attributes: List[CheckAttribute]
    version: str = "1.0"
    model: str = "gpt-4o-mini"
    provider: str = "openai"  # "openai" oder "openrouter"
    text_column_name: Optional[str] = None  # Optionaler Name der Textspalte
    research_question: Optional[str] = None  # Optionale Untersuchungsfrage für Kontext
    include_reasoning: bool = True  # Ob Begründungen für Prüfmerkmale generiert werden sollen
    
    def __post_init__(self):
        """Validiert die Daten nach Initialisierung"""
        if not self.check_attributes:
            raise ValueError("check_attributes darf nicht leer sein")
        
        # Validiere provider
        if self.provider not in ["openai", "openrouter"]:
            raise ValueError(
                f"provider muss 'openai' oder 'openrouter' sein, nicht '{self.provider}'"
            )
        
        # Validiere, dass alle Elemente CheckAttribute sind
        for attr in self.check_attributes:
            if not isinstance(attr, CheckAttribute):
                raise ValueError(
                    f"Alle Elemente in check_attributes müssen CheckAttribute sein, "
                    f"nicht {type(attr)}"
                )


@dataclass
class AnalysisResult:
    """Ergebnis der LLM-Analyse für einen Text"""
    paraphrase: str
    sentiment: str
    sentiment_reason: str
    keywords: List[str]
    custom_checks: Dict[str, Union[bool, str, List[str], None]]
    custom_checks_reasons: Dict[str, str] = None  # Begründungen für custom_checks
    error: Optional[str] = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    
    def __post_init__(self):
        """Validiert die Daten nach Initialisierung"""
        # Initialisiere custom_checks_reasons falls None
        if self.custom_checks_reasons is None:
            self.custom_checks_reasons = {}
        
        # Validiere sentiment
        valid_sentiments = ["positiv", "negativ", "gemischt"]
        if self.sentiment not in valid_sentiments:
            raise ValueError(
                f"sentiment muss einer von {valid_sentiments} sein, nicht '{self.sentiment}'"
            )
        
        # Validiere keywords Anzahl (2-4)
        if not (2 <= len(self.keywords) <= 4):
            raise ValueError(
                f"keywords muss 2-4 Elemente enthalten, hat aber {len(self.keywords)}"
            )


@dataclass
class CategoryMapping:
    """Mapping von Kategorien zu Keywords"""
    categories: Dict[str, List[str]]
    
    def __post_init__(self):
        """Validiert die Daten nach Initialisierung"""
        if not self.categories:
            raise ValueError("categories darf nicht leer sein")


@dataclass
class ProcessingStats:
    """Statistiken über Verarbeitung"""
    total_rows: int = 0
    successful: int = 0
    failed: int = 0
    errors: List[str] = field(default_factory=list)
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_tokens: int = 0
    
    def add_success(self, prompt_tokens: int = 0, completion_tokens: int = 0):
        """
        Erhöht den Erfolgs-Zähler und fügt Token-Statistiken hinzu.
        
        Args:
            prompt_tokens: Anzahl Prompt-Tokens
            completion_tokens: Anzahl Completion-Tokens
        """
        self.successful += 1
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens
        self.total_tokens += (prompt_tokens + completion_tokens)
    
    def add_failure(self, error_msg: str):
        """Erhöht den Fehler-Zähler und fügt Fehlermeldung hinzu"""
        self.failed += 1
        self.errors.append(error_msg)
    
    def summary(self) -> str:
        """
        Erstellt eine Zusammenfassung der Verarbeitungsstatistiken.
        
        Returns:
            Formatierte Zusammenfassung als String
        """
        if self.total_rows == 0:
            return "Keine Zeilen verarbeitet"
        
        error_rate = (self.failed / self.total_rows * 100) if self.total_rows > 0 else 0
        
        summary = f"""
Verarbeitung abgeschlossen:
- Gesamt: {self.total_rows} Zeilen
- Erfolgreich: {self.successful}
- Fehlgeschlagen: {self.failed}
- Fehlerrate: {error_rate:.1f}%

Token-Statistiken:
- Prompt-Tokens: {self.total_prompt_tokens:,}
- Completion-Tokens: {self.total_completion_tokens:,}
- Gesamt-Tokens: {self.total_tokens:,}
"""
        
        if self.errors:
            summary += f"\nFehler ({len(self.errors)}):\n"
            # Zeige maximal die ersten 5 Fehler
            for error in self.errors[:5]:
                summary += f"  - {error}\n"
            if len(self.errors) > 5:
                summary += f"  ... und {len(self.errors) - 5} weitere Fehler\n"
        
        return summary
    
    def __post_init__(self):
        """Validiert die Daten nach Initialisierung"""
        if self.total_rows < 0:
            raise ValueError("total_rows muss >= 0 sein")
        if self.successful < 0:
            raise ValueError("successful muss >= 0 sein")
        if self.failed < 0:
            raise ValueError("failed muss >= 0 sein")
        if self.total_prompt_tokens < 0:
            raise ValueError("total_prompt_tokens muss >= 0 sein")
        if self.total_completion_tokens < 0:
            raise ValueError("total_completion_tokens muss >= 0 sein")
        if self.total_tokens < 0:
            raise ValueError("total_tokens muss >= 0 sein")


@dataclass
class PDFInfo:
    """Informationen über eine PDF-Datei"""
    path: Path
    filename: str
    size_bytes: int
    page_count: int
    char_count: int
    chunk_count: int
    
    def __post_init__(self):
        """Validiert die Daten nach Initialisierung"""
        if self.size_bytes < 0:
            raise ValueError("size_bytes muss >= 0 sein")
        if self.page_count < 0:
            raise ValueError("page_count muss >= 0 sein")
        if self.char_count < 0:
            raise ValueError("char_count muss >= 0 sein")
        if self.chunk_count < 1:
            raise ValueError("chunk_count muss >= 1 sein")


@dataclass
class PDFProcessingStats:
    """Statistiken für PDF-Verarbeitung"""
    total_pdfs: int = 0
    successful_pdfs: int = 0
    failed_pdfs: int = 0
    total_chunks: int = 0
    errors: List[str] = field(default_factory=list)
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_tokens: int = 0
    
    def add_pdf_success(self, chunk_count: int, prompt_tokens: int, completion_tokens: int):
        """
        Zeichnet erfolgreiche PDF-Verarbeitung auf.
        
        Args:
            chunk_count: Anzahl der Chunks für dieses PDF
            prompt_tokens: Anzahl Prompt-Tokens
            completion_tokens: Anzahl Completion-Tokens
        """
        self.successful_pdfs += 1
        self.total_chunks += chunk_count
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens
        self.total_tokens += (prompt_tokens + completion_tokens)
    
    def add_pdf_failure(self, error_msg: str):
        """
        Zeichnet fehlgeschlagene PDF-Verarbeitung auf.
        
        Args:
            error_msg: Fehlermeldung
        """
        self.failed_pdfs += 1
        self.errors.append(error_msg)
    
    def summary(self) -> str:
        """
        Erstellt eine Zusammenfassung der PDF-Verarbeitungsstatistiken.
        
        Returns:
            Formatierte Zusammenfassung als String
        """
        if self.total_pdfs == 0:
            return "Keine PDFs verarbeitet"
        
        error_rate = (self.failed_pdfs / self.total_pdfs * 100) if self.total_pdfs > 0 else 0
        
        summary = f"""
PDF-Verarbeitung abgeschlossen:
- Gesamt: {self.total_pdfs} PDFs
- Erfolgreich: {self.successful_pdfs}
- Fehlgeschlagen: {self.failed_pdfs}
- Fehlerrate: {error_rate:.1f}%
- Gesamt-Chunks: {self.total_chunks}

Token-Statistiken:
- Prompt-Tokens: {self.total_prompt_tokens:,}
- Completion-Tokens: {self.total_completion_tokens:,}
- Gesamt-Tokens: {self.total_tokens:,}
"""
        
        if self.errors:
            summary += f"\nFehler ({len(self.errors)}):\n"
            for error in self.errors[:5]:
                summary += f"  - {error}\n"
            if len(self.errors) > 5:
                summary += f"  ... und {len(self.errors) - 5} weitere Fehler\n"
        
        return summary
    
    def __post_init__(self):
        """Validiert die Daten nach Initialisierung"""
        if self.total_pdfs < 0:
            raise ValueError("total_pdfs muss >= 0 sein")
        if self.successful_pdfs < 0:
            raise ValueError("successful_pdfs muss >= 0 sein")
        if self.failed_pdfs < 0:
            raise ValueError("failed_pdfs muss >= 0 sein")
        if self.total_chunks < 0:
            raise ValueError("total_chunks muss >= 0 sein")


@dataclass
class Chunk:
    """Repräsentiert einen Text-Chunk"""
    chunk_id: int
    text: str
    char_count: int
    start_position: int
    end_position: int
    
    def __post_init__(self):
        """Validiert die Daten nach Initialisierung"""
        if self.chunk_id < 0:
            raise ValueError("chunk_id muss >= 0 sein")
        if self.char_count < 0:
            raise ValueError("char_count muss >= 0 sein")
        if self.start_position < 0:
            raise ValueError("start_position muss >= 0 sein")
        if self.end_position < self.start_position:
            raise ValueError("end_position muss >= start_position sein")
        if self.char_count != len(self.text):
            raise ValueError(f"char_count ({self.char_count}) muss der Länge von text ({len(self.text)}) entsprechen")


@dataclass
class MergedResult:
    """Zusammengeführtes Analyseergebnis für ein PDF-Dokument"""
    filename: str
    paraphrase: str
    sentiment: int  # -1, 0, oder 1
    sentiment_reason: str
    keywords: List[str]
    custom_checks: Dict[str, Union[str, bool, List[str]]]
    custom_checks_reasons: Dict[str, str]  # Begründungen für custom_checks
    keyword_category: str
    chunk_count: int
    error: Optional[str] = None
    
    def __post_init__(self):
        """Validiert die Daten nach Initialisierung"""
        if self.sentiment not in [-1, 0, 1]:
            raise ValueError(f"sentiment muss -1, 0 oder 1 sein, nicht {self.sentiment}")
        if self.chunk_count < 1:
            raise ValueError("chunk_count muss >= 1 sein")
