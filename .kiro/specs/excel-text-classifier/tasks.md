# Implementation Plan: Qlassif-AI

## Overview

Dieser Implementierungsplan beschreibt die schrittweise Entwicklung von Qlassif-AI, einem Python-Tool zur automatisierten Klassifizierung von Textantworten in Excel-Dateien mittels LLMs. Die Implementierung erfolgt modular, wobei jede Komponente einzeln entwickelt und getestet wird, bevor sie integriert wird.

## Tasks

- [x] 1. Projekt-Setup und Grundstruktur
  - Python-Projekt mit Poetry oder pip initialisieren
  - Abhängigkeiten installieren: openpyxl, openai, python-dotenv, hypothesis (für Tests)
  - Verzeichnisstruktur erstellen: src/, tests/unit/, tests/property/, tests/integration/
  - Logging-Konfiguration einrichten
  - _Requirements: 8.1, 8.2, 8.3_

- [ ]* 1.1 Projekt-Setup testen
  - Verifizieren, dass alle Abhängigkeiten korrekt installiert sind
  - Testen, dass Logging funktioniert

- [x] 2. Environment Manager implementieren
  - [x] 2.1 EnvironmentManager-Klasse erstellen
    - Methode zum Suchen und Laden von .env-Dateien implementieren
    - Methode zum Abrufen des API-Keys aus Umgebungsvariablen
    - Methode zur Validierung des API-Key-Formats
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

  - [ ]* 2.2 Property Test für API-Key-Laden schreiben
    - **Property 11: API-Key-Laden**
    - **Validates: Requirements 3.8, 11.1, 11.3, 11.4, 11.5**

  - [ ]* 2.3 Unit Tests für EnvironmentManager schreiben
    - Test für erfolgreichen API-Key-Abruf
    - Test für fehlenden API-Key (Edge Case)
    - Test für .env-Datei-Suche in mehreren Pfaden
    - _Requirements: 11.2, 11.3, 11.4, 11.5_

- [x] 3. File Discovery Module implementieren
  - [x] 3.1 FileDiscovery-Klasse erstellen
    - Methode zum Scannen eines Verzeichnisses nach Excel-Dateien (.xlsx, .xls)
    - Methode zur Präsentation einer interaktiven Dateiauswahl
    - _Requirements: 1.1, 1.2_

  - [ ]* 3.2 Property Test für Excel-Datei-Erkennung schreiben
    - **Property 1: Excel-Datei-Erkennung**
    - **Validates: Requirements 1.1, 1.2**

  - [ ]* 3.3 Unit Tests für FileDiscovery schreiben
    - Test für Verzeichnis mit mehreren Excel-Dateien
    - Test für Verzeichnis ohne Excel-Dateien (Edge Case)
    - Test für nicht-existierendes Verzeichnis (Edge Case)
    - _Requirements: 1.1, 1.2_

- [x] 4. Data Models definieren
  - [x] 4.1 Dataclasses für alle Datenstrukturen erstellen
    - SheetInfo, CheckAttribute, Config, AnalysisResult, CategoryMapping, ProcessingStats
    - Validierungslogik für CheckAttribute (answer_type muss "boolean" oder "categorical" sein)
    - _Requirements: 4.4, 5.1_

  - [ ]* 4.2 Unit Tests für Data Models schreiben
    - Test für gültige und ungültige CheckAttribute-Instanzen
    - Test für Config-Validierung
    - _Requirements: 4.4_

- [x] 5. Config Manager implementieren
  - [x] 5.1 ConfigManager-Klasse erstellen
    - Methode zum Suchen einer config.json-Datei
    - Methode zum Laden und Validieren einer Config-Datei
    - Methode zum Speichern einer Config als JSON
    - Methode für interaktiven Dialog zur Erstellung neuer Prüfmerkmale
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 5.1, 5.2, 5.3_

  - [ ]* 5.2 Property Test für Config-Serialisierung Round-Trip schreiben
    - **Property 14: Config-Serialisierung Round-Trip**
    - **Validates: Requirements 4.5, 5.1, 5.2**

  - [ ]* 5.3 Property Test für Config-Datei-Suche schreiben
    - **Property 12: Config-Datei-Suche**
    - **Validates: Requirements 4.1**

  - [ ]* 5.4 Property Test für Prüfmerkmal-Speicherung schreiben
    - **Property 13: Prüfmerkmal-Speicherung**
    - **Validates: Requirements 4.4**

  - [ ]* 5.5 Property Test für ungültige Config-Behandlung schreiben
    - **Property 17: Ungültige Config-Behandlung**
    - **Validates: Requirements 5.3**

  - [ ]* 5.6 Unit Tests für ConfigManager schreiben
    - Test für erfolgreichen Config-Load
    - Test für ungültige JSON-Datei (Edge Case)
    - Test für fehlende Felder in Config (Edge Case)
    - _Requirements: 4.1, 4.2, 5.2, 5.3_

- [x] 6. Checkpoint - Basis-Infrastruktur validieren
  - Sicherstellen, dass alle Tests bis hierhin bestehen
  - Bei Fragen den Benutzer konsultieren

- [x] 7. Excel Loader & Sheet Parser implementieren
  - [x] 7.1 ExcelLoader-Klasse erstellen
    - Methode zum Laden einer Excel-Datei mit openpyxl
    - Methode zum Finden kompatibler Sheets (mit "text", "Antwort", "answer" Spalten)
    - Methode zum Lokalisieren der Textspalte (innerhalb der ersten 5 Zeilen)
    - Methode zum Identifizieren nicht-leerer Datenzeilen
    - _Requirements: 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4_

  - [ ]* 7.2 Property Test für Workbook-Laden und Sheet-Analyse schreiben
    - **Property 2: Workbook-Laden und Sheet-Analyse**
    - **Validates: Requirements 1.3**

  - [ ]* 7.3 Property Test für kompatible Sheet-Erkennung schreiben
    - **Property 3: Kompatible Sheet-Erkennung**
    - **Validates: Requirements 1.4**

  - [ ]* 7.4 Property Test für Textspalten-Identifikation schreiben
    - **Property 4: Textspalten-Identifikation**
    - **Validates: Requirements 2.1, 2.4**

  - [ ]* 7.5 Property Test für nicht-leere Zeilen-Identifikation schreiben
    - **Property 5: Nicht-leere Zeilen-Identifikation**
    - **Validates: Requirements 2.2**

  - [ ]* 7.6 Property Test für Excel-Ladefehler-Behandlung schreiben
    - **Property 25: Excel-Ladefehler-Behandlung**
    - **Validates: Requirements 8.1**

  - [ ]* 7.7 Unit Tests für ExcelLoader schreiben
    - Test für Excel-Datei mit mehreren kompatiblen Sheets
    - Test für Excel-Datei ohne kompatible Sheets (Edge Case)
    - Test für Sheet mit mehreren Textspalten (Edge Case - erste wird verwendet)
    - Test für Kopfzeile nicht in erster Zeile (Edge Case)
    - Test für ungültige Excel-Datei (Edge Case)
    - _Requirements: 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 8.1_

- [x] 8. LLM Analyzer implementieren
  - [x] 8.1 LLMAnalyzer-Klasse erstellen
    - OpenAI-Client mit 60 Sekunden Timeout initialisieren
    - Methode zum Erstellen strukturierter Prompts für Textanalyse
    - Methode zum Parsen von LLM-JSON-Antworten
    - Methode zur vollständigen Textanalyse (Paraphrase, Sentiment, Keywords, Prüfmerkmale)
    - Fehlerbehandlung für API-Timeouts und ungültige Antworten
    - _Requirements: 3.1, 3.2, 3.3, 3.5, 3.6, 3.7, 3.8, 4.6, 4.7_

  - [ ]* 8.2 Property Test für LLM-Analyse-Vollständigkeit schreiben
    - **Property 6: LLM-Analyse-Vollständigkeit**
    - **Validates: Requirements 3.1, 3.2, 3.3**

  - [ ]* 8.3 Property Test für Sentiment-Validität schreiben
    - **Property 7: Sentiment-Validität**
    - **Validates: Requirements 3.2**

  - [ ]* 8.4 Property Test für Keyword-Anzahl schreiben
    - **Property 8: Keyword-Anzahl**
    - **Validates: Requirements 3.3**

  - [ ]* 8.5 Property Test für Boolean-Prüfmerkmal-Validität schreiben
    - **Property 15: Boolean-Prüfmerkmal-Validität**
    - **Validates: Requirements 4.6**

  - [ ]* 8.6 Property Test für Kategoriale-Prüfmerkmal-Validität schreiben
    - **Property 16: Kategoriale-Prüfmerkmal-Validität**
    - **Validates: Requirements 4.7**

  - [ ]* 8.7 Property Test für Fehlertoleranz bei LLM-Aufrufen schreiben
    - **Property 10: Fehlertoleranz bei LLM-Aufrufen**
    - **Validates: Requirements 3.5, 8.2**

  - [ ]* 8.8 Unit Tests für LLMAnalyzer schreiben
    - Test mit gemockter OpenAI API für erfolgreiche Analyse
    - Test für API-Timeout (Edge Case)
    - Test für ungültige JSON-Antwort vom LLM (Edge Case)
    - Test für API-Rate-Limit (Edge Case)
    - _Requirements: 3.1, 3.2, 3.3, 3.5, 3.7, 4.6, 4.7_

- [x] 9. Checkpoint - Kern-Analyse-Funktionalität validieren
  - Sicherstellen, dass alle Tests bis hierhin bestehen
  - Bei Fragen den Benutzer konsultieren

- [x] 10. Keyword Categorizer implementieren
  - [x] 10.1 KeywordCategorizer-Klasse erstellen
    - Methode zum Sammeln und Deduplizieren aller Keywords
    - Methode zur LLM-basierten Generierung von Überkategorien
    - Methode zur Zuordnung von Keywords zu Kategorien
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

  - [ ]* 10.2 Property Test für Keyword-Sammlung schreiben
    - **Property 18: Keyword-Sammlung**
    - **Validates: Requirements 6.1**

  - [ ]* 10.3 Property Test für Kategorie-Generierung schreiben
    - **Property 19: Kategorie-Generierung**
    - **Validates: Requirements 6.2**

  - [ ]* 10.4 Property Test für Kategorie-Zuordnung schreiben
    - **Property 20: Kategorie-Zuordnung**
    - **Validates: Requirements 6.3**

  - [ ]* 10.5 Property Test für Kategorie-Spalte-Erstellung schreiben
    - **Property 21: Kategorie-Spalte-Erstellung**
    - **Validates: Requirements 6.4**

  - [ ]* 10.6 Unit Tests für KeywordCategorizer schreiben
    - Test für Keyword-Deduplizierung
    - Test für Antworten ohne Keywords (Edge Case - Kategorie "Keine")
    - Test für LLM-Kategorisierung mit gemockter API
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 11. Excel Writer implementieren
  - [x] 11.1 ExcelWriter-Klasse erstellen
    - Methode zum Hinzufügen von Ergebnisspalten rechts der Textspalte
    - Methode zum Schreiben von Analyseergebnissen in Zeilen
    - Methode zum Speichern der modifizierten Excel-Datei
    - _Requirements: 3.4, 7.1, 7.2, 7.3, 7.4, 7.5_

  - [ ]* 11.2 Property Test für Spalten-Positionierung schreiben
    - **Property 9: Spalten-Positionierung**
    - **Validates: Requirements 3.4, 7.1**

  - [ ]* 11.3 Property Test für Spalten-Benennung schreiben
    - **Property 22: Spalten-Benennung**
    - **Validates: Requirements 7.2, 7.3**

  - [ ]* 11.4 Property Test für Datei-Speicherung schreiben
    - **Property 23: Datei-Speicherung**
    - **Validates: Requirements 7.4**

  - [ ]* 11.5 Property Test für Multi-Sheet-Verarbeitung schreiben
    - **Property 24: Multi-Sheet-Verarbeitung**
    - **Validates: Requirements 7.5**

  - [ ]* 11.6 Unit Tests für ExcelWriter schreiben
    - Test für korrektes Schreiben von Ergebnissen
    - Test für Überschreiben vs. neue Datei mit Suffix
    - Test für mehrere Sheets
    - _Requirements: 3.4, 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 12. Statistics Generator implementieren
  - [x] 12.1 StatisticsGenerator-Klasse erstellen
    - Methode zur Berechnung von Kategorie-Häufigkeiten
    - Methode zum Sammeln von Keywords pro Kategorie (dedupliziert)
    - Methode zur Erstellung einer Statistik-Excel-Datei
    - Methode zum Sortieren der Kategorien nach Häufigkeit
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6_

  - [ ]* 12.2 Property Test für Kategorie-Häufigkeits-Berechnung schreiben
    - **Property 28: Kategorie-Häufigkeits-Berechnung**
    - **Validates: Requirements 10.1**

  - [ ]* 12.3 Property Test für Keywords-pro-Kategorie-Sammlung schreiben
    - **Property 29: Keywords-pro-Kategorie-Sammlung**
    - **Validates: Requirements 10.2, 10.5**

  - [ ]* 12.4 Property Test für Statistik-Excel-Erstellung schreiben
    - **Property 30: Statistik-Excel-Erstellung**
    - **Validates: Requirements 10.3, 10.4**

  - [ ]* 12.5 Property Test für Kategorie-Sortierung schreiben
    - **Property 31: Kategorie-Sortierung**
    - **Validates: Requirements 10.6**

  - [ ]* 12.6 Unit Tests für StatisticsGenerator schreiben
    - Test für korrekte Häufigkeitsberechnung
    - Test für Keyword-Deduplizierung
    - Test für absteigende Sortierung
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6_

- [x] 13. Checkpoint - Output-Komponenten validieren
  - Sicherstellen, dass alle Tests bis hierhin bestehen
  - Bei Fragen den Benutzer konsultieren

- [x] 14. Main Pipeline implementieren
  - [x] 14.1 Hauptprogramm-Logik erstellen
    - CLI-Interface für Benutzerinteraktion
    - Pipeline-Orchestrierung: File Discovery → Excel Loading → Config Management → Analysis → Categorization → Output
    - ProcessingStats-Tracking während der Verarbeitung
    - Fehlerbehandlung und Logging auf Pipeline-Ebene
    - _Requirements: 1.1, 1.2, 1.3, 8.3, 8.4_

  - [ ]* 14.2 Property Test für Verarbeitungs-Statistiken schreiben
    - **Property 26: Verarbeitungs-Statistiken**
    - **Validates: Requirements 8.3**

  - [ ]* 14.3 Property Test für kritische-Fehler-Behandlung schreiben
    - **Property 27: Kritische-Fehler-Behandlung**
    - **Validates: Requirements 8.4**

  - [ ]* 14.4 Integration Tests schreiben
    - End-to-End Test mit kleiner Test-Excel-Datei
    - Test für vollständige Pipeline mit gemockter LLM-API
    - Test für Pipeline mit mehreren Sheets
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 3.1, 3.2, 3.3, 6.1, 6.2, 6.3, 7.1, 7.2, 7.3, 10.1, 10.2, 10.3_

- [x] 15. Dokumentation und Finalisierung
  - [x] 15.1 README.md erstellen
    - Installation-Anleitung
    - Verwendungsbeispiele
    - Konfiguration (API-Key, Config-Datei)
    - Beispiel-Screenshots oder -Ausgaben

  - [x] 15.2 Beispiel-Dateien erstellen
    - Beispiel-Excel-Datei mit Testdaten
    - Beispiel-config.json mit verschiedenen Prüfmerkmalen
    - Beispiel-.env-Datei

  - [x] 15.3 Code-Dokumentation vervollständigen
    - Docstrings für alle öffentlichen Methoden
    - Type Hints überprüfen und vervollständigen
    - Inline-Kommentare für komplexe Logik

- [x] 16. Final Checkpoint - Vollständige Validierung
  - Alle Tests ausführen (Unit, Property, Integration)
  - Code Coverage prüfen (Ziel: >80% Line Coverage)
  - Manuelle End-to-End Tests mit echten Excel-Dateien
  - Bei Problemen den Benutzer konsultieren

## Notes

- Tasks mit `*` sind optional und können für ein schnelleres MVP übersprungen werden
- Jeder Task referenziert spezifische Requirements für Nachvollziehbarkeit
- Checkpoints stellen inkrementelle Validierung sicher
- Property Tests validieren universelle Korrektheitseigenschaften
- Unit Tests validieren spezifische Beispiele und Edge Cases
- Die Implementierung erfolgt modular, sodass jede Komponente unabhängig getestet werden kann
- LLM-API-Aufrufe sollten in Tests gemockt werden, um Kosten zu vermeiden
- Für Integration Tests kann optional ein Test-API-Key verwendet werden
