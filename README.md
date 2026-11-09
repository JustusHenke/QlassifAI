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

Qlassif-AI unterstuetzt **6 LLM-Provider**. Bei einer minimalen Config ohne `provider` gilt OpenAI als Standard. Für OpenRouter tragen Sie `"provider": "openrouter"` ausdrücklich ein:

| Provider | Typ | API-Key | Modellbeispiele |
|----------|-----|---------|-----------------|
| **OpenRouter** | Cloud | `OPENROUTER_API_KEY` | `google/gemini-2.0-flash-001` |
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

### Ablage und Grundregeln

Qlassif-AI sucht im beim Start ausgewählten Arbeitsverzeichnis nach einer Datei mit dem festen Namen `QlassifAI_config.json`. Legen Sie die Datei also in den Ordner mit Ihren Excel- oder PDF-Eingabedateien. Wenn keine Config gefunden wird, können Sie die Prüfmerkmale im Programm eingeben und die Konfiguration dort speichern.

Die Dateien `QlassifAI_example_config.json` und `QlassifAI_example_config_ollama.json` sind Vorlagen. Kopieren Sie eine davon in den Arbeitsordner, nennen Sie die Kopie `QlassifAI_config.json` und passen Sie die Werte an. Die API-Schlüssel gehören **nicht** in die JSON-Datei, sondern in eine `.env`-Datei oder in Umgebungsvariablen (siehe [API-Key einrichten](#api-key-einrichten)).

JSON erlaubt keine Kommentare. Achten Sie auf doppelte Anführungszeichen und darauf, nach dem letzten Element eines Objekts oder einer Liste kein Komma zu setzen.

### Kleinstmögliche gültige Config

Technisch zwingend ist eine nicht-leere Liste `check_attributes`. Jedes Prüfmerkmal muss eine Frage und einen gültigen Antworttyp haben:

```json
{
  "check_attributes": [
    {
      "question": "Wird ein konkretes Unterstützungsangebot genannt?",
      "answer_type": "boolean"
    }
  ]
}
```

Diese Config verwendet die Standardwerte `provider: "openai"` und `model: "gpt-4o-mini"` und benötigt daher einen `OPENAI_API_KEY`. Für einen anderen Provider sollten Sie `provider` und `model` ausdrücklich in der Config setzen.

### Pflichtfelder der Prüfmerkmale

| Feld | Pflicht? | Regeln |
|------|----------|--------|
| `check_attributes` | Ja | Liste mit mindestens einem Prüfmerkmal; darf nicht leer sein. |
| `question` | Ja, je Prüfmerkmal | Nicht-leere Prüffrage. Verwenden Sie möglichst eindeutige Fragen, da der Fragetext auch als Schlüssel für das Analyseergebnis dient. |
| `answer_type` | Ja, je Prüfmerkmal | Einer der exakten Werte `boolean`, `categorical` oder `multi_categorical`. |
| `categories` | Nur bei `categorical` und `multi_categorical` | Liste mit mindestens zwei Kategorien. Bei `boolean` das Feld ganz weglassen. |
| `definition` | Nein | Optionale Definition, Abgrenzung oder Kodierregel; sie gibt dem Modell zusätzlichen Kontext. |

Die Antworttypen bedeuten:

- `boolean`: Ja/Nein-Kodierung (`true` oder `false`); wenn der Text keinen Bezug zur Frage hat, kann das Ergebnis `null` sein.
- `categorical`: genau eine der angegebenen Kategorien oder `null`.
- `multi_categorical`: eine oder mehrere der angegebenen Kategorien als Liste oder `null`.

`null` ist ein möglicher Analysewert für „nicht einschlägig/kein Bezug“ und keine Config-Einstellung.

Kategorien und Fragen sollten klar und voneinander unterscheidbar formuliert sein. Wenn Sie eine Kategorie wie „Sonstiges“ wünschen, müssen Sie sie selbst in `categories` aufnehmen.

### Vollständiges Beispiel

```json
{
  "version": "2.0",
  "provider": "openrouter",
  "model": "google/gemini-2.0-flash-001",
  "text_column_name": "Textantwort",
  "research_question": "Wie bewerten Studierende die Unterstützungsangebote im ersten Semester?",
  "include_reasoning": true,
  "check_attributes": [
    {
      "question": "Wird ein konkretes Unterstützungsangebot genannt?",
      "answer_type": "boolean",
      "definition": "Als Unterstützungsangebot zählt eine benannte Einrichtung oder Maßnahme."
    },
    {
      "question": "Wie wird das Angebot bewertet?",
      "answer_type": "categorical",
      "categories": ["Positiv", "Negativ", "Gemischt", "Neutral"],
      "definition": "Bewerte die Gesamtaussage, nicht nur einzelne Wörter."
    },
    {
      "question": "Welche Themen werden angesprochen?",
      "answer_type": "multi_categorical",
      "categories": ["Studieneinstieg", "Beratung", "Lernen und Lehre", "Organisation"],
      "definition": "Mehrere Themen können gleichzeitig zutreffen."
    }
  ]
}
```

### Optionale Felder auf oberster Ebene

| Feld | Standardwert | Bedeutung |
|------|--------------|-----------|
| `version` | `"1.0"` | Optionaler Versionshinweis für die Config. |
| `provider` | `"openai"` | Einer von `openrouter`, `openai`, `anthropic`, `mistral`, `ollama` oder `lmstudio`. Für Cloud-Provider den passenden API-Key separat einrichten; Ollama und LMStudio benötigen laut Anwendung keinen API-Key. |
| `model` | `"gpt-4o-mini"` | Modellname, passend zum ausgewählten Provider. Beispiele stehen in der [Provider-Tabelle](#provider). |
| `text_column_name` | keine | Optionaler Name der Textspalte in Excel. Ohne Angabe sucht das Programm in den ersten fünf Zeilen nach üblichen Namen wie `text`, `antwort`, `answer` oder `textantwort`. Mit Angabe wird gezielt nach diesem Spaltennamen gesucht; der angegebene Name kann auch Teil der Spaltenüberschrift sein. Für PDF-Dateien ist das Feld ohne Bedeutung. |
| `research_question` | keine | Übergeordnete Forschungsfrage, die dem Modell als Kontext für alle Prüfmerkmale mitgegeben wird. |
| `include_reasoning` | `true` | Boolean. Bei `false` werden die Begründungen zu den Prüfmerkmalen weggelassen; die übrigen Analysefelder bleiben erhalten. |
| `scientific` | nicht aktiviert | Optionaler Block für Konfidenz-Ausgabe und wissenschaftliche Zusatzdateien. Details siehe unten. |

Die unterstützten Provider müssen exakt so (klein geschrieben) eingetragen werden. Das Feld `provider` ist technisch optional, wird in der Praxis aber empfohlen: Ohne Angabe gilt **OpenAI**, nicht OpenRouter.

### Optionale wissenschaftliche Einstellungen

Wenn Sie keine wissenschaftlichen Zusatzdateien oder Konfidenzspalten benötigen, lassen Sie `scientific` ganz weg. Sobald ein nicht-leerer `scientific`-Block gesetzt ist, wird der wissenschaftliche Modus aktiviert; `multi_coder` steuert darin separat den Vergleich mehrerer Modelle.

```json
"scientific": {
  "multi_coder": false,
  "confidence_threshold": 70,
  "seed": null
}
```

Fügen Sie diesen Block auf derselben Ebene wie `check_attributes` ein. Die möglichen Felder darin sind:

| Feld | Standardwert | Bedeutung |
|------|--------------|-----------|
| `multi_coder` | `false` | Bei `true` wird jede Antwort mit mehreren Modellen kodiert und verglichen. Dann sind mindestens zwei Einträge in `coder_models` erforderlich. |
| `coder_models` | `["gpt-4o-mini"]` | Modellnamen für den Multi-Coder-Modus. Verwenden Sie mindestens zwei Modelle des gewählten Providers, wenn `multi_coder` auf `true` steht. |
| `primary_coder` | `"model_1"` | Auswahl des Hauptergebnisses: `model_1` (erstes Modell in `coder_models`) oder `highest_confidence` (Modell mit der höchsten mittleren Konfidenz). Relevant bei aktiviertem Multi-Coder. |
| `confidence_threshold` | `70` | Ganze Zahl von 0 bis 100. Niedrigere Konfidenzwerte werden in der Excel-Ausgabe markiert. |
| `seed` | `null` | Optionaler ganzzahliger Wert, der im Methodenprotokoll dokumentiert wird. Er erzwingt keine identischen Ergebnisse bei späteren LLM-Aufrufen. |
| `output_dir` | – | Wird von der aktuellen Anwendung nicht zur Pfadsteuerung verwendet; das Ausgabe-Verzeichnis wird automatisch neben den Eingabedaten angelegt. Lassen Sie dieses Feld weg. |

Beispiel für aktivierten Multi-Coder-Modus:

```json
"scientific": {
  "multi_coder": true,
  "coder_models": ["gpt-4o-mini", "gpt-4o"],
  "primary_coder": "highest_confidence",
  "confidence_threshold": 70
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
