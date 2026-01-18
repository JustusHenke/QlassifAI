"""Qlassif-AI - Hauptprogramm"""

import sys
from pathlib import Path

# Füge src zum Python-Pfad hinzu
sys.path.insert(0, str(Path(__file__).parent / "src"))

from environment_manager import EnvironmentManager, MissingAPIKeyError
from file_discovery import FileDiscovery
from excel_loader import ExcelLoader, NoCompatibleSheetsError
from config_manager import ConfigManager
from llm_analyzer import LLMAnalyzer
from keyword_categorizer import KeywordCategorizer
from excel_writer import ExcelWriter
from statistics_generator import StatisticsGenerator
from models import ProcessingStats
from logging_config import setup_logging, get_logger

# Setup Logging
setup_logging()
logger = get_logger("main")


def main():
    """Hauptfunktion"""
    print("=" * 60)
    print("Qlassif-AI - LLM-basierte Textanalyse für Excel")
    print("=" * 60)
    
    try:
        # 1. Verzeichnis abfragen
        print("\n1. Verzeichnis auswählen...")
        print("In welchem Ordner liegt die zu untersuchende Datei?")
        print("(Enter für aktuelles Verzeichnis)")
        
        directory_input = input("Pfad: ").strip()
        
        if not directory_input:
            working_directory = Path.cwd()
            print(f"✓ Verwende aktuelles Verzeichnis: {working_directory}")
        else:
            working_directory = Path(directory_input)
            if not working_directory.exists():
                print(f"✗ Verzeichnis existiert nicht: {working_directory}")
                print("Verwende stattdessen aktuelles Verzeichnis")
                working_directory = Path.cwd()
            elif not working_directory.is_dir():
                print(f"✗ Pfad ist kein Verzeichnis: {working_directory}")
                print("Verwende stattdessen aktuelles Verzeichnis")
                working_directory = Path.cwd()
            else:
                print(f"✓ Verwende Verzeichnis: {working_directory}")
        
        # 2. File Discovery - Excel-Datei auswählen
        print("\n2. Wähle Excel-Datei...")
        file_discovery = FileDiscovery()
        excel_file = file_discovery.find_and_select_file(str(working_directory))
        
        # 3. Config Manager - Prüfmerkmale laden/erstellen
        print("\n3. Lade Konfiguration...")
        config_manager = ConfigManager()
        config = config_manager.load_or_create_config(working_directory)
        
        # 4. Environment Manager - API-Key laden (nach Config, um Provider zu kennen)
        print("\n4. Lade API-Key...")
        env_manager = EnvironmentManager()
        api_key = env_manager.get_api_key(config.provider)
        
        # 5. Excel Loader - Datei laden und analysieren (mit konfiguriertem Spaltennamen)
        print("\n5. Lade Excel-Datei...")
        excel_loader = ExcelLoader(custom_text_column=config.text_column_name)
        sheet_infos = excel_loader.load_and_analyze(excel_file)
        
        # Zeige detaillierte Übersicht
        total_rows = sum(len(sheet_info.data_rows) for sheet_info in sheet_infos)
        print("\n" + "=" * 60)
        print("Excel-Datei erfolgreich geladen")
        print("=" * 60)
        print(f"✓ Datei: {excel_file.name}")
        print(f"✓ Kompatible Sheets gefunden: {len(sheet_infos)}")
        print(f"✓ Gesamtzahl zu verarbeitender Zeilen: {total_rows}")
        print("\nDetails pro Sheet:")
        for sheet_info in sheet_infos:
            print(f"  • {sheet_info.name}: {len(sheet_info.data_rows)} Zeilen")
        print("=" * 60)
        
        # 6. LLM Analyzer - Initialisieren
        print("\n6. Initialisiere LLM Analyzer...")
        print(f"   Provider: {config.provider}")
        print(f"   Modell: {config.model}")
        llm_analyzer = LLMAnalyzer(api_key=api_key, model=config.model, provider=config.provider)
        
        # 7. Verarbeite alle Sheets
        print("\n7. Verarbeite Textantworten...")
        print("=" * 60)
        
        all_results = []
        stats = ProcessingStats()
        
        for sheet_info in sheet_infos:
            print(f"\nVerarbeite Sheet: {sheet_info.name}")
            print(f"Anzahl Zeilen: {len(sheet_info.data_rows)}")
            
            sheet_results = []
            stats.total_rows += len(sheet_info.data_rows)
            
            for idx, row_idx in enumerate(sheet_info.data_rows, start=1):
                # Hole Text
                cell = sheet_info.sheet.cell(
                    row=row_idx, 
                    column=sheet_info.text_column_index
                )
                text = str(cell.value) if cell.value else ""
                
                print(f"  Zeile {idx}/{len(sheet_info.data_rows)}: ", end="", flush=True)
                
                # Analysiere
                result = llm_analyzer.analyze_text(text, config.check_attributes)
                
                if result.error:
                    print(f"✗ Fehler: {result.error}")
                    stats.add_failure(f"Zeile {row_idx}: {result.error}")
                else:
                    print("✓")
                    stats.add_success(result.prompt_tokens, result.completion_tokens)
                
                sheet_results.append(result)
            
            all_results.extend(sheet_results)
        
        print("\n" + "=" * 60)
        print("Verarbeitung abgeschlossen")
        print(stats.summary())
        
        # 7. Keyword Categorizer - Kategorisiere Keywords
        print("\n7. Kategorisiere Keywords...")
        keyword_categorizer = KeywordCategorizer(llm_analyzer)
        category_mapping, category_assignments = keyword_categorizer.categorize_all(all_results)
        
        # 8. Excel Writer - Erstelle neue Excel-Datei mit Ergebnissen
        print("\n8. Erstelle neue Excel-Datei mit Ergebnissen...")
        excel_writer = ExcelWriter()
        
        output_file = excel_file.parent / f"{excel_file.stem}_analyzed{excel_file.suffix}"
        excel_writer.create_new_workbook_with_results(
            sheet_infos=sheet_infos,
            all_results=all_results,
            category_assignments=category_assignments,
            check_attributes=config.check_attributes,
            output_path=output_file
        )
        
        # 9. Statistics Generator - Erstelle Statistik-Datei
        print("\n9. Erstelle Statistik-Datei...")
        stats_generator = StatisticsGenerator()
        stats_file = excel_file.parent / f"{excel_file.stem}_statistics.xlsx"
        
        # Extrahiere Sheet-Namen und Zeilenzahlen
        sheet_names = [sheet_info.name for sheet_info in sheet_infos]
        sheet_row_counts = [len(sheet_info.data_rows) for sheet_info in sheet_infos]
        
        stats_generator.generate_statistics(
            sheet_names,
            sheet_row_counts,
            category_assignments,
            category_mapping,
            stats_file
        )
        
        # Fertig
        print("\n" + "=" * 60)
        print("✓ Analyse erfolgreich abgeschlossen!")
        print("=" * 60)
        print(f"\nErgebnisse:")
        print(f"  - Analysierte Datei: {output_file}")
        print(f"  - Statistik-Datei: {stats_file}")
        print(f"  - Verarbeitete Zeilen: {stats.total_rows}")
        print(f"  - Erfolgreich: {stats.successful}")
        print(f"  - Fehlgeschlagen: {stats.failed}")
        print(f"\nToken-Verbrauch:")
        print(f"  - Prompt-Tokens: {stats.total_prompt_tokens:,}")
        print(f"  - Completion-Tokens: {stats.total_completion_tokens:,}")
        print(f"  - Gesamt-Tokens: {stats.total_tokens:,}")
        
    except MissingAPIKeyError as e:
        print(f"\n✗ Fehler: {e}")
        print("\nBitte setzen Sie OPENAI_API_KEY als Umgebungsvariable")
        print("oder erstellen Sie eine .env-Datei mit:")
        print("OPENAI_API_KEY=your-api-key-here")
        sys.exit(1)
    
    except NoCompatibleSheetsError as e:
        print(f"\n✗ Fehler: {e}")
        print("\nDie Excel-Datei muss eine Spalte mit dem Namen")
        print("'text', 'Antwort', 'answer' oder 'Textantwort' enthalten.")
        sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n\n✗ Abbruch durch Benutzer")
        sys.exit(1)
    
    except Exception as e:
        print(f"\n✗ Unerwarteter Fehler: {e}")
        logger.exception("Unerwarteter Fehler")
        sys.exit(1)


if __name__ == "__main__":
    main()
