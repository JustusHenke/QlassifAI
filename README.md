# Qlassif-AI

> LLM-basiertes Analysewerkzeug fuer Excel-Dateien und PDF-Dokumente mit offenen Textantworten

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Ueberblick

Qlassif-AI analysiert automatisch Textantworten in Excel-Dateien und PDF-Dokumenten mittels Large Language Models (LLMs) und erstellt strukturierte Auswertungen.

**Features:**
- Zwei Verarbeitungsmodi: Excel-Tabellen oder PDF-Dateien
- Automatische Textanalyse: Paraphrase, Sentiment, Keywords
- Benutzerdefinierte Pruefmerkmale mit Kontext/Regeln
- Keyword-Kategorisierung via LLM
- Statistik-Generierung pro Sheet und gesamt
- Multi-Sheet-Support

## Installation

### Voraussetzungen

- Python 3.8 oder hoeher
- API-Key eines unterstuetzten Providers (siehe unten)

### Schnellstart

```bash
git clone https://github.com/JustusHenke/QlassifAi.git
cd QlassifAi
pip install -r requirements.txt
```

## Provider

Qlassif-AI unterstuetzt **6 LLM-Provider**:

| Provider | Typ | API-Key | Modellbeispiele |
|----------|-----|---------|-----------------|
| **OpenRouter** (Standard) | Cloud | `OPENROUTER_API_KEY` | `google/gemini-2.0-flash-001` |
| **OpenAI** | Cloud | `OPENAI_API_KEY` | `gpt-4o-mini`, `gpt-4o` |
| **Anthropic** | Cloud | `ANTHROPIC_API_KEY` | `claude-3-5-sonnet-20241022` |
| **Mistral** | Cloud | `MISTRAL_API_KEY` | `mistral-large-latest` |
| **Ollama** | Lokal | Keine | `llama3.1:8b`, `mistral:7b` |
| **LMStudio** | Lokal | Keine | Beliebige Modelle |

### API-Key einrichten

**Option 1: .env-Datei (empfohlen)**

```env
# OpenRouter (Standard)
OPENROUTER_API_KEY=your-api-key-here

# OpenAI
OPENAI_API_KEY=your-api-key-here

# Anthropic
ANTHROPIC_API_KEY=your-api-key-here

# Mistral
MISTRAL_API_KEY=your-api-key-here
```

**Option 2: Umgebungsvariable**

```bash
# Windows
set OPENROUTER_API_KEY=your-api-key-here

# Linux/Mac
export OPENROUTER_API_KEY=your-api-key-here
```

**Option 3: Lokale Modelle (kein API-Key noetig)**

```bash
# Ollama starten und Modell laden
ollama serve
ollama pull llama3.1:8b

# Oder LMStudio starten und Modell laden
```

### Provider-Konfiguration

```json
{
  "provider": "openrouter",
  "model": "google/gemini-2.0-flash-001"
}
```

## Konfiguration

### Config-Datei (QlassifAI_config.json)

```json
{
  "version": "2.0",
  "provider": "openrouter",
  "model": "google/gemini-2.0-flash-001",
  "text_column_name": "Textantwort",
  "research_question": "Ihre Forschungsfrage hier",
  "include_reasoning": true,
  "scientific": {
    "multi_coder": false,
    "confidence_threshold": 70,
    "seed": null
  },
  "check_attributes": [
    {
      "question": "Ihre Prueffrage?",
      "answer_type": "boolean",
      "definition": "Kontext fuer die Entscheidung"
    }
  ]
}
```

### Config-Optionen

| Option | Typ | Beschreibung |
|--------|-----|--------------|
| `provider` | string | `openrouter`, `openai`, `anthropic`, `mistral`, `ollama`, `lmstudio` |
| `model` | string | Modell-Name (provider-abhaengig) |
| `text_column_name` | string | Name der Textspalte in Excel |
| `research_question` | string | Uebergeordnete Forschungsfrage |
| `include_reasoning` | boolean | Begrueundungen generieren (default: true) |
| `scientific.multi_coder` | boolean | Multi-Model-Intercoder aktivieren |
| `scientific.confidence_threshold` | int | Schwellwert fuer niedrige Konfidenz (0-100) |
| `scientific.seed` | int | Seed fuer Reproduzierbarkeit |

### Modell-Empfehlungen

**Cloud:**
- `openrouter`: `google/gemini-2.0-flash-001` (schnell, guenstig)
- `openai`: `gpt-4o-mini` (ausgewogen)
- `anthropic`: `claude-3-5-sonnet-20241022` (hohe Qualitaet)

**Lokal:**
- `ollama`: `llama3.1:8b` (empfohlen)
- `lmstudio`: Beliebiges quantisiertes Modell

**Multi-Coder (Intercoder-Reliabilitaet):**
```json
{
  "scientific": {
    "multi_coder": true,
    "coder_models": ["gpt-4o-mini", "gpt-4o"],
    "primary_coder": "highest_confidence",
    "confidence_threshold": 70
  }
}
```

## Verwendung

```bash
python main.py
```

### Moduswahl

```
[1] Excel-Tabellen
[2] PDF-Dateien
```

### Excel-Modus

1. Verzeichnis waehlen (Enter fuer aktuelles Verzeichnis)
2. Excel-Datei auswaehlen
3. Config laden oder erstellen
4. Verarbeitung abwarten
5. Ergebnisse in `{InputDatei}_analyzed/`

### PDF-Modus

1. Verzeichnis mit PDFs waehlen
2. Config laden oder erstellen
3. Verarbeitung abwarten
4. Ergebnisse in `{Verzeichnisname}_analyzed/`

## Ausgabe

Alle Dateien werden flach in ein Ausgabeverzeichnis gespeichert:

```
{InputDateiName}_analyzed/
├── {name}_analyzed_YYYYMMDD.xlsx      # Alles in einer Datei:
│   ├── {SheetName}                    #   Analysedaten (pro Sheet)
│   ├── Statistiken                    #   Kategorie-Haeufigkeiten
│   ├── Intercoder                     #   Kodierervergleich (bei multi_coder)
│   └── Kappa-Statistik                #   Kappa-Werte (bei multi_coder)
├── methodology.md                     # Methodenprotokoll (bei scientific)
├── codebook.json                      # Maschinenlesbarer Codeplan (bei scientific)
├── frequency_tables.csv               # Fuer R/SPSS (bei scientific)
└── audit_trail_YYYYMMDD.json          # Audit Trail (bei scientific)
```

## Scientific Mode (optional)

Wissenschaftliche Parameter fuer methodische Robustheit:

```json
{
  "scientific": {
    "multi_coder": true,
    "coder_models": ["gpt-4o-mini", "gpt-4o"],
    "primary_coder": "highest_confidence",
    "confidence_threshold": 70,
    "seed": 42
  }
}
```

**Features:**
- **Confidence Scores**: Konfidenz pro Klassifikation (0-100%)
- **Multi-Model-Intercoder**: Kodierervergleich mit Kappa-Berechnung
- **Reproduzierbarkeit**: methodology.md, codebook.json, Audit Trail

## Fehlerbehandlung

| Fehler | Loesung |
|--------|---------|
| `API-Key nicht gefunden` | `.env`-Datei erstellen oder Umgebungsvariable setzen |
| `Keine kompatiblen Sheets` | Spaltenname in Config anpassen (`text_column_name`) |
| `API-Timeout` | Internetverbindung pruefen, erneut versuchen |
| `anthropic nicht installiert` | `pip install anthropic` ausfuehren |
| `mistralai nicht installiert` | `pip install mistralai` ausfuehren |

## Tests

```bash
# Alle Tests ausfuehren
python tests/test_confidence_engine.py
python tests/test_kappa_calculator.py
python tests/test_multi_coder.py
python tests/test_reproducibility.py
python tests/test_config_backwards_compat.py
python tests/test_scientific_workflow.py
```

## Lizenz

MIT License
