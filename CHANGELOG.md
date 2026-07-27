# Changelog

Alle wesentlichen Aenderungen an Qlassif-AI.

Das Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.1.0/),
und dieses Projekt haelt sich an [Semantic Versioning](https://semver.org/lang/de/).

## [Unreleased]

Keine Aenderungen seit dem letzten Release.

## [2.0.2] - 2025-07-27

### Geaendert
- Alle Ausgaben (Analysedaten, Statistiken, Intercoder, Kappa) in EINER Excel-Datei statt separater Dateien
- Output-Struktur vereinfacht: Nur noch `{name}_analyzed_YYYYMMDD.xlsx` + reproducibility-Dateien

## [2.0.1] - 2025-07-27

### Geaendert
- `max_tokens` von 1000 auf 10000 erhoeht (verhindert JSON-Abschneiden bei langen Fragebezeichnungen)
- `save_all()` Aufrufe in main.py korrigiert (output_dir Parameter fehlte)
- Example Config mit angepassten Prueffragen fuer Erstsemester-Unterstuetzung

## [2.0.0] - 2025-07-27

### Hinzugefuegt

**Wissenschaftliche Methodik (A011-A013)**
- `ScientificConfig` Dataclass fuer optionale Parameter
- `Confidence Scores` fuer LLM-Klassifikationen (0-100%)
- `Multi-Model-Intercoder` fuer Kodierervergleich (optional)
- `KappaCalculator` fuer Cohen's Kappa / Fleiss' Kappa
- `ReproducibilityManager` fuer Methodenprotokoll und Audit Trail
- Automatische Generierung von `methodology.md`, `codebook.json`, `frequency_tables.csv`

**6 LLM-Provider**
- OpenRouter (Standard), OpenAI, Anthropic, Mistral (Cloud)
- Ollama, LMStudio (lokal, kein API-Key noetig)
- Provider-spezifische API-Methoden (OpenAI-kompatibel, Anthropic SDK, Mistral SDK)

**Exception-Hierarchie (A006)**
- Zentrale `exceptions.py` mit spezialisierten Fehlertypen
- `QlassifError` als Basis-Exception
- `ConfigError`, `APIKeyError`, `ExcelError`, `PDFError`, `LLMError`, `FileDiscoveryError`

**Excel-Writer Refactoring (A003)**
- 7 wiederverwendbare Helper Methods
- Einheitliches Header-Styling
- Zentrale Formatierung fuer Custom Checks

**Unit & Integration Tests (A007)**
- 48 Unit Tests fuer ConfidenceEngine, KappaCalculator, MultiCoder, ReproducibilityManager, Config
- 5 Integration Tests fuer gesamten wissenschaftlichen Workflow

### Geaendert

**Multi-Coder uebernimmt Hauptanalyse**
- Wenn `multi_coder=true`, fuehrt der Primary Codierer die Hauptanalyse durch
- Keine doppelte Analyse mehr (vorher: Hauptanalyse + Multi-Coder = 2x)
- Ergebnis des Primary Codierers fliesst direkt in die Haupttabelle ein

**Output-Struktur vereinfacht**
- Alle Dateien flach in `{InputDateiName}_analyzed/` (keine Unterordner mehr)
- Enthaelt: Excel-Dateien, methodology.md, codebook.json, frequency_tables.csv, audit_trail

**API-Key-Validierung (A002)**
- OpenAI: `sk-` oder `sk-proj-` Prefix, Mindestlaenge 40
- OpenRouter: `sk-or-` Prefix, Mindestlaenge 40
- Lokale Provider (Ollama, LMStudio) benoetigen keinen API-Key

**Path Validation (A004)**
- Pfade werden mit `.resolve()` normalisiert

**JSON-Parsing (A009)**
- Robuster gegen LLM-Antworten mit Erklaertext
- Extrahiert JSON aus Text vor/nach dem Objekt

**Keyword-Limit (A010)**
- Von 150 auf 200 erhoeht, dynamisiert via Klassen-Attribut

**Requirements gepinnt (A008)**
- Exakte Versionen statt `>=`
- `anthropic>=0.39.0` und `mistralai>=1.0.0` hinzugefuegt

**Config interaktiv erweitert**
- Wissenschaftliche Parameter abfragbar (Multi-Coder, Konfidenz-Schwellwert, Seed)

**Default Provider**
- Standard ist jetzt `openrouter` statt `openai`

### Entfernt
- Kommentierter API-Key aus `.env` (A001)

## [1.0.0] - 2025-01-15

### Hinzugefuegt
- Initiale Veroeffentlichung
- Excel-Modus mit zeilenweiser Textanalyse
- PDF-Modus mit intelligenter Chunking-Strategie
- Benutzerdefinierte Pruefmerkmale (boolean, categorical, multi_categorical)
- Keyword-Kategorisierung via LLM
- Statistik-Generierung pro Sheet und gesamt
- Multi-Provider-Support (OpenAI, OpenRouter)
- Interaktive Config-Erstellung
