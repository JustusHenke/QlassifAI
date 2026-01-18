# Requirements Document

## Introduction

Qlassif-AI ist ein LLM-basiertes Analysewerkzeug, das Excel-Dateien mit offenen Textantworten einliest, diese automatisch klassifiziert und die Ergebnisse strukturiert in die Excel-Datei zurückschreibt. Das Tool unterstützt mehrere Sheets, konfigurierbare Prüfmerkmale und automatische Keyword-Kategorisierung.

## Glossary

- **System**: Qlassif-AI
- **LLM**: Large Language Model (z.B. GPT-4, Claude)
- **Sheet**: Ein einzelnes Arbeitsblatt innerhalb einer Excel-Datei
- **Kopfspalte**: Die erste Zeile eines Sheets mit Spaltenüberschriften
- **Textspalte**: Eine Spalte mit der Überschrift "text", "Antwort" oder "answer"
- **Prüfmerkmal**: Eine benutzerdefinierte Klassifikationsfrage (z.B. "Wird über Wettbewerb gesprochen?")
- **Config_File**: JSON-Datei zur Speicherung von benutzerdefinierten Prüfmerkmalen
- **Keyword_Kategorie**: Übergeordnete Gruppierung von ähnlichen Keywords

## Requirements

### Requirement 1: Dateiauswahl und -verarbeitung

**User Story:** Als Benutzer möchte ich Excel-Dateien aus einem Verzeichnis auswählen können, damit ich die zu analysierenden Daten einfach laden kann.

#### Acceptance Criteria

1. WHEN das System startet, THEN THE System SHALL das aktuelle Verzeichnis nach Excel-Dateien durchsuchen
2. WHEN Excel-Dateien gefunden werden, THEN THE System SHALL eine Auswahlliste mit allen gefundenen Dateien anzeigen
3. WHEN der Benutzer eine Datei auswählt, THEN THE System SHALL die Datei laden und alle Sheets analysieren
4. WHEN ein Sheet eine Kopfspalte mit "text", "Antwort" oder "answer" enthält, THEN THE System SHALL dieses Sheet als kompatibel markieren
5. WHEN keine kompatiblen Sheets gefunden werden, THEN THE System SHALL eine Fehlermeldung anzeigen

### Requirement 2: Textdaten-Identifikation

**User Story:** Als Benutzer möchte ich, dass das System automatisch die relevanten Textspalten findet, damit ich nicht manuell konfigurieren muss.

#### Acceptance Criteria

1. WHEN ein Sheet geladen wird, THEN THE System SHALL die Kopfzeile nach Spalten mit den Namen "text", "Antwort" oder "answer" durchsuchen
2. WHEN eine Textspalte gefunden wird, THEN THE System SHALL alle nicht-leeren Zeilen unter dieser Spalte als zu analysierende Einträge markieren
3. WHEN mehrere kompatible Spalten in einem Sheet existieren, THEN THE System SHALL die erste gefundene Spalte verwenden
4. WHEN die Kopfzeile nicht in der ersten Zeile ist, THEN THE System SHALL die ersten 5 Zeilen durchsuchen

### Requirement 3: LLM-basierte Textanalyse

**User Story:** Als Benutzer möchte ich, dass jede Textantwort automatisch analysiert wird, damit ich strukturierte Insights erhalte.

#### Acceptance Criteria

1. WHEN eine Textantwort verarbeitet wird, THEN THE System SHALL eine Paraphrase der Aussage generieren
2. WHEN eine Textantwort verarbeitet wird, THEN THE System SHALL das Sentiment als "positiv", "negativ" oder "gemischt" klassifizieren
3. WHEN eine Textantwort verarbeitet wird, THEN THE System SHALL 2-4 Keywords extrahieren, die textnah aber leicht abstrahiert sind
4. WHEN alle Standardanalysen abgeschlossen sind, THEN THE System SHALL die Ergebnisse in separaten Spalten rechts der Textspalte speichern
5. WHEN ein LLM-API-Fehler auftritt, THEN THE System SHALL den Fehler protokollieren und mit der nächsten Zeile fortfahren
6. WHEN das System LLM-API-Aufrufe durchführt, THEN THE System SHALL OpenAI GPT-4 oder kompatible Modelle verwenden
7. WHEN das System mit dem LLM kommuniziert, THEN THE System SHALL einen HTTP-Client mit 60 Sekunden Timeout verwenden
8. WHEN das System API-Aufrufe durchführt, THEN THE System SHALL den API-Key aus Umgebungsvariablen laden

### Requirement 4: Konfigurierbare Prüfmerkmale

**User Story:** Als Benutzer möchte ich eigene Prüfmerkmale definieren können, damit ich spezifische Aspekte der Textantworten untersuchen kann.

#### Acceptance Criteria

1. WHEN das System startet, THEN THE System SHALL nach einer Config_File im aktuellen Verzeichnis suchen
2. WHEN eine Config_File gefunden wird, THEN THE System SHALL dem Benutzer anbieten, diese zu laden
3. WHEN keine Config_File existiert oder der Benutzer keine laden möchte, THEN THE System SHALL einen Dialog zur Definition neuer Prüfmerkmale starten
4. WHEN der Benutzer ein Prüfmerkmal definiert, THEN THE System SHALL die Prüffrage und den Antworttyp (boolean oder kategorial) speichern
5. WHEN der Benutzer keine weiteren Prüfmerkmale hinzufügen möchte, THEN THE System SHALL die Konfiguration in einer JSON-Datei speichern
6. WHEN ein Prüfmerkmal vom Typ boolean ist, THEN THE System SHALL für jede Textantwort "true" oder "false" zurückgeben
7. WHEN ein Prüfmerkmal vom Typ kategorial ist, THEN THE System SHALL für jede Textantwort eine der vordefinierten Kategorien zurückgeben

### Requirement 5: Config-File-Verwaltung

**User Story:** Als Benutzer möchte ich Prüfmerkmale speichern und wiederverwenden können, damit ich nicht jedes Mal neu konfigurieren muss.

#### Acceptance Criteria

1. WHEN Prüfmerkmale definiert werden, THEN THE System SHALL diese in einer JSON-Datei mit strukturiertem Format speichern
2. WHEN eine Config_File geladen wird, THEN THE System SHALL alle Prüfmerkmale aus der Datei extrahieren
3. WHEN eine Config_File ungültig ist, THEN THE System SHALL eine Fehlermeldung anzeigen und zur manuellen Definition wechseln
4. WHEN der Benutzer die Config_File bearbeiten möchte, THEN THE System SHALL den Pfad zur Datei anzeigen

### Requirement 6: Keyword-Kategorisierung

**User Story:** Als Benutzer möchte ich, dass Keywords automatisch in Überkategorien gruppiert werden, damit ich thematische Cluster erkenne.

#### Acceptance Criteria

1. WHEN alle Textantworten verarbeitet sind, THEN THE System SHALL alle extrahierten Keywords sammeln
2. WHEN alle Keywords gesammelt sind, THEN THE System SHALL mittels LLM Überkategorien entwickeln, die ähnliche Keywords gruppieren
3. WHEN Überkategorien erstellt sind, THEN THE System SHALL jeder Textantwort basierend auf ihren Keywords eine oder mehrere Kategorien zuordnen
4. WHEN Kategorien zugeordnet sind, THEN THE System SHALL diese in einer neuen Spalte "Keyword_Kategorie" speichern
5. WHEN keine Keywords für eine Antwort existieren, THEN THE System SHALL die Kategorie als "Keine" markieren

### Requirement 7: Excel-Ausgabe

**User Story:** Als Benutzer möchte ich, dass die Analyseergebnisse strukturiert in die Excel-Datei geschrieben werden, damit ich sie weiterverarbeiten kann.

#### Acceptance Criteria

1. WHEN Analyseergebnisse vorliegen, THEN THE System SHALL neue Spalten rechts der Textspalte erstellen
2. WHEN neue Spalten erstellt werden, THEN THE System SHALL diese mit "Paraphrase", "Sentiment", "Keywords" und den Namen der Prüfmerkmale benennen
3. WHEN alle Analysen abgeschlossen sind, THEN THE System SHALL die Spalte "Keyword_Kategorie" hinzufügen
4. WHEN die Excel-Datei gespeichert wird, THEN THE System SHALL die ursprüngliche Datei überschreiben oder eine neue Datei mit Suffix erstellen
5. WHEN mehrere Sheets verarbeitet werden, THEN THE System SHALL alle kompatiblen Sheets mit Ergebnissen aktualisieren

### Requirement 8: Fehlerbehandlung und Logging

**User Story:** Als Benutzer möchte ich informiert werden, wenn Fehler auftreten, damit ich Probleme nachvollziehen kann.

#### Acceptance Criteria

1. WHEN ein Fehler beim Laden der Excel-Datei auftritt, THEN THE System SHALL eine aussagekräftige Fehlermeldung anzeigen
2. WHEN ein LLM-API-Aufruf fehlschlägt, THEN THE System SHALL den Fehler protokollieren und mit der Verarbeitung fortfahren
3. WHEN die Verarbeitung abgeschlossen ist, THEN THE System SHALL eine Zusammenfassung mit Anzahl verarbeiteter Zeilen und Fehlern anzeigen
4. WHEN kritische Fehler auftreten, THEN THE System SHALL die Verarbeitung stoppen und den Benutzer informieren

### Requirement 10: Kategorie-Auswertung

**User Story:** Als Benutzer möchte ich eine Übersicht über die Häufigkeit der Kategorien und zugehörigen Keywords erhalten, damit ich Trends und Muster schnell erkennen kann.

#### Acceptance Criteria

1. WHEN alle Textantworten kategorisiert sind, THEN THE System SHALL die Häufigkeit jeder Keyword_Kategorie berechnen
2. WHEN Kategorie-Häufigkeiten berechnet sind, THEN THE System SHALL für jede Kategorie alle zugehörigen Keywords sammeln
3. WHEN die Auswertung abgeschlossen ist, THEN THE System SHALL eine separate Excel-Datei mit Kategorie-Statistiken erstellen
4. WHEN die Auswertungs-Excel erstellt wird, THEN THE System SHALL Spalten für "Kategorie", "Häufigkeit" und "Keywords" enthalten
5. WHEN Keywords für eine Kategorie gesammelt werden, THEN THE System SHALL diese deduplizieren und kommagetrennt darstellen
6. WHEN die Auswertung gespeichert wird, THEN THE System SHALL die Kategorien nach Häufigkeit absteigend sortieren

### Requirement 11: API-Konfiguration

**User Story:** Als Benutzer möchte ich, dass das System API-Credentials sicher verwaltet, damit meine Zugangsdaten geschützt sind.

#### Acceptance Criteria

1. WHEN das System startet, THEN THE System SHALL den OPENAI_API_KEY aus Umgebungsvariablen laden
2. WHEN kein API-Key gefunden wird, THEN THE System SHALL eine Fehlermeldung anzeigen und die Verarbeitung stoppen
3. WHEN das System Umgebungsvariablen lädt, THEN THE System SHALL mehrere .env-Dateipfade durchsuchen
4. WHEN eine .env-Datei gefunden wird, THEN THE System SHALL diese laden und dem Benutzer den Pfad anzeigen
5. WHEN keine .env-Datei gefunden wird, THEN THE System SHALL eine Warnung ausgeben und versuchen, direkt auf Umgebungsvariablen zuzugreifen
