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
from mode_selector import ModeSelector
from pdf_workflow import process_pdf_mode

# Setup Logging
setup_logging()
logger = get_logger("main")


def main():
    """Hauptfunktion"""
    print("=" * 60)
    print("Qlassif-AI - LLM-basierte Textanalyse")
    print("=" * 60)
    
    try:
        # 0. Mode Selection - Wähle zwischen Excel und PDF
        print("\n0. Modus auswählen...")
        mode_selector = ModeSelector()
        mode = mode_selector.select_mode()
        
        # 1. Verzeichnis abfragen
        print("\n1. Verzeichnis auswählen...")
        if mode == "excel":
            print("In welchem Ordner liegt die zu untersuchende Excel-Datei?")
        else:
            print("In welchem Ordner liegen die zu untersuchenden PDF-Dateien?")
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
        
        # 2. Config Manager - Prüfmerkmale laden/erstellen
        print("\n2. Lade Konfiguration...")
        config_manager = ConfigManager()
        config = config_manager.load_or_create_config(working_directory)
        
        # 3. Environment Manager - API-Key laden (nach Config, um Provider zu kennen)
        print("\n3. Lade API-Key...")
        env_manager = EnvironmentManager()
        api_key = env_manager.get_api_key(config.provider)
        
        # Verzweige basierend auf Modus
        if mode == "pdf":
            # PDF-Modus
            merged_results, pdf_stats = process_pdf_mode(
                working_directory=str(working_directory),
                config=config,
                api_key=api_key
            )
            
            if not merged_results:
                print("\n✗ Keine PDFs erfolgreich verarbeitet")
                sys.exit(1)
            
            # Kategorisiere Keywords
            print("\n" + "=" * 60)
            print("Kategorisiere Keywords...")
            print("=" * 60)
            llm_analyzer = LLMAnalyzer(api_key=api_key, model=config.model, provider=config.provider)
            keyword_categorizer = KeywordCategorizer(llm_analyzer)
            
            # Erstelle temporäre AnalysisResult-Objekte für Kategorisierung
            from models import AnalysisResult
            temp_results = []
            for result in merged_results:
                temp_results.append(AnalysisResult(
                    paraphrase=result.paraphrase,
                    sentiment={-1: "negativ", 0: "gemischt", 1: "positiv"}[result.sentiment],
                    sentiment_reason=result.sentiment_reason,
                    keywords=result.keywords,
                    custom_checks=result.custom_checks
                ))
            
            category_mapping, category_assignments = keyword_categorizer.categorize_all(temp_results)
            
            # Aktualisiere merged_results mit Kategorien
            for result, categories in zip(merged_results, category_assignments):
                result.keyword_category = ", ".join(categories)
            
            # Erstelle Output-Dateien
            print("\n" + "=" * 60)
            print("Erstelle Output-Datei...")
            print("=" * 60)
            
            dir_name = working_directory.name
            output_file = working_directory / f"{dir_name}_analyzed.xlsx"
            
            excel_writer = ExcelWriter()
            excel_writer.create_pdf_results_workbook(
                merged_results=merged_results,
                check_attributes=config.check_attributes,
                category_mapping=category_mapping,
                output_path=output_file
            )
            
            # Fertig
            print("\n" + "=" * 60)
            print("✓ PDF-Analyse erfolgreich abgeschlossen!")
            print("=" * 60)
            print(f"\nErgebnisse:")
            print(f"  - Analysedatei: {output_file}")
            print(f"  - Verarbeitete PDFs: {pdf_stats.total_pdfs}")
            print(f"  - Erfolgreich: {pdf_stats.successful_pdfs}")
            print(f"  - Fehlgeschlagen: {pdf_stats.failed_pdfs}")
            print(f"  - Gesamt Chunks: {pdf_stats.total_chunks}")
            print(f"\nToken-Verbrauch:")
            print(f"  - Prompt-Tokens: {pdf_stats.total_prompt_tokens:,}")
            print(f"  - Completion-Tokens: {pdf_stats.total_completion_tokens:,}")
            print(f"  - Gesamt-Tokens: {pdf_stats.total_tokens:,}")
            
        else:
            # Excel-Modus (bestehender Code)
            # 4. File Discovery - Excel-Datei auswählen
            print("\n4. Wähle Excel-Datei...")
            file_discovery = FileDiscovery()
            excel_file = file_discovery.find_and_select_file(str(working_directory), file_type="excel")
            excel_file = file_discovery.find_and_select_file(str(working_directory), file_type="excel")
        
            # 5. Excel Loader - Datei laden und analysieren (mit konfiguriertem Spaltennamen)
            print("\n5. Lade Excel-Datei...")
            excel_loader = ExcelLoader(custom_text_column=config.text_column_name)
            sheet_infos = excel_loader.load_and_analyze(excel_file)
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
        
            # 8. Keyword Categorizer - Kategorisiere Keywords
            print("\n8. Kategorisiere Keywords...")
            keyword_categorizer = KeywordCategorizer(llm_analyzer)
            category_mapping, category_assignments = keyword_categorizer.categorize_all(all_results)
        
            # 9. Excel Writer - Erstelle neue Excel-Datei mit Ergebnissen
            print("\n9. Erstelle neue Excel-Datei mit Ergebnissen...")
            excel_writer = ExcelWriter()
        
            output_file = excel_file.parent / f"{excel_file.stem}_analyzed{excel_file.suffix}"
            excel_writer.create_new_workbook_with_results(
                sheet_infos=sheet_infos,
                all_results=all_results,
                category_assignments=category_assignments,
                check_attributes=config.check_attributes,
                category_mapping=category_mapping,
                output_path=output_file
            )
        
            # Fertig
            print("\n" + "=" * 60)
            print("✓ Analyse erfolgreich abgeschlossen!")
            print("=" * 60)
            print(f"\nErgebnisse:")
            print(f"  - Analysedatei: {output_file}")
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
