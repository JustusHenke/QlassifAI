# 🔍 Qlassif-AI

> LLM-basiertes Analysewerkzeug für Excel-Dateien und PDF-Dokumente mit offenen Textantworten

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-green.svg)](https://openai.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📋 Überblick

Qlassif*AI* analysiert automatisch Textantworten in Excel-Dateien und PDF-Dokumenten mittels Large Language Models (LLMs) und erstellt strukturierte Auswertungen. Das Tool unterstützt:

- 📊 **Zwei Verarbeitungsmodi**: Excel-Tabellen oder PDF-Dateien
- ✨ **Automatische Textanalyse**: Paraphrase, Sentiment mit Begründung, Keywords
- 🎯 **Benutzerdefinierte Prüfmerkmale**: Eigene Klassifikationsfragen mit Kontext/Regeln
- 📊 **Keyword-Kategorisierung**: Automatische thematische Gruppierung
- 📈 **Statistik-Generierung**: Übersichtliche Auswertungen pro Sheet und gesamt
- 🎨 **Professionelles Design**: Bläuliches Theme für Output-Tabellen
- 🔄 **Multi-Sheet-Support**: Verarbeitung mehrerer Sheets in einer Datei
- 📄 **PDF-Verarbeitung**: Intelligente Chunking-Strategie für große Dokumente

## 🚀 Installation

### Voraussetzungen

- Python 3.8 oder höher
- API-Key von [OpenAI](https://platform.openai.com/api-keys) oder [OpenRouter](https://openrouter.ai/keys)

### Schnellstart

```bash
# Repository klonen
git clone https://github.com/JustusHenke/QlassifAi.git
cd QlassifAi

# Abhängigkeiten installieren
pip install -r requirements.txt

# API-Key konfigurieren
echo "OPENAI_API_KEY=your-api-key-here" > .env

# Programm starten
python main.py
```

## ⚙️ Konfiguration

### API-Key einrichten

**Option 1: .env-Datei (empfohlen)**

Erstellen Sie eine `.env`-Datei im Projektverzeichnis:

**Für OpenAI:**
```env
OPENAI_API_KEY=your-api-key-here
```

**Für OpenRouter:**
```env
OPENROUTER_API_KEY=your-api-key-here
```

**Option 2: Umgebungsvariable**

```bash
# Windows (OpenAI)
set OPENAI_API_KEY=your-api-key-here

# Windows (OpenRouter)
set OPENROUTER_API_KEY=your-api-key-here

# Linux/Mac (OpenAI)
export OPENAI_API_KEY=your-api-key-here

# Linux/Mac (OpenRouter)
export OPENROUTER_API_KEY=your-api-key-here
```

### Prüfmerkmale konfigurieren

Erstellen Sie eine `QlassifAI_config.json` im Arbeitsverzeichnis:

```json
{
  "version": "1.0",
  "provider": "openai",
  "model": "gpt-4o-mini",
  "text_column_name": "Textantwort",
  "research_question": "Wie bewerten Studierende die Unterstützungsangebote im ersten Semester?",
  "check_attributes": [
    {
      "question": "Wird über Wettbewerb gesprochen?",
      "answer_type": "boolean",
      "definition": "Wettbewerb bedeutet Vergleich mit anderen Anbietern, Konkurrenten oder Alternativen."
    },
    {
      "question": "Welche Produktkategorie wird erwähnt?",
      "answer_type": "categorical",
      "categories": ["Hardware", "Software", "Service", "Keine"],
      "definition": "Hardware = physische Geräte; Software = Programme/Apps; Service = Dienstleistungen"
    },
    {
      "question": "Welche Themen werden angesprochen?",
      "answer_type": "multi_categorical",
      "categories": ["Preis", "Qualität", "Support"],
      "definition": "Mehrere Themen können gleichzeitig vorkommen"
    }
  ]
}
```

#### 📝 Konfigurationsoptionen

| Option | Typ | Beschreibung | Beispiel |
|--------|-----|--------------|----------|
| `version` | string | Konfigurationsversion | `"1.0"` |
| `provider` | string | LLM-Provider | `"openai"`, `"openrouter"` |
| `model` | string | Modell-Name | `"gpt-4o-mini"`, `"anthropic/claude-3.5-sonnet"` |
| `text_column_name` | string (optional) | Name der Textspalte | `"Textantwort"`, `"text"` |
| `research_question` | string (optional) | Übergeordnete Untersuchungsfrage für Kontext | `"Wie bewerten Studierende...?"` |
| `include_reasoning` | boolean (optional) | Ob Begründungen für Prüfmerkmale generiert werden (default: true) | `true`, `false` |
| `check_attributes` | array | Liste der Prüfmerkmale | siehe unten |

> **💡 Neu**: Mit `research_question` können Sie eine übergeordnete Forschungsfrage definieren, die zusätzlichen Kontext für alle Prüfmerkmale liefert. Dies hilft dem LLM, die Prüffragen im richtigen Zusammenhang zu bewerten.

> **💡 Performance-Tipp**: Setzen Sie `include_reasoning` auf `false`, um Begründungsspalten zu deaktivieren. Dies reduziert die Token-Nutzung und beschleunigt die Analyse, wenn Sie nur die Klassifikationsergebnisse benötigen.

#### 🎯 Prüfmerkmal-Typen

**Boolean (Ja/Nein)**
```json
{
  "question": "Ist die Aussage zukunftsorientiert?",
  "answer_type": "boolean",
  "definition": "Zukunftsorientiert = Bezug auf zukünftige Entwicklungen oder Pläne"
}
```

**Categorical (Eine Kategorie)**
```json
{
  "question": "Welche Emotion wird ausgedrückt?",
  "answer_type": "categorical",
  "categories": ["Freude", "Ärger", "Trauer", "Neutral"],
  "definition": "Emotion basierend auf Wortwahl und Kontext"
}
```

**Multi-Categorical (Mehrere Kategorien gleichzeitig)**
```json
{
  "question": "Welche Themen werden angesprochen?",
  "answer_type": "multi_categorical",
  "categories": ["Preis", "Qualität", "Support", "Innovation"],
  "definition": "Mehrere Themen können gleichzeitig im Text vorkommen"
}
```

## 💻 Verwendung

### Moduswahl

Beim Start wählen Sie zwischen zwei Verarbeitungsmodi:

```bash
python main.py

============================================================
Qlassif-AI - Moduswahl
============================================================

Sollen Excel-Tabellen oder PDF-Dateien ausgewertet werden?
  [1] Excel-Tabellen
  [2] PDF-Dateien

Bitte wählen Sie (1 oder 2):
```

### 📊 Excel-Modus

Analysiert Textantworten in Excel-Tabellen zeilenweise.

**Schritt-für-Schritt:**

1. **📁 Verzeichnisauswahl**: Geben Sie den Ordner mit der Excel-Datei an (Enter für aktuelles Verzeichnis)
2. **📄 Dateiauswahl**: Wählen Sie eine Excel-Datei aus dem Verzeichnis
3. **⚙️ Konfiguration**: Laden Sie eine existierende Config oder erstellen Sie neue Prüfmerkmale
4. **🔄 Verarbeitung**: Das Tool analysiert alle Textantworten (mit Fortschrittsanzeige)
5. **✅ Ausgabe**: Ergebnisse werden im selben Verzeichnis gespeichert

### 📄 PDF-Modus

Analysiert PDF-Dokumente als Ganzes mit intelligenter Chunking-Strategie.

**Schritt-für-Schritt:**

1. **📁 Verzeichnisauswahl**: Geben Sie den Ordner mit PDF-Dateien an (Enter für aktuelles Verzeichnis)
2. **📄 Dateiauswahl**: Das Tool findet automatisch alle PDFs im Verzeichnis
3. **⚙️ Konfiguration**: Laden Sie eine existierende Config oder erstellen Sie neue Prüfmerkmale
4. **🔄 Verarbeitung**: 
   - PDFs werden in Chunks aufgeteilt (max. 15.000 Zeichen)
   - Jeder Chunk wird einzeln analysiert
   - Ergebnisse werden pro PDF zusammengeführt
5. **✅ Ausgabe**: Eine Excel-Datei mit allen PDF-Analysen wird erstellt

**PDF-Besonderheiten:**
- Große PDFs werden automatisch in handhabbare Chunks aufgeteilt
- Sentiment wird über alle Chunks gemittelt (-1 = negativ, 0 = gemischt, 1 = positiv)
- Keywords werden dedupliziert und auf die häufigsten 4 reduziert
- Prüfmerkmale werden über Mehrheitsentscheidung zusammengeführt

### Excel-Datei-Format (Excel-Modus)

Ihre Excel-Datei muss eine Spalte mit einem der folgenden Namen enthalten:
- `text`
- `Antwort`
- `answer`
- `Textantwort`
- Oder einen benutzerdefinierten Namen in der Config (`text_column_name`)

**Beispiel:**

| Kategorie | Textantwort | Zeichen |
|-----------|-------------|---------|
| Alle | Das Stipendium hilft mir sehr bei der Finanzierung... | 150 |
| Alle | Ich bin sehr zufrieden mit der Betreuung... | 120 |

> **💡 Tipp**: Das Tool ignoriert automatisch gefilterte/versteckte Zeilen in Excel!

## 📊 Ausgabe

### Excel-Modus

Das Tool erstellt zwei Excel-Dateien im selben Verzeichnis wie die Eingabedatei:

### 1. 📋 Analysierte Datei (`*_analyzed.xlsx`)

Enthält die Originaldaten plus neue Spalten mit **bläulichem Theme**:

| Spalte | Beschreibung | Beispiel |
|--------|--------------|----------|
| **Paraphrase** | Kompakte Umformulierung (max. 1-2 Sätze) | "Stipendium ermöglicht Studienfinanzierung" |
| **Sentiment** | Stimmung der Aussage | "positiv", "negativ", "gemischt" |
| **Sentiment_Begründung** | Grund für Sentiment (max. 30 Wörter) | "Positive Wortwahl wie 'hilft sehr' und 'zufrieden'" |
| **Keywords** | 2-4 extrahierte Schlüsselwörter | "Stipendium, Finanzierung, Studium" |
| **[Prüfmerkmale]** | Antworten auf benutzerdefinierte Fragen | "Ja", "Nein", Kategorie, oder "nicht kodiert" |
| **Keyword_Kategorie** | Automatisch zugeordnete Themen | "Finanzierung, Unterstützung" |

> **✨ Neu**: Boolean-Werte werden als "Ja"/"Nein" angezeigt. Wenn kein Bezug zum Thema besteht, wird "nicht kodiert" angezeigt.

### 2. 📈 Statistik-Datei (`*_statistics.xlsx`)

Enthält Auswertungen **pro Sheet und gesamt**:

**Pro Sheet:**
```
Sheet: Fragebogen_2024
┌─────────────────┬────────────┬──────────────────────┐
│ Kategorie       │ Häufigkeit │ Keywords             │
├─────────────────┼────────────┼──────────────────────┤
│ Finanzierung    │ 45         │ Stipendium, Geld...  │
│ Betreuung       │ 32         │ Mentor, Hilfe...     │
└─────────────────┴────────────┴──────────────────────┘
```

**Zusammen (Gesamt):**
```
Zusammen
┌─────────────────┬────────────┬──────────────────────┐
│ Kategorie       │ Häufigkeit │ Keywords             │
├─────────────────┼────────────┼──────────────────────┤
│ Finanzierung    │ 89         │ Stipendium, Geld...  │
│ Betreuung       │ 67         │ Mentor, Hilfe...     │
└─────────────────┴────────────┴──────────────────────┘
```

### PDF-Modus

Das Tool erstellt eine Excel-Datei mit zwei Sheets:

#### 1. 📋 Analyseergebnisse (`*_analyzed.xlsx`)

Enthält eine Zeile pro PDF-Dokument mit **bläulichem Theme**:

| Spalte | Beschreibung | Beispiel |
|--------|--------------|----------|
| **Dateiname** | Name der PDF-Datei | "Dokument_01.pdf" |
| **Paraphrase** | Zusammenfassung des gesamten Dokuments | "Bericht über Projektfortschritt..." |
| **Sentiment** | Stimmung des Dokuments | "positiv", "negativ", "gemischt" |
| **Sentiment_Begründung** | Grund für Sentiment | "Überwiegend positive Formulierungen" |
| **Keywords** | 4 wichtigste Keywords | "Projekt, Erfolg, Team, Innovation" |
| **[Prüfmerkmale]** | Antworten auf benutzerdefinierte Fragen | "Ja", "Nein", Kategorie, oder "nicht kodiert" |
| **Keyword_Kategorie** | Automatisch zugeordnete Themen | "Projektmanagement, Innovation" |
| **Chunk_Anzahl** | Anzahl der analysierten Chunks | 3 |

#### 2. 📈 Statistik-Sheet

Enthält Auswertungen über alle PDFs:

```
PDF-Analyse Statistiken
┌─────────────────┬────────────┬──────────────────────┐
│ Kategorie       │ Häufigkeit │ Keywords             │
├─────────────────┼────────────┼──────────────────────┤
│ Innovation      │ 12         │ Projekt, Idee...     │
│ Qualität        │ 8          │ Standard, Test...    │
└─────────────────┴────────────┴──────────────────────┘
```

## 🎯 Features im Detail

### ✨ Intelligente Textanalyse
- **Kompakte Paraphrase**: Kernaussage in 1-2 Sätzen
- **Sentiment mit Begründung**: Stimmungsanalyse mit Erklärung (max. 30 Wörter)
- **Keyword-Extraktion**: 2-4 relevante Schlüsselwörter pro Text
- **Thematische Kategorisierung**: Automatische Gruppierung ähnlicher Keywords

### 📊 Zwei Verarbeitungsmodi
- **Excel-Modus**: Zeilenweise Analyse von Textantworten in Tabellen
- **PDF-Modus**: Dokumentenweise Analyse mit intelligenter Chunking-Strategie
- **Automatische Erkennung**: Wählen Sie beim Start den passenden Modus

### 🎨 Professionelle Ausgabe
- **Bläuliches Theme**: Ansprechende Formatierung der Output-Tabellen
- **Autofilter**: Aktiviert für einfaches Filtern und Sortieren
- **Multi-Sheet-Support**: Verarbeitung mehrerer Sheets in einer Datei (Excel-Modus)
- **Separate Statistiken**: Pro Sheet und Gesamt-Übersicht

### 🔧 Flexible Konfiguration
- **Benutzerdefinierte Prüfmerkmale**: Boolean, kategoriale oder multi-kategoriale Fragen
- **Kontext/Regeln**: Definition für präzisere Klassifikation
- **Multi-Provider-Support**: OpenAI oder OpenRouter
- **Modellauswahl**: Wählen Sie zwischen verschiedenen LLM-Modellen
- **Anpassbare Spaltennamen**: Konfigurierbare Textspalte (Excel-Modus)

### 🚀 Benutzerfreundlich
- **Interaktive Dialoge**: Schritt-für-Schritt-Anleitung
- **Fortschrittsanzeige**: Echtzeit-Feedback während der Verarbeitung
- **Fehlerbehandlung**: Automatische Wiederholungsversuche bei API-Fehlern
- **Detailliertes Logging**: Vollständige Protokollierung in `qlassif-ai.log`

## 📁 Projektstruktur

```
qlassif-ai/
├── 📄 main.py                          # Hauptprogramm
├── 📋 requirements.txt                 # Python-Abhängigkeiten
├── 📝 README.md                        # Diese Datei
├── ⚙️ QlassifAI_example_config.json   # Beispiel-Konfiguration
├── 📂 src/                             # Quellcode
│   ├── environment_manager.py          # API-Key Management
│   ├── file_discovery.py               # Dateiauswahl
│   ├── excel_loader.py                 # Excel-Import
│   ├── config_manager.py               # Konfigurationsverwaltung
│   ├── llm_analyzer.py                 # LLM-Analyse
│   ├── keyword_categorizer.py          # Keyword-Kategorisierung
│   ├── excel_writer.py                 # Excel-Export mit Theme
│   ├── statistics_generator.py         # Statistik-Generierung
│   ├── models.py                       # Datenmodelle
│   └── logging_config.py               # Logging-Setup
└── 📊 Sample-Dateien/                  # Beispiel-Daten
    ├── Beispielantworten.xlsx
    └── Sample_Erstsemester_Unterstuetzung.xlsx
```

## ⚠️ Fehlerbehandlung

### Häufige Fehler und Lösungen

| Fehler | Ursache | Lösung |
|--------|---------|--------|
| `OPENAI_API_KEY nicht gefunden` | API-Key nicht konfiguriert | Erstellen Sie eine `.env`-Datei oder setzen Sie die Umgebungsvariable |
| `Keine kompatiblen Sheets gefunden` | Falsche Spaltennamen (Excel-Modus) | Stellen Sie sicher, dass eine Spalte "text", "Antwort", "answer" oder "Textantwort" heißt, oder konfigurieren Sie `text_column_name` |
| `Keine PDF-Dateien gefunden` | Falsches Verzeichnis (PDF-Modus) | Stellen Sie sicher, dass PDF-Dateien im angegebenen Verzeichnis liegen |
| `API-Timeout` | Netzwerkprobleme | Das Tool versucht automatisch mehrmals. Prüfen Sie Ihre Internetverbindung |
| `Rate Limit Error` | Zu viele API-Anfragen | Warten Sie kurz und versuchen Sie es erneut |

### 📝 Logging

Alle Aktivitäten werden in `qlassif-ai.log` protokolliert:
- ✅ Verarbeitungsschritte
- ⚠️ Warnungen
- ❌ Fehler und Stack Traces
- 🔄 API-Aufrufe und Antworten

## 💰 Kosten

Das Tool unterstützt **OpenAI** und **OpenRouter** als LLM-Provider.

### OpenAI (Standard)

Standardmäßig verwendet das Tool **GPT-4o-mini** für optimale Kosten-Nutzen-Balance.

| Anzahl Textantworten | Geschätzte Kosten (USD) |
|---------------------|------------------------|
| 100 | $0.01 - $0.05 |
| 500 | $0.05 - $0.25 |
| 1000 | $0.10 - $0.50 |

### OpenRouter

OpenRouter bietet Zugang zu verschiedenen Modellen mit unterschiedlichen Preisen:

| Modell | Beispiel | Kosten |
|--------|----------|--------|
| GPT-4o-mini | `openai/gpt-4o-mini` | 💰 |
| Claude 3.5 Sonnet | `anthropic/claude-3.5-sonnet` | 💰💰💰 |
| Llama 3.1 70B | `meta-llama/llama-3.1-70b-instruct` | 💰💰 |

> **💡 Tipp**: Die tatsächlichen Kosten hängen von der Textlänge und Anzahl der Prüfmerkmale ab.

### Modellvergleich (OpenAI)

| Modell | Geschwindigkeit | Qualität | Kosten |
|--------|----------------|----------|--------|
| `gpt-4o-mini` | ⚡⚡⚡ | ⭐⭐⭐ | 💰 |
| `gpt-4` | ⚡ | ⭐⭐⭐⭐⭐ | 💰💰💰💰 |
| `gpt-3.5-turbo` | ⚡⚡⚡⚡ | ⭐⭐ | 💰 |

## 🛠️ Entwicklung

### Neue Prüfmerkmale hinzufügen

**Option 1: Config-Datei bearbeiten**
```json
{
  "check_attributes": [
    {
      "question": "Neue Frage?",
      "answer_type": "boolean",
      "definition": "Kontext für die Entscheidung"
    }
  ]
}
```

**Option 2: Interaktiv beim Start**
```
Prüffrage (oder Enter zum Beenden): Ist die Aussage zukunftsorientiert?
Antworttyp:
  1. Boolean (Ja/Nein)
  2. Kategorial (mehrere Kategorien)
Wählen Sie (1 oder 2): 1
Definition/Regeln (optional, Enter zum Überspringen): Bezug auf zukünftige Entwicklungen
✓ Boolean-Prüfmerkmal hinzugefügt
```

### Modell ändern

Bearbeiten Sie das `model`-Feld in `QlassifAI_config.json`:
```json
{
  "model": "gpt-4"  // oder "gpt-3.5-turbo", "gpt-4o-mini"
}
```

## 📚 Beispiele

### Beispiel 1: Schnellstart

```bash
# Programm starten
python main.py

# Interaktive Schritte:
# 1. Enter drücken (aktuelles Verzeichnis)
# 2. Beispielantworten.xlsx auswählen
# 3. QlassifAI_config.json laden
# 4. Warten auf Verarbeitung
# 5. Ergebnisse prüfen:
#    - Beispielantworten_analyzed.xlsx
#    - Beispielantworten_statistics.xlsx
```

### Beispiel 2: Eigene Konfiguration

```bash
# 1. Config erstellen
cat > QlassifAI_config.json << EOF
{
  "version": "1.0",
  "model": "gpt-4o-mini",
  "text_column_name": "Feedback",
  "research_question": "Wie zufrieden sind Kunden mit unserem Service?",
  "check_attributes": [
    {
      "question": "Enthält konstruktive Kritik?",
      "answer_type": "boolean",
      "definition": "Konstruktiv = konkrete Verbesserungsvorschläge"
    }
  ]
}
EOF

# 2. Programm starten
python main.py
```


## 📄 Lizenz

Dieses Projekt ist unter der MIT-Lizenz lizenziert.

## 🆘 Support

Bei Fragen oder Problemen:

1. 📋 Prüfen Sie die Log-Datei `qlassif-ai.log`
2. 📦 Stellen Sie sicher, dass alle Abhängigkeiten installiert sind: `pip install -r requirements.txt`
3. 🔑 Verifizieren Sie Ihren OpenAI API-Key
4. 📖 Konsultieren Sie die [OpenAI API-Dokumentation](https://platform.openai.com/docs)
5. 🐛 Erstellen Sie ein Issue auf GitHub

---

**Entwickelt mit ❤️ und Spec-Driven Development**
