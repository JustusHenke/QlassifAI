"""Qlassif-AI - Hauptprogramm"""

import sys
from pathlib import Path
from datetime import datetime

# Füge src zum Python-Pfad hinzu
sys.path.insert(0, str(Path(__file__).parent / "src"))

from environment_manager import EnvironmentManager
from file_discovery import FileDiscovery
from excel_loader import ExcelLoader
from config_manager import ConfigManager
from llm_analyzer import LLMAnalyzer
from keyword_categorizer import KeywordCategorizer
from excel_writer import ExcelWriter
from statistics_generator import StatisticsGenerator
from models import ProcessingStats
from logging_config import setup_logging, get_logger
from mode_selector import ModeSelector
from pdf_workflow import process_pdf_mode
from exceptions import (
    QlassifError, MissingAPIKeyError, NoCompatibleSheetsError,
    ConfigError, ExcelError, PDFError, LLMError, FileDiscoveryError
)

# Neue Module für wissenschaftliche Methodik
from confidence_engine import ConfidenceEngine
from multi_coder import MultiCoder
from reproducibility_manager import ReproducibilityManager, MethodologyMetadata
from output_manager import OutputManager

# Setup Logging
setup_logging()
logger = get_logger("main")


def _run_multi_coder_workflow(working_directory: Path, config, api_key: str,
                              all_results: list, check_attributes: list):
    """
    Führt Multi-Coder Kodierung durch (wenn multi_coder=true).
    
    Args:
        working_directory: Arbeitsverzeichnis
        config: Konfiguration
        api_key: API-Key
        all_results: Bisherige Analyseergebnisse
        check_attributes: Prüfmerkmale
        
    Returns:
        Tuple mit (intercoder_result, output_manager)
    """
    sc = config.scientific
    
    print("\n" + "=" * 60)
    print("Multi-Coder Modus aktiviert")
    print("=" * 60)
    print(f"  Modelle: {', '.join(sc.coder_models)}")
    print(f"  Strategie: {sc.primary_coder}")
    print()
    
    # Initialisiere OutputManager
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_manager = OutputManager(working_directory, 'results', timestamp)
    
    # Initialisiere MultiCoder
    multi_coder = MultiCoder(sc)
    
    for model_name in sc.coder_models:
        # Erstelle Analyzer pro Modell
        analyzer = LLMAnalyzer(api_key=api_key, model=model_name, provider=config.provider)
        multi_coder.add_analyzer(model_name, analyzer)
    
    # Führe Multi-Coder Kodierung durch
    intercoder_results = []
    
    # Sammle alle Texte aus den Ergebnissen
    texts = []
    for result in all_results:
        if hasattr(result, 'paraphrase') and result.paraphrase:
            texts.append(result.paraphrase)
        else:
            texts.append("")  # Fallback
    
    print(f"\nVerarbeite {len(texts)} Texte mit {len(sc.coder_models)} Modellen...")
    
    for idx, text in enumerate(texts):
        if not text.strip():
            continue
        
        print(f"  Text {idx + 1}/{len(texts)}: ", end="", flush=True)
        
        try:
            intercoder_result = multi_coder.encode_text(
                text=text,
                check_attributes=check_attributes,
                research_question=config.research_question,
                include_reasoning=config.include_reasoning
            )
            intercoder_results.append(intercoder_result)
            print("✓")
        except Exception as e:
            print(f"✗ {e}")
    
    if intercoder_results:
        # Aggregiere Ergebnisse
        aggregated = MultiCoder.aggregate_batch_results(intercoder_results)
        overall_kappa = aggregated.get("__overall__", {}).get("mean_kappa", 0.0)
        
        print(f"\n  Durchschnittliche Übereinstimmung: {overall_kappa:.1%}")
        
        # Erstelle Intercoder-Excel
        if intercoder_results:
            excel_writer = ExcelWriter(confidence_threshold=sc.confidence_threshold)
            intercoder_path = output_manager.get_intercoder_path(working_directory.name)
            
            from openpyxl import Workbook
            wb = Workbook()
            wb.remove(wb.active)
            
            # Erstelle Intercoder-Sheet
            excel_writer.create_intercoder_sheet(wb, intercoder_results[0], check_attributes)
            excel_writer.create_kappa_sheet(wb, intercoder_results[0])
            
            wb.save(intercoder_path)
            print(f"  Intercoder-Datei: {intercoder_path}")
    
    return intercoder_results, output_manager


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
            # Path Validation:.resolve() normalisiert den Pfad
            working_directory = Path(directory_input).resolve()
            
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
        
        # 3. Environment Manager - API-Key laden
        print("\n3. Lade API-Key...")
        env_manager = EnvironmentManager()
        api_key = env_manager.get_api_key(config.provider)
        
        # Prüfe ob wissenschaftlicher Modus aktiv ist
        has_science = config.scientific is not None
        has_multi_coder = has_science and config.scientific.multi_coder
        
        if has_science:
            print(f"\n  Wissenschaftlicher Modus aktiviert")
            if has_multi_coder:
                print(f"  Multi-Coder: {', '.join(config.scientific.coder_models)}")
            print(f"  Konfidenz-Schwellwert: {config.scientific.confidence_threshold}%")
        
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
                    custom_checks=result.custom_checks,
                    custom_checks_reasons={}
                ))
            
            keyword_to_category, category_assignments = keyword_categorizer.categorize_all(temp_results)
            
            # Aktualisiere merged_results mit Kategorien
            for result, categories in zip(merged_results, category_assignments):
                result.keyword_category = ", ".join(categories)
            
            # Erstelle Output-Dateien
            print("\n" + "=" * 60)
            print("Erstelle Output-Datei...")
            print("=" * 60)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dir_name = working_directory.name
            output_file = working_directory / f"{dir_name}_analyzed_{timestamp}.xlsx"
            
            excel_writer = ExcelWriter(
                confidence_threshold=config.scientific.confidence_threshold if has_science else 0.7
            )
            excel_writer.create_pdf_results_workbook(
                merged_results=merged_results,
                check_attributes=config.check_attributes,
                keyword_to_category=keyword_to_category,
                output_path=output_file,
                include_reasoning=config.include_reasoning,
                include_confidence=has_science
            )
            
            # Multi-Coder für PDF (optional)
            if has_multi_coder:
                _run_multi_coder_workflow(
                    working_directory, config, api_key, temp_results, config.check_attributes
                )
            
            # Reproduzierbarkeit (optional)
            if has_science:
                print("\n" + "=" * 60)
                print("Erstelle Reproduzierbarkeitsdateien...")
                print("=" * 60)
                
                output_manager = OutputManager(working_directory, dir_name, timestamp)
                rm = ReproducibilityManager(output_manager.output_dir)
                
                metadata = MethodologyMetadata(
                    model=config.model,
                    provider=config.provider,
                    temperature=0.3,
                    seed=config.scientific.seed,
                    research_question=config.research_question or "",
                    check_attributes=[
                        {"question": a.question, "answer_type": a.answer_type, 
                         "categories": a.categories or [], "definition": a.definition or ""}
                        for a in config.check_attributes
                    ],
                    multi_coder=has_multi_coder,
                    coder_models=config.scientific.coder_models if has_multi_coder else [],
                    confidence_threshold=config.scientific.confidence_threshold,
                    total_items=pdf_stats.total_pdfs,
                    total_successful=pdf_stats.successful_pdfs,
                    total_failed=pdf_stats.failed_pdfs,
                    total_tokens=pdf_stats.total_tokens
                )
                
                # Convert merged_results to dicts for export
                results_dicts = [
                    {"custom_checks": r.custom_checks, "sentiment": r.sentiment, "keywords": r.keywords}
                    for r in merged_results
                ]
                
                output_files = rm.save_all(output_manager.output_dir,
                    metadata, 
                    [{"question": a.question, "answer_type": a.answer_type, 
                      "categories": a.categories or [], "definition": a.definition or ""}
                     for a in config.check_attributes],
                    results_dicts
                )
                
                for key, path in output_files.items():
                    print(f"  ✓ {key}: {path}")
            
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
            # Excel-Modus
            # 4. File Discovery
            print("\n4. Wähle Excel-Datei...")
            file_discovery = FileDiscovery()
            excel_file = file_discovery.find_and_select_file(str(working_directory), file_type="excel")
        
            # 5. Excel Loader
            print("\n5. Lade Excel-Datei...")
            excel_loader = ExcelLoader(custom_text_column=config.text_column_name)
            sheet_infos = excel_loader.load_and_analyze(excel_file)
        
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
        
            # 6. Analysator initialisieren
            print("\n6. Initialisiere Analysator...")
            print(f"   Provider: {config.provider}")
            
            all_results = []
            stats = ProcessingStats()
            intercoder_results = []
            llm_analyzer = None
            
            if has_multi_coder:
                # Multi-Coder: Primary Codierer liefert Hauptergebnisse
                coder_models_str = ", ".join(config.scientific.coder_models)
                print(f"   Modus: Multi-Coder ({coder_models_str})")
                print(f"   Prim\u00e4rer Kodierer: {config.scientific.primary_coder}")
                
                multi_coder_inst = MultiCoder(config.scientific)
                for model_name in config.scientific.coder_models:
                    analyzer = LLMAnalyzer(api_key=api_key, model=model_name, provider=config.provider)
                    multi_coder_inst.add_analyzer(model_name, analyzer)
                
                llm_analyzer = LLMAnalyzer(api_key=api_key, model=config.scientific.coder_models[0], provider=config.provider)
            else:
                print(f"   Modell: {config.model}")
                llm_analyzer = LLMAnalyzer(api_key=api_key, model=config.model, provider=config.provider)

            # 7. Verarbeite alle Sheets
            print("\n7. Verarbeite Textantworten...")
            print("=" * 60)

            for sheet_info in sheet_infos:
                print(f"\nVerarbeite Sheet: {sheet_info.name}")
                print(f"Anzahl Zeilen: {len(sheet_info.data_rows)}")

                sheet_results = []
                stats.total_rows += len(sheet_info.data_rows)

                for idx, row_idx in enumerate(sheet_info.data_rows, start=1):
                    cell = sheet_info.sheet.cell(
                        row=row_idx,
                        column=sheet_info.text_column_index
                    )
                    text = str(cell.value) if cell.value else ""

                    print(f"  Zeile {idx}/{len(sheet_info.data_rows)}: ", end="", flush=True)

                    if has_multi_coder:
                        try:
                            ic_result = multi_coder_inst.encode_text(
                                text=text,
                                check_attributes=config.check_attributes,
                                research_question=config.research_question,
                                include_reasoning=config.include_reasoning
                            )
                            intercoder_results.append(ic_result)
                            result = ic_result.primary_coder.analysis_result
                            sheet_results.append(result)
                            print(f"OK ({len(ic_result.coder_results)} Kodierer)")
                            stats.add_success(result.prompt_tokens, result.completion_tokens)
                        except Exception as e:
                            print(f"Fehler: {e}")
                            stats.add_failure(f"Zeile {row_idx}: {e}")
                    else:
                        result = llm_analyzer.analyze_text(
                            text,
                            config.check_attributes,
                            config.research_question,
                            config.include_reasoning
                        )

                        if result.error:
                            print(f"Fehler: {result.error}")
                            stats.add_failure(f"Zeile {row_idx}: {result.error}")
                        else:
                            print("OK")
                            stats.add_success(result.prompt_tokens, result.completion_tokens)

                        sheet_results.append(result)

                all_results.extend(sheet_results)

            print("\n" + "=" * 60)
            print("Verarbeitung abgeschlossen")
            print(stats.summary())

            # Intercoder-Statistiken
            if has_multi_coder and intercoder_results:
                from kappa_calculator import KappaCalculator
                aggregated = MultiCoder.aggregate_batch_results(intercoder_results)
                overall_kappa = aggregated.get("__overall__", {}).get("mean_kappa", 0.0)
                print(f"\n  Intercoder-Reliabilit\u00e4t:")
                print(f"    Kodierer: {len(config.scientific.coder_models)}")
                print(f"    \u00dcbereinstimmung: {overall_kappa:.1%}")
                print(f"    Interpretation: {KappaCalculator.interpret_kappa_de(overall_kappa)}")

            # 8. Keyword Categorizer
            print("\n8. Kategorisiere Keywords...")
            keyword_categorizer = KeywordCategorizer(llm_analyzer)
            keyword_to_category, category_assignments = keyword_categorizer.categorize_all(all_results)

            # 9. Excel Writer
            print("\n9. Erstelle neue Excel-Datei mit Ergebnissen...")

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_manager = OutputManager(working_directory, excel_file.stem, timestamp)
            output_file = output_manager.get_analyzed_path()

            excel_writer = ExcelWriter(
                confidence_threshold=config.scientific.confidence_threshold if has_science else 0.7
            )
            workbook = excel_writer.create_new_workbook_with_results(
                sheet_infos=sheet_infos,
                all_results=all_results,
                category_assignments=category_assignments,
                check_attributes=config.check_attributes,
                keyword_to_category=keyword_to_category,
                output_path=output_file,
                include_reasoning=config.include_reasoning,
                include_confidence=has_science
            )

            # Intercoder-Sheets (optional) - direkt ins gleiche Workbook
            if has_multi_coder and intercoder_results:
                excel_writer.create_intercoder_sheet(workbook, intercoder_results[0], config.check_attributes)
                excel_writer.create_kappa_sheet(workbook, intercoder_results[0])

            # Einmal alles speichern
            workbook.save(output_file)
            print(f"  Ergebnisse: {output_file}")

            # Reproduzierbarkeit (optional)
            if has_science:
                print("\n" + "=" * 60)
                print("Erstelle Reproduzierbarkeitsdateien...")
                print("=" * 60)
                
                rm = ReproducibilityManager(output_manager.output_dir)
                
                metadata = MethodologyMetadata(
                    model=config.model,
                    provider=config.provider,
                    temperature=0.3,
                    seed=config.scientific.seed,
                    research_question=config.research_question or "",
                    check_attributes=[
                        {"question": a.question, "answer_type": a.answer_type, 
                         "categories": a.categories or [], "definition": a.definition or ""}
                        for a in config.check_attributes
                    ],
                    multi_coder=has_multi_coder,
                    coder_models=config.scientific.coder_models if has_multi_coder else [],
                    confidence_threshold=config.scientific.confidence_threshold,
                    total_items=stats.total_rows,
                    total_successful=stats.successful,
                    total_failed=stats.failed,
                    total_tokens=stats.total_tokens
                )
                
                results_dicts = [
                    {"custom_checks": r.custom_checks, "sentiment": r.sentiment, "keywords": r.keywords}
                    for r in all_results
                ]
                
                output_files = rm.save_all(output_manager.output_dir,
                    metadata,
                    [{"question": a.question, "answer_type": a.answer_type, 
                      "categories": a.categories or [], "definition": a.definition or ""}
                     for a in config.check_attributes],
                    results_dicts
                )
                
                for key, path in output_files.items():
                    print(f"  ✓ {key}: {path}")
        
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
        print(f"\n✗ API-Key Fehler: {e}")
        print("\nBitte setzen Sie OPENAI_API_KEY als Umgebungsvariable")
        print("oder erstellen Sie eine .env-Datei mit:")
        print("OPENAI_API_KEY=your-api-key-here")
        sys.exit(1)
    
    except NoCompatibleSheetsError as e:
        print(f"\n✗ Excel-Fehler: {e}")
        print("\nDie Excel-Datei muss eine Spalte mit dem Namen")
        print("'text', 'Antwort', 'answer' oder 'Textantwort' enthalten.")
        sys.exit(1)
    
    except ConfigError as e:
        print(f"\n✗ Konfigurationsfehler: {e}")
        logger.error(f"Konfigurationsfehler: {e}")
        sys.exit(1)
    
    except (ExcelError, PDFError) as e:
        print(f"\n✗ Dateifehler: {e}")
        logger.error(f"Dateifehler: {e}")
        sys.exit(1)
    
    except LLMError as e:
        print(f"\n✗ LLM-Fehler: {e}")
        logger.error(f"LLM-Fehler: {e}")
        sys.exit(1)
    
    except FileDiscoveryError as e:
        print(f"\n✗ Dateisuchfehler: {e}")
        logger.error(f"Dateisuchfehler: {e}")
        sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n\n✗ Abbruch durch Benutzer")
        sys.exit(1)
    
    except QlassifError as e:
        print(f"\n✗ Anwendungsfehler: {e}")
        logger.exception("Anwendungsfehler")
        sys.exit(1)
    
    except Exception as e:
        print(f"\n✗ Unerwarteter Fehler: {e}")
        logger.exception("Unerwarteter Fehler")
        sys.exit(1)


if __name__ == "__main__":
    main()
