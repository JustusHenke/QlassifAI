# Changelog

Alle wesentlichen Änderungen an Qlassif-AI.

Das Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.1.0/),
und dieses Projekt hält sich an [Semantic Versioning](https://semver.org/lang/de/).

## [Unreleased]

Keine Änderungen seit dem letzten Release.

## [2.0.0] - 2025-07-27

### Hinzugefügt
- **Wissenschaftliche Methodik** (A011-A013)
  - `ScientificConfig` Dataclass für optionale Parameter
  - `Confidence Scores` für LLM-Klassifikationen (0-100%)
  - `Multi-Model-Intercoder` für Kodierervergleich (optional)
  - `KappaCalculator` für Cohen's Kappa / Fleiss' Kappa
  - `ReproducibilityManager` für Methodenprotokoll und Audit Trail
  - Automatische Generierung von `methodology.md`, `codebook.json`, `frequency_tables.csv`

- **Exception-Hierarchie** (A006)
  - Zentrale `exceptions.py` mit spezialisierten Fehlertypen
  - `QlassifError` als Basis-Exception
  - `ConfigError`, `APIKeyError`, `ExcelError`, `PDFError`, `LLMError`, `FileDiscoveryError`

- **Excel-Writer Refactoring** (A003)
  - 7 wiederverwendbare Helper Methods
  - Einheitliches Header-Styling
  - Zentrale Formatierung für Custom Checks

- **Unit Tests** (A007)
  - 48 Tests für ConfidenceEngine, KappaCalculator, MultiCoder, ReproducibilityManager, Config
  - 5 Integration Tests für gesamten wissenschaftlichen Workflow

### Geändert
- **API-Key-Validierung** (A002)
  - OpenAI: `sk-` oder `sk-proj-` Prefix, Mindestlänge 40
  - OpenRouter: `sk-or-` Prefix, Mindestlänge 40
  - Keine Leerzeichen erlaubt

- **Path Validation** (A004)
  - Pfade werden mit `.resolve()` normalisiert

- **JSON-Parsing** (A009)
  - Robuster gegen LLM-Antworten mit Erklärtext
  - Extrahiert JSON aus Text vor/nach dem Objekt

- **Keyword-Limit** (A010)
  - Von 150 auf 200 erhöht
  - Dynamisiert via Klassen-Attribut

- **Requirements gepinnt** (A008)
  - Exakte Versionen statt `>=`

### Entfernt
- Kommentierter API-Key aus `.env` (A001)

## [1.0.0] - 2025-01-15

### Hinzugefügt
- Initiale Veröffentlichung
- Excel-Modus mit zeilenweiser Textanalyse
- PDF-Modus mit intelligenter Chunking-Strategie
- Benutzerdefinierte Prüfmerkmale (boolean, categorical, multi_categorical)
- Keyword-Kategorisierung via LLM
- Statistik-Generierung pro Sheet und gesamt
- Multi-Provider-Support (OpenAI, OpenRouter)
- Interaktive Config-Erstellung
