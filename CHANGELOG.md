# Changelog

Alle wesentlichen Aenderungen an Qlassif-AI.

Das Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.1.0/),
und dieses Projekt haelt sich an [Semantic Versioning](https://semver.org/lang/de/).

## [Unreleased]

### Behoben
- Keyword-Kategorisierung: Crash bei `None`-Antworten des LLM (`'NoneType' object has no attribute 'strip'`) behoben; jetzt None-Check, Retry-Schleife (3 Versuche), JSON-Cleaning vor dem Parsen und Validierung, dass ein JSON-Objekt zurückkommt, bevor der Fallback „Allgemein" greift

## [2.1.3] - 2026-11-09

### Behoben
- Checkpoint-Speichern bricht die Analyse nicht mehr ab: Sync-Dienste (Dropbox/OneDrive) koennen die Checkpoint-Datei kurzzeitig sperren; jetzt 3 Versuche mit Wartezeit, dann Fallback auf direktes Schreiben, im ungünstigsten Fall nur eine Log-Warnung

## [2.1.2] - 2026-11-09

### Hinzugefuegt
- Sichtbarer Grund auf der Konsole, wenn ein Checkpoint verworfen wird (geaenderte Quelldatei vs. geaenderte Konfiguration vs. unlesbare Datei) statt nur INFO im Log
- Hinweis bei Strg-C: Anzahl gesicherter Faelle und Checkpoint-Dateiname werden angezeigt (bzw. Hinweis, dass noch kein abgeschlossener Fall vorliegt)
- README: Hinweise zum Verwerfen des Checkpoints und zum Strg-C-Verhalten ergaenzt

## [2.1.1] - 2026-11-09

### Hinzugefuegt
- Checkpoint-Verwaltung (`src/checkpoint.py`): Zwischenergebnisse werden nach jedem erfolgreichen Fall gesichert ({Excel-Name}_checkpoint.json bzw. _pdf_checkpoint.json); nach Abbruch kann am letzten kompletten Fall fortgesetzt werden; Checkpoint ist an Quelldatei + Config-Hash gebunden, wird nach fehlerfreiem Lauf geloescht
- README-Abschnitt „Zwischenergebnisse und Wiederaufnahme nach Abbruch"

## [2.1.0] - 2026-11-09

### Hinzugefuegt
- `pyproject.toml` mit Console-Entry-Point: Nach `pip install -e .` steht der Befehl `qlassifai` systemweit zur Verfuegung (Start aus jedem Projektverzeichnis heraus moeglich)
- Neue Config-Parameter `sample_size` (Zufallsstichprobe) und `offset` (Faelle ueberspringen), nur via Config; Reihenfolge: erst Offset, dann Stichprobe; im Excel-Modus ueber alle Sheets gemeinsam, im PDF-Modus pro Datei; reproduzierbar ueber `scientific.seed`
- Textspaltenname (`text_column_name`) kann jetzt auch im interaktiven CLI-Dialog festgelegt werden (bisher nur via Config-Datei)
- Beim Laden einer Config ohne `text_column_name` kann dieser nachtraeglich per CLI angegeben werden (Enter = automatische Erkennung)

### Geaendert
- JSON-Reparatur abgeschnittener LLM-Antworten vor dem Retry: Offene Strings/Klammern werden geschlossen bzw. am letzten Trenner zurueckgekappt, statt sofort einen erneuten (kostenpflichtigen) API-Aufruf zu starten
- Konsolenausgabe zeigt nur noch WARNINGS und ERRORS; das vollstaendige INFO-Log geht in `qlassif-ai.log` (Fortschrittsanzeige bleibt lesbar)

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
