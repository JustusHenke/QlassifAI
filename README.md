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

Qlassif-AI unterstuetzt **6 LLM-Provider** fuer maximale Flexibilitaet:

### Cloud-Provider

| Provider | API-Key | Modellbeispiele | Kosten |
|----------|---------|-----------------|--------|
| **OpenRouter** (Standard) | `OPENROUTER_API_KEY` | `google/gemini-2.0-flash-001`, `anthropic/claude-3.5-sonnet` | Variabel |
| **OpenAI** | `OPENAI_API_KEY` | `gpt-4o-mini`, `gpt-4o`, `gpt-3.5-turbo` | Variabel |
| **Anthropic** | `ANTHROPIC_API_KEY` | `claude-3-5-sonnet-20241022`, `claude-3-haiku-20240307` | Variabel |
| **Mistral** | `MISTRAL_API_KEY` | `mistral-large-latest`, `mistral-small-latest` | Variabel |

### Lokale Provider

| Provider | API-Key | Modellbeispiele | Kosten |
|----------|---------|-----------------|--------|
| **Ollama** | Keiner noetig | `llama3.1:8b`, `mistral:7b`, `phi3` | Kostenlos |
| **LMStudio** | Keiner noetig | Beliebige lokal geladene Modelle | Kostenlos |

### Provider-Übersicht

| Provider | Provider-Wert | Base URL | Authentifizierung |
|----------|---------------|----------|-------------------|
| OpenRouter | `openrouter` | `https://openrouter.ai/api/v1` | API-Key |
| OpenAI | `openai` | `https://api.openai.com/v1` | API-Key |
| Anthropic | `anthropic` | Anthropic SDK | API-Key |
| Mistral | `mistral` | Mistral SDK | API-Key |
| Ollama | `ollama` | `http://localhost:11434/v1` | Keine |
| LMStudio | `lmstudio` | `http://localhost:1234/v1` | Keine |

## Konfiguration

### API-Key einrichten

**Option 1: .env-Datei (empfohlen)**

Erstellen Sie eine `.env`-Datei im Projektverzeichnis:

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
# Ollama starten
ollama serve
ollama pull llama3.1:8b

# Oder LMStudio starten und Modell laden
```

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

**Fuer beste Ergebnisse:**
- `openrouter`: `google/gemini-2.0-flash-001` (schnell, guenstig)
- `openai`: `gpt-4o-mini` (ausgewogen)
- `anthropic`: `claude-3-5-sonnet-20241022` (hohe Qualitaet)

**Fuer lokale Nutzung:**
- `ollama`: `llama3.1:8b` (empfohlen), `mistral:7b`
- `lmstudio`: Beliebiges quantisiertes Modell

**Fuer Multi-Coder (Intercoder-Reliabilitaet):**
```json
{
  "scientific": {
    "multi_coder": true,
    "coder_models": ["openrouter/openai/gpt-4o-mini", "openrouter/anthropic/claude-3.5-sonnet"]
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
5. Ergebnisse in `*_analyzed.xlsx`

### PDF-Modus

1. Verzeichnis mit PDFs waehlen
2. Config laden oder erstellen
3. Verarbeitung abwarten
4. Ergebnisse in `*_analyzed.xlsx`

## Ausgabe

### Excel-Modus

- `*_analyzed.xlsx` - Originaldaten + Analyseergebnisse
- `*_statistics.xlsx` - Statistiken pro Sheet und gesamt

### Scientific Mode (optional)

Wenn `scientific` in der Config aktiviert ist:

- `analyzed/` - Analysedateien
- `reproducibility/methodology.md` - Methodenprotokoll
- `reproducibility/codebook.json` - Maschinenlesbarer Codeplan
- `reproducibility/frequency_tables.csv` - Fuer R/SPSS
- `audit_trail/` - Audit Trail JSONs
- `intercoder/` - Intercoder-Vergleich (bei multi_coder)

## Fehlerbehandlung

| Fehler | Loesung |
|--------|---------|
| `API-Key nicht gefunden` | `.env`-Datei erstellen oder Umgebungsvariable setzen |
| `Keine kompatiblen Sheets` | Spaltenname in Config anpassen (`text_column_name`) |
| `API-Timeout` | Internetverbindung pruefen, erneut versuchen |
| `anthropic nicht installiert` | `pip install anthropic` ausfuehren |
| `mistralai nicht installiert` | `pip install mistralai` ausfuehren |

## Logging

Alle Aktivitaeten werden in `qlassif-ai.log` protokolliert.

## Lizenz

MIT License
