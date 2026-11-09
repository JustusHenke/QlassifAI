"""PDF Workflow für Qlassif-AI - Orchestriert PDF-Verarbeitung"""

import logging
from pathlib import Path
from typing import List
import sys

# Füge src zum Python-Pfad hinzu falls nötig
if str(Path(__file__).parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent))

from models import Config, PDFProcessingStats, MergedResult
from pdf_processor import PDFProcessor, PDFExtractionError
from text_chunker import TextChunker
from llm_analyzer import LLMAnalyzer
from result_merger import ResultMerger
from file_discovery import FileDiscovery
from checkpoint import CheckpointManager, merged_to_dict, merged_from_dict

logger = logging.getLogger(__name__)


def process_pdf_mode(working_directory: str, config: Config, api_key: str) -> tuple[List[MergedResult], PDFProcessingStats]:
    """
    Verarbeitet PDF-Modus: Dateiauswahl → Textextraktion → Chunking → Analyse → Zusammenführung.
    
    Args:
        working_directory: Arbeitsverzeichnis mit PDF-Dateien
        config: Konfiguration mit check_attributes
        api_key: API-Key für LLM
        
    Returns:
        Tuple von (Liste von MergedResult, PDFProcessingStats)
    """
    logger.info("Starte PDF-Verarbeitungsmodus")
    
    # Initialisiere Komponenten
    file_discovery = FileDiscovery()
    pdf_processor = PDFProcessor()
    text_chunker = TextChunker()
    llm_analyzer = LLMAnalyzer(
        api_key=api_key,
        model=config.model,
        provider=config.provider
    )
    result_merger = ResultMerger()
    stats = PDFProcessingStats()
    
    # Finde und wähle PDF-Dateien
    try:
        pdf_files = file_discovery.scan_pdf_directory(working_directory)
        
        if not pdf_files:
            print(f"\n❌ Keine PDF-Dateien in {working_directory} gefunden")
            logger.error(f"Keine PDF-Dateien in {working_directory}")
            return [], stats
        
        print(f"\n✓ {len(pdf_files)} PDF-Datei(en) gefunden")
        logger.info(f"{len(pdf_files)} PDF-Dateien gefunden")
        
        # Offset + Zufallsstichprobe aus Config anwenden (vor der Verarbeitung,
        # damit nicht analysierte PDFs keine API-Kosten verursachen)
        if config.offset or config.sample_size:
            from sampling import apply_sampling
            seed = config.scientific.seed if config.scientific else None
            total_before = len(pdf_files)
            pdf_files = apply_sampling(pdf_files, config.sample_size, config.offset, seed)
            print(f"\n  Stichproben-Modus (Config):")
            if config.offset:
                print(f"  ✓ Offset: erste {config.offset} PDFs übersprungen")
            if config.sample_size:
                print(f"  ✓ Zufallsstichprobe: {len(pdf_files)} von {total_before} PDFs"
                      + (f" (Seed: {seed})" if seed is not None else ""))
        
    except Exception as e:
        error_msg = f"Fehler bei PDF-Dateisuche: {e}"
        logger.error(error_msg)
        print(f"\n❌ {error_msg}")
        return [], stats
    
    # Checkpoint: Zwischenergebnisse laden (Wiederaufnahme nach Abbruch)
    checkpoint_path = Path(working_directory) / "_pdf_checkpoint.json"
    fingerprint = {
        "model": config.model,
        "provider": config.provider,
        "research_question": config.research_question,
        "check_attributes": [
            {"question": a.question, "answer_type": a.answer_type,
             "categories": a.categories, "definition": a.definition}
            for a in config.check_attributes
        ],
    }
    source_id = "pdf|" + ";".join(p.name for p in pdf_files)
    checkpoint = CheckpointManager(checkpoint_path, source_id, fingerprint)
    resume = False
    if checkpoint.has_entries():
        print(f"\n  Checkpoint gefunden: {len(checkpoint)} PDF(s) bereits bearbeitet.")
        choice = input("  Am letzten kompletten PDF fortsetzen? (j/n): ").strip().lower()
        resume = choice in ["j", "ja", "y", "yes"]
        if not resume:
            checkpoint.clear()
            print("  Checkpoint verworfen, Start von vorn")
    
    # Verarbeite jede PDF-Datei
    merged_results = []
    
    for pdf_idx, pdf_path in enumerate(pdf_files, start=1):
        # Wiederaufnahme: bereits bearbeitete PDF aus Checkpoint laden
        if resume and checkpoint.get(pdf_path.name) is not None:
            merged_result = merged_from_dict(checkpoint.get(pdf_path.name))
            merged_results.append(merged_result)
            stats.total_pdfs += 1
            stats.add_pdf_success(chunk_count=merged_result.chunk_count,
                                  prompt_tokens=0, completion_tokens=0)
            print(f"\n[{pdf_idx}/{len(pdf_files)}] {pdf_path.name}: übersprungen (Checkpoint)")
            continue
        
        print(f"\n{'='*60}")
        print(f"Verarbeite PDF {pdf_idx}/{len(pdf_files)}: {pdf_path.name}")
        print(f"{'='*60}")
        
        stats.total_pdfs += 1
        
        try:
            # Extrahiere Text
            print(f"  [1/4] Extrahiere Text...")
            text = pdf_processor.extract_text(pdf_path)
            print(f"  ✓ {len(text)} Zeichen extrahiert")
            
            # Chunke Text
            print(f"  [2/4] Teile Text in Chunks...")
            chunks = text_chunker.chunk_text(text)
            print(f"  ✓ {len(chunks)} Chunk(s) erstellt")
            
            # Analysiere jeden Chunk
            print(f"  [3/4] Analysiere Chunks...")
            chunk_results = []
            chunk_prompt_tokens = 0
            chunk_completion_tokens = 0
            
            for chunk in chunks:
                print(f"    → Chunk {chunk.chunk_id + 1}/{len(chunks)} ({chunk.char_count} Zeichen)...", end=" ")
                
                result = llm_analyzer.analyze_text(
                    text=chunk.text,
                    check_attributes=config.check_attributes,
                    research_question=config.research_question,
                    include_reasoning=config.include_reasoning
                )
                
                if result.error:
                    print(f"❌ Fehler: {result.error}")
                    logger.error(f"Chunk {chunk.chunk_id} Analyse fehlgeschlagen: {result.error}")
                else:
                    print(f"✓")
                    chunk_results.append(result)
                    chunk_prompt_tokens += result.prompt_tokens
                    chunk_completion_tokens += result.completion_tokens
            
            if not chunk_results:
                error_msg = f"Alle Chunks von {pdf_path.name} fehlgeschlagen"
                logger.error(error_msg)
                stats.add_pdf_failure(error_msg)
                print(f"  ❌ Keine erfolgreichen Chunk-Analysen")
                continue
            
            # Führe Ergebnisse zusammen
            print(f"  [4/4] Führe Ergebnisse zusammen...")
            merged_result = result_merger.merge_results(
                filename=pdf_path.name,
                chunk_results=chunk_results,
                check_attributes=config.check_attributes
            )
            
            if merged_result.error:
                print(f"  ❌ Fehler beim Zusammenführen: {merged_result.error}")
                stats.add_pdf_failure(f"{pdf_path.name}: {merged_result.error}")
            else:
                print(f"  ✓ Ergebnisse zusammengeführt")
                merged_results.append(merged_result)
                checkpoint.add(pdf_path.name, merged_to_dict(merged_result))
                checkpoint.save()
                stats.add_pdf_success(
                    chunk_count=len(chunks),
                    prompt_tokens=chunk_prompt_tokens,
                    completion_tokens=chunk_completion_tokens
                )
                
                # Zeige Zusammenfassung
                sentiment_str = {-1: "negativ", 0: "gemischt", 1: "positiv"}[merged_result.sentiment]
                print(f"\n  Zusammenfassung:")
                print(f"    - Sentiment: {sentiment_str}")
                print(f"    - Keywords: {', '.join(merged_result.keywords[:3])}")
                print(f"    - Chunks: {merged_result.chunk_count}")
                print(f"    - Tokens: {chunk_prompt_tokens + chunk_completion_tokens}")
        
        except PDFExtractionError as e:
            error_msg = f"{pdf_path.name}: {str(e)}"
            logger.error(error_msg)
            stats.add_pdf_failure(error_msg)
            print(f"  ❌ {e}")
            continue
        
        except Exception as e:
            error_msg = f"{pdf_path.name}: Unerwarteter Fehler: {str(e)}"
            logger.error(error_msg)
            stats.add_pdf_failure(error_msg)
            print(f"  ❌ Unerwarteter Fehler: {e}")
            continue
    
    # Zeige finale Statistiken
    print(f"\n{'='*60}")
    print("PDF-Verarbeitung abgeschlossen")
    print(f"{'='*60}")
    print(stats.summary())
    
    # Checkpoint aufräumen: Bei vollständigem Lauf löschen, sonst behalten
    if stats.failed_pdfs == 0 and merged_results:
        checkpoint.clear()
    
    logger.info(f"PDF-Verarbeitung abgeschlossen: {stats.successful_pdfs}/{stats.total_pdfs} erfolgreich")
    
    return merged_results, stats
