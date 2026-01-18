# Design Document: Qlassif-AI

## Overview

Qlassif-AI ist ein Python-basiertes Tool zur automatisierten Klassifizierung von Textantworten in Excel-Dateien mittels Large Language Models (LLMs). Das System liest Excel-Dateien ein, identifiziert Textspalten, führt verschiedene Analysen durch (Paraphrase, Sentiment, Keywords, benutzerdefinierte Prüfmerkmale) und schreibt die Ergebnisse strukturiert zurück. Zusätzlich werden Keywords automatisch in Überkategorien gruppiert und eine separate Auswertungsdatei mit Kategorie-Häufigkeiten erstellt.

## Architecture

Das System folgt einer Pipeline-Architektur mit folgenden Hauptkomponenten:

```
┌─────────────────┐
│  File Discovery │
│    & Selection  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Excel Loader   │
│  & Sheet Parser │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Config Manager  │
│ (Load/Create)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  LLM Analyzer   │
│  (Row-by-Row)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Keyword      │
│ Categorization  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Excel Writer &  │
│ Stats Generator │
└─────────────────┘
```

Die Architektur ist modular aufgebaut, sodass jede Komponente unabhängig getestet und erweitert werden kann.

## Components and Interfaces

### 1. File Discovery Module

**Verantwortlichkeit:** Durchsucht Verzeichnisse nach Excel-Dateien und präsentiert Auswahloptionen.

**Schnittstelle:**
```python
class FileDiscovery:
    def scan_directory(self, path: str) -> List[Path]:
        """Scannt Verzeichnis nach .xlsx und .xls Dateien"""
        
    def present_file_selection(self, files: List[Path]) -> Path:
        """Zeigt interaktive Auswahl und gibt gewählte Datei zurück"""
```

### 2. Excel Loader & Sheet Parser

**Verantwortlichkeit:** Lädt Excel-Dateien und identifiziert kompatible Sheets mit Textspalten.

**Schnittstelle:**
```python
class ExcelLoader:
    def load_workbook(self, file_path: Path) -> Workbook:
        """Lädt Excel-Datei mit openpyxl"""
        
    def find_compatible_sheets(self, workbook: Workbook) -> List[SheetInfo]:
        """Findet Sheets mit 'text', 'Antwort' oder 'answer' Spalten"""
        
    def locate_text_column(self, sheet: Worksheet) -> Optional[int]:
        """Findet Index der Textspalte in den ersten 5 Zeilen"""

@dataclass
class SheetInfo:
    name: str
    sheet: Worksheet
    text_column_index: int
    header_row_index: int
    data_rows: List[int]  # Indizes nicht-leerer Zeilen
```

### 3. Config Manager

**Verantwortlichkeit:** Verwaltet benutzerdefinierte Prüfmerkmale (laden, erstellen, speichern).

**Schnittstelle:**
```python
class ConfigManager:
    def find_config_file(self, directory: Path) -> Optional[Path]:
        """Sucht nach config.json im Verzeichnis"""
        
    def load_config(self, config_path: Path) -> Config:
        """Lädt und validiert Config-Datei"""
        
    def create_config_interactive(self) -> Config:
        """Interaktiver Dialog zur Erstellung neuer Prüfmerkmale"""
        
    def save_config(self, config: Config, path: Path) -> None:
        """Speichert Config als JSON"""

@dataclass
class CheckAttribute:
    question: str
    answer_type: str  # "boolean" oder "categorical"
    categories: Optional[List[str]] = None  # Nur für categorical

@dataclass
class Config:
    check_attributes: List[CheckAttribute]
    version: str = "1.0"
```

**JSON-Format:**
```json
{
  "version": "1.0",
  "check_attributes": [
    {
      "question": "Wird über Wettbewerb gesprochen?",
      "answer_type": "boolean"
    },
    {
      "question": "Welche Produktkategorie wird erwähnt?",
      "answer_type": "categorical",
      "categories": ["Hardware", "Software", "Service", "Keine"]
    }
  ]
}
```

### 4. LLM Analyzer

**Verantwortlichkeit:** Führt alle LLM-basierten Analysen durch (Paraphrase, Sentiment, Keywords, Prüfmerkmale).

**Schnittstelle:**
```python
class LLMAnalyzer:
    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.client = OpenAI(api_key=api_key, timeout=60.0)
        self.model = model
        
    def analyze_text(self, text: str, check_attributes: List[CheckAttribute]) -> AnalysisResult:
        """Führt vollständige Analyse eines Textes durch"""
        
    def _build_analysis_prompt(self, text: str, check_attributes: List[CheckAttribute]) -> str:
        """Erstellt strukturierten Prompt für LLM"""
        
    def _parse_llm_response(self, response: str) -> AnalysisResult:
        """Parst strukturierte LLM-Antwort"""

@dataclass
class AnalysisResult:
    paraphrase: str
    sentiment: str  # "positiv", "negativ", "gemischt"
    keywords: List[str]  # 2-4 Keywords
    custom_checks: Dict[str, Union[bool, str]]  # Ergebnisse der Prüfmerkmale
    error: Optional[str] = None
```

**LLM-Prompt-Struktur:**
```
Analysiere folgenden Text und gib die Ergebnisse im JSON-Format zurück:

Text: "{text}"

Bitte liefere:
1. Paraphrase: Eine umformulierte Version der Aussage
2. Sentiment: Klassifiziere als "positiv", "negativ" oder "gemischt"
3. Keywords: Extrahiere 2-4 Keywords (textnah, leicht abstrahiert)
4. Prüfmerkmale:
   - {question_1}: {answer_type_1}
   - {question_2}: {answer_type_2}

Antwortformat:
{
  "paraphrase": "...",
  "sentiment": "...",
  "keywords": ["...", "..."],
  "custom_checks": {
    "question_1": ...,
    "question_2": ...
  }
}
```

### 5. Keyword Categorizer

**Verantwortlichkeit:** Gruppiert alle Keywords in Überkategorien und ordnet diese den Antworten zu.

**Schnittstelle:**
```python
class KeywordCategorizer:
    def __init__(self, llm_analyzer: LLMAnalyzer):
        self.llm_analyzer = llm_analyzer
        
    def collect_all_keywords(self, results: List[AnalysisResult]) -> List[str]:
        """Sammelt und dedupliziert alle Keywords"""
        
    def generate_categories(self, keywords: List[str]) -> Dict[str, List[str]]:
        """Generiert Überkategorien mittels LLM"""
        
    def assign_categories(self, result: AnalysisResult, 
                         category_mapping: Dict[str, List[str]]) -> List[str]:
        """Ordnet Keywords einer Antwort zu Kategorien zu"""

@dataclass
class CategoryMapping:
    categories: Dict[str, List[str]]  # Kategorie -> Keywords
```

**LLM-Prompt für Kategorisierung:**
```
Gegeben ist folgende Liste von Keywords:
{keywords}

Entwickle 5-10 Überkategorien, die diese Keywords thematisch gruppieren.
Jedes Keyword sollte genau einer Kategorie zugeordnet werden.

Antwortformat:
{
  "Kategorie_1": ["keyword1", "keyword2", ...],
  "Kategorie_2": ["keyword3", "keyword4", ...],
  ...
}
```

### 6. Excel Writer

**Verantwortlichkeit:** Schreibt Analyseergebnisse zurück in Excel-Datei.

**Schnittstelle:**
```python
class ExcelWriter:
    def add_result_columns(self, sheet: Worksheet, text_col_index: int,
                          check_attributes: List[CheckAttribute]) -> Dict[str, int]:
        """Erstellt neue Spalten rechts der Textspalte"""
        
    def write_results(self, sheet: Worksheet, row_index: int,
                     result: AnalysisResult, column_mapping: Dict[str, int]) -> None:
        """Schreibt Analyseergebnis in Zeile"""
        
    def save_workbook(self, workbook: Workbook, output_path: Path) -> None:
        """Speichert modifizierte Excel-Datei"""
```

**Spaltenreihenfolge:**
1. Paraphrase
2. Sentiment
3. Keywords (kommagetrennt)
4. [Prüfmerkmal 1]
5. [Prüfmerkmal 2]
6. ...
7. Keyword_Kategorie (kommagetrennt)

### 7. Statistics Generator

**Verantwortlichkeit:** Erstellt Auswertungsdatei mit Kategorie-Häufigkeiten.

**Schnittstelle:**
```python
class StatisticsGenerator:
    def calculate_category_frequencies(self, 
                                      category_assignments: List[List[str]]) -> Dict[str, int]:
        """Berechnet Häufigkeit jeder Kategorie"""
        
    def collect_keywords_per_category(self,
                                     category_mapping: Dict[str, List[str]]) -> Dict[str, Set[str]]:
        """Sammelt alle Keywords pro Kategorie"""
        
    def create_statistics_workbook(self, 
                                  frequencies: Dict[str, int],
                                  keywords_per_category: Dict[str, Set[str]]) -> Workbook:
        """Erstellt neue Excel-Datei mit Statistiken"""
        
    def save_statistics(self, workbook: Workbook, output_path: Path) -> None:
        """Speichert Statistik-Datei"""
```

**Statistik-Excel-Format:**
| Kategorie | Häufigkeit | Keywords |
|-----------|------------|----------|
| Kategorie_1 | 45 | keyword1, keyword2, keyword3 |
| Kategorie_2 | 32 | keyword4, keyword5 |
| ... | ... | ... |

### 8. Environment Manager

**Verantwortlichkeit:** Lädt API-Keys aus Umgebungsvariablen.

**Schnittstelle:**
```python
class EnvironmentManager:
    def load_env_file(self, search_paths: List[Path]) -> Optional[Path]:
        """Sucht und lädt .env-Datei"""
        
    def get_api_key(self) -> str:
        """Holt OPENAI_API_KEY aus Umgebung"""
        
    def validate_api_key(self, api_key: str) -> bool:
        """Validiert Format des API-Keys"""
```

## Data Models

### Core Data Structures

```python
from dataclasses import dataclass
from typing import List, Dict, Optional, Union
from pathlib import Path
from openpyxl import Workbook
from openpyxl.worksheet.worksheet import Worksheet

@dataclass
class SheetInfo:
    """Informationen über ein kompatibles Excel-Sheet"""
    name: str
    sheet: Worksheet
    text_column_index: int
    header_row_index: int
    data_rows: List[int]

@dataclass
class CheckAttribute:
    """Benutzerdefiniertes Prüfmerkmal"""
    question: str
    answer_type: str  # "boolean" | "categorical"
    categories: Optional[List[str]] = None

@dataclass
class Config:
    """Konfiguration mit Prüfmerkmalen"""
    check_attributes: List[CheckAttribute]
    version: str = "1.0"

@dataclass
class AnalysisResult:
    """Ergebnis der LLM-Analyse für einen Text"""
    paraphrase: str
    sentiment: str
    keywords: List[str]
    custom_checks: Dict[str, Union[bool, str]]
    error: Optional[str] = None

@dataclass
class CategoryMapping:
    """Mapping von Kategorien zu Keywords"""
    categories: Dict[str, List[str]]

@dataclass
class ProcessingStats:
    """Statistiken über Verarbeitung"""
    total_rows: int
    successful: int
    failed: int
    errors: List[str]
```

## Correctness Properties

*Eine Property ist eine Eigenschaft oder ein Verhalten, das über alle gültigen Ausführungen eines Systems hinweg wahr sein sollte - im Wesentlichen eine formale Aussage darüber, was das System tun soll. Properties dienen als Brücke zwischen menschenlesbaren Spezifikationen und maschinenverifizierbaren Korrektheitsgarantien.*



Bevor ich die Correctness Properties schreibe, führe ich eine Prework-Analyse durch, um zu bestimmen, welche Acceptance Criteria testbar sind:



### Properties

**Property 1: Excel-Datei-Erkennung**
*Für jedes* Verzeichnis mit Excel-Dateien (.xlsx, .xls) sollte die Scan-Funktion alle diese Dateien finden und als Liste zurückgeben.
**Validates: Requirements 1.1, 1.2**

**Property 2: Workbook-Laden und Sheet-Analyse**
*Für jede* gültige Excel-Datei sollte das Laden erfolgreich sein und alle Sheets sollten auf Kompatibilität analysiert werden.
**Validates: Requirements 1.3**

**Property 3: Kompatible Sheet-Erkennung**
*Für jedes* Sheet mit einer Kopfspalte namens "text", "Antwort" oder "answer" (case-insensitive) sollte das Sheet als kompatibel markiert werden.
**Validates: Requirements 1.4**

**Property 4: Textspalten-Identifikation**
*Für jedes* Sheet sollte die Funktion die Kopfzeile (innerhalb der ersten 5 Zeilen) nach Spalten mit den Namen "text", "Antwort" oder "answer" durchsuchen und die erste gefundene Spalte zurückgeben.
**Validates: Requirements 2.1, 2.4**

**Property 5: Nicht-leere Zeilen-Identifikation**
*Für jedes* Sheet mit einer Textspalte sollten nur Zeilen mit nicht-leerem Text als zu analysierende Einträge markiert werden.
**Validates: Requirements 2.2**

**Property 6: LLM-Analyse-Vollständigkeit**
*Für jeden* nicht-leeren Text sollte die Analyse-Funktion eine nicht-leere Paraphrase, ein gültiges Sentiment und 2-4 Keywords zurückgeben.
**Validates: Requirements 3.1, 3.2, 3.3**

**Property 7: Sentiment-Validität**
*Für jede* Textanalyse sollte das zurückgegebene Sentiment genau einer der Werte "positiv", "negativ" oder "gemischt" sein.
**Validates: Requirements 3.2**

**Property 8: Keyword-Anzahl**
*Für jede* Textanalyse sollte die Anzahl der extrahierten Keywords zwischen 2 und 4 (inklusive) liegen.
**Validates: Requirements 3.3**

**Property 9: Spalten-Positionierung**
*Für jedes* Sheet sollten die Ergebnisspalten direkt rechts der Textspalte beginnen und in der korrekten Reihenfolge erstellt werden.
**Validates: Requirements 3.4, 7.1**

**Property 10: Fehlertoleranz bei LLM-Aufrufen**
*Für jeden* LLM-API-Fehler sollte das System den Fehler protokollieren, die betroffene Zeile überspringen und mit der nächsten Zeile fortfahren.
**Validates: Requirements 3.5, 8.2**

**Property 11: API-Key-Laden**
*Für jede* Systemausführung sollte der API-Key aus der Umgebungsvariable OPENAI_API_KEY oder aus einer .env-Datei geladen werden.
**Validates: Requirements 3.8, 11.1, 11.3, 11.4, 11.5**

**Property 12: Config-Datei-Suche**
*Für jedes* Verzeichnis sollte die Funktion nach einer config.json-Datei suchen und diese zurückgeben, falls vorhanden.
**Validates: Requirements 4.1**

**Property 13: Prüfmerkmal-Speicherung**
*Für jedes* definierte Prüfmerkmal sollte die Datenstruktur die Prüffrage und den Antworttyp (boolean oder categorical) korrekt speichern.
**Validates: Requirements 4.4**

**Property 14: Config-Serialisierung Round-Trip**
*Für jede* gültige Config-Struktur sollte das Speichern als JSON und anschließende Laden eine äquivalente Config-Struktur zurückgeben.
**Validates: Requirements 4.5, 5.1, 5.2**

**Property 15: Boolean-Prüfmerkmal-Validität**
*Für jedes* Prüfmerkmal vom Typ boolean sollte die LLM-Antwort entweder true oder false sein.
**Validates: Requirements 4.6**

**Property 16: Kategoriale-Prüfmerkmal-Validität**
*Für jedes* Prüfmerkmal vom Typ categorical sollte die LLM-Antwort eine der vordefinierten Kategorien sein.
**Validates: Requirements 4.7**

**Property 17: Ungültige Config-Behandlung**
*Für jede* ungültige oder fehlerhafte Config-Datei sollte das System einen Fehler zurückgeben und nicht abstürzen.
**Validates: Requirements 5.3**

**Property 18: Keyword-Sammlung**
*Für alle* Analyseergebnisse sollte die Funktion alle Keywords sammeln und deduplizieren.
**Validates: Requirements 6.1**

**Property 19: Kategorie-Generierung**
*Für jede* Liste von Keywords sollte die LLM-Funktion Überkategorien zurückgeben, die die Keywords gruppieren.
**Validates: Requirements 6.2**

**Property 20: Kategorie-Zuordnung**
*Für jede* Textantwort mit Keywords sollte mindestens eine Kategorie zugeordnet werden.
**Validates: Requirements 6.3**

**Property 21: Kategorie-Spalte-Erstellung**
*Für jedes* verarbeitete Sheet sollte eine Spalte "Keyword_Kategorie" mit den zugeordneten Kategorien existieren.
**Validates: Requirements 6.4**

**Property 22: Spalten-Benennung**
*Für jedes* verarbeitete Sheet sollten die Ergebnisspalten die Namen "Paraphrase", "Sentiment", "Keywords", [Prüfmerkmal-Namen] und "Keyword_Kategorie" haben.
**Validates: Requirements 7.2, 7.3**

**Property 23: Datei-Speicherung**
*Für jede* verarbeitete Excel-Datei sollte die Ausgabedatei erfolgreich gespeichert werden und lesbar sein.
**Validates: Requirements 7.4**

**Property 24: Multi-Sheet-Verarbeitung**
*Für jede* Excel-Datei mit mehreren kompatiblen Sheets sollten alle kompatiblen Sheets mit Ergebnissen aktualisiert werden.
**Validates: Requirements 7.5**

**Property 25: Excel-Ladefehler-Behandlung**
*Für jede* ungültige oder nicht-existierende Excel-Datei sollte das System einen aussagekräftigen Fehler zurückgeben.
**Validates: Requirements 8.1**

**Property 26: Verarbeitungs-Statistiken**
*Für jede* abgeschlossene Verarbeitung sollte das System die Anzahl der verarbeiteten Zeilen, erfolgreichen Analysen und Fehler korrekt zählen.
**Validates: Requirements 8.3**

**Property 27: Kritische-Fehler-Behandlung**
*Für jeden* kritischen Fehler (z.B. fehlender API-Key) sollte das System die Verarbeitung stoppen und einen Fehler zurückgeben.
**Validates: Requirements 8.4**

**Property 28: Kategorie-Häufigkeits-Berechnung**
*Für alle* kategorisierten Antworten sollte die Häufigkeit jeder Kategorie korrekt gezählt werden.
**Validates: Requirements 10.1**

**Property 29: Keywords-pro-Kategorie-Sammlung**
*Für jede* Kategorie sollten alle zugehörigen Keywords gesammelt und dedupliziert werden.
**Validates: Requirements 10.2, 10.5**

**Property 30: Statistik-Excel-Erstellung**
*Für jede* abgeschlossene Verarbeitung sollte eine separate Excel-Datei mit Spalten "Kategorie", "Häufigkeit" und "Keywords" erstellt werden.
**Validates: Requirements 10.3, 10.4**

**Property 31: Kategorie-Sortierung**
*Für jede* Statistik-Excel sollten die Kategorien nach Häufigkeit absteigend sortiert sein.
**Validates: Requirements 10.6**

## Error Handling

### Fehlertypen und Behandlung

1. **Datei-Fehler**
   - Nicht-existierende Dateien → FileNotFoundError mit klarer Meldung
   - Ungültige Excel-Dateien → InvalidFileError mit Dateiname
   - Keine kompatiblen Sheets → NoCompatibleSheetsError

2. **API-Fehler**
   - Fehlender API-Key → MissingAPIKeyError (kritisch, stoppt Verarbeitung)
   - API-Timeout → Retry mit exponential backoff (max 3 Versuche)
   - API-Rate-Limit → Wartezeit und Retry
   - Ungültige API-Antwort → Zeile überspringen, Fehler protokollieren

3. **Config-Fehler**
   - Ungültige JSON → InvalidConfigError, Fallback zu interaktivem Dialog
   - Fehlende Felder → ValidationError mit Details
   - Ungültige Antworttypen → ValidationError

4. **Verarbeitungs-Fehler**
   - Leere Textspalte → Warnung, Sheet überspringen
   - Schreibfehler → IOError, Verarbeitung stoppen

### Fehler-Logging

```python
import logging

logger = logging.getLogger("qlassif-ai")
logger.setLevel(logging.INFO)

# Format: [TIMESTAMP] [LEVEL] [MODULE] Message
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)

# Console Handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# File Handler (optional)
file_handler = logging.FileHandler('qlassif-ai.log')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
```

### Fehler-Statistiken

Das System sammelt während der Verarbeitung Fehlerstatistiken:

```python
@dataclass
class ProcessingStats:
    total_rows: int = 0
    successful: int = 0
    failed: int = 0
    errors: List[str] = field(default_factory=list)
    
    def add_success(self):
        self.successful += 1
        
    def add_failure(self, error_msg: str):
        self.failed += 1
        self.errors.append(error_msg)
        
    def summary(self) -> str:
        return f"""
Verarbeitung abgeschlossen:
- Gesamt: {self.total_rows} Zeilen
- Erfolgreich: {self.successful}
- Fehlgeschlagen: {self.failed}
- Fehlerrate: {self.failed/self.total_rows*100:.1f}%
"""
```

## Testing Strategy

### Dual Testing Approach

Das System wird mit einer Kombination aus Unit Tests und Property-Based Tests getestet:

- **Unit Tests**: Verifizieren spezifische Beispiele, Edge Cases und Fehlerbehandlung
- **Property Tests**: Verifizieren universelle Properties über alle Eingaben hinweg

Beide Testarten sind komplementär und notwendig für umfassende Abdeckung.

### Property-Based Testing

Wir verwenden **Hypothesis** als Property-Based Testing Framework für Python.

**Konfiguration:**
- Minimum 100 Iterationen pro Property Test
- Jeder Test referenziert seine Design-Property
- Tag-Format: `# Feature: excel-text-classifier, Property {number}: {property_text}`

**Beispiel:**
```python
from hypothesis import given, strategies as st
import hypothesis

# Feature: excel-text-classifier, Property 7: Sentiment-Validität
@given(text=st.text(min_size=1))
@hypothesis.settings(max_examples=100)
def test_sentiment_validity(text):
    """Für jede Textanalyse sollte das Sentiment 'positiv', 'negativ' oder 'gemischt' sein"""
    analyzer = LLMAnalyzer(api_key="test-key")
    result = analyzer.analyze_text(text, [])
    
    assert result.sentiment in ["positiv", "negativ", "gemischt"]
```

### Unit Testing

Unit Tests fokussieren sich auf:
- Spezifische Beispiele (z.B. bekannte Texte mit erwarteten Sentiments)
- Edge Cases (z.B. leere Sheets, fehlende Spalten)
- Fehlerbehandlung (z.B. ungültige Config-Dateien)
- Integration zwischen Komponenten

**Test-Struktur:**
```
tests/
├── unit/
│   ├── test_file_discovery.py
│   ├── test_excel_loader.py
│   ├── test_config_manager.py
│   ├── test_llm_analyzer.py
│   ├── test_keyword_categorizer.py
│   ├── test_excel_writer.py
│   ├── test_statistics_generator.py
│   └── test_environment_manager.py
├── property/
│   ├── test_properties_file_handling.py
│   ├── test_properties_analysis.py
│   ├── test_properties_config.py
│   └── test_properties_output.py
└── integration/
    └── test_end_to_end.py
```

### Test Data Generators

Für Property-Based Tests benötigen wir intelligente Generatoren:

```python
from hypothesis import strategies as st

# Generator für Excel-kompatible Spaltennamen
@st.composite
def excel_column_names(draw):
    valid_names = ["text", "Antwort", "answer", "TEXT", "ANTWORT", "ANSWER"]
    return draw(st.sampled_from(valid_names))

# Generator für CheckAttribute
@st.composite
def check_attribute(draw):
    question = draw(st.text(min_size=5, max_size=100))
    answer_type = draw(st.sampled_from(["boolean", "categorical"]))
    categories = None
    if answer_type == "categorical":
        categories = draw(st.lists(st.text(min_size=1, max_size=20), min_size=2, max_size=5))
    return CheckAttribute(question=question, answer_type=answer_type, categories=categories)

# Generator für Config
@st.composite
def config_generator(draw):
    attributes = draw(st.lists(check_attribute(), min_size=1, max_size=10))
    return Config(check_attributes=attributes)

# Generator für Textantworten
text_responses = st.text(min_size=10, max_size=500, alphabet=st.characters(blacklist_categories=('Cs',)))
```

### Mocking Strategy

Für Tests, die LLM-API-Aufrufe beinhalten:
- **Unit Tests**: Mocken der OpenAI API mit vordefinierten Antworten
- **Property Tests**: Verwenden von Dummy-Responses, die das erwartete Format haben
- **Integration Tests**: Optional echte API-Aufrufe mit Test-API-Key

```python
from unittest.mock import Mock, patch

@patch('openai.OpenAI')
def test_llm_analyzer_with_mock(mock_openai):
    # Mock API response
    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(content='{"paraphrase": "...", "sentiment": "positiv", "keywords": ["a", "b"]}'))]
    mock_openai.return_value.chat.completions.create.return_value = mock_response
    
    analyzer = LLMAnalyzer(api_key="test-key")
    result = analyzer.analyze_text("Test text", [])
    
    assert result.sentiment == "positiv"
```

### Test Coverage Goals

- **Line Coverage**: Minimum 80%
- **Branch Coverage**: Minimum 70%
- **Property Coverage**: Alle 31 Properties müssen getestet werden
- **Edge Case Coverage**: Alle identifizierten Edge Cases müssen Unit Tests haben

### Continuous Testing

- Tests laufen bei jedem Commit (CI/CD)
- Property Tests laufen mit erhöhter Iteration-Anzahl (1000) im Nightly Build
- Performance-Tests für große Excel-Dateien (>1000 Zeilen)
