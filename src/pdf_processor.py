"""PDF Processor für Qlassif-AI - PDF-Dateiverarbeitung und Textextraktion"""

import logging
from pathlib import Path
from typing import List, Dict, Any
import pdfplumber

logger = logging.getLogger(__name__)


class PDFExtractionError(Exception):
    """Fehler bei PDF-Textextraktion"""
    pass


class PDFProcessor:
    """Behandelt PDF-Dateioperationen"""
    
    def discover_pdfs(self, directory: Path) -> List[Path]:
        """
        Findet alle PDF-Dateien im Verzeichnis.
        
        Args:
            directory: Zu durchsuchendes Verzeichnis
            
        Returns:
            Liste von PDF-Dateipfaden
        """
        if not directory.exists():
            logger.error(f"Verzeichnis existiert nicht: {directory}")
            return []
        
        if not directory.is_dir():
            logger.error(f"Pfad ist kein Verzeichnis: {directory}")
            return []
        
        # Finde alle PDF-Dateien (case-insensitive)
        pdf_files = []
        for file_path in directory.iterdir():
            if file_path.is_file() and file_path.suffix.lower() == '.pdf':
                pdf_files.append(file_path)
        
        logger.info(f"{len(pdf_files)} PDF-Dateien in {directory} gefunden")
        return sorted(pdf_files)
    
    def extract_text(self, pdf_path: Path) -> str:
        """
        Extrahiert allen Text aus PDF-Datei.
        
        Args:
            pdf_path: Pfad zur PDF-Datei
            
        Returns:
            Extrahierter Textinhalt
            
        Raises:
            PDFExtractionError: Wenn Extraktion fehlschlägt
        """
        if not pdf_path.exists():
            error_msg = f"PDF-Datei existiert nicht: {pdf_path.name}"
            logger.error(error_msg)
            raise PDFExtractionError(error_msg)
        
        try:
            full_text = ""
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    page_text = page.extract_text()
                    if page_text:
                        full_text += page_text + "\n"
                    else:
                        logger.warning(
                            f"Seite {page_num} in {pdf_path.name} enthält keinen extrahierbaren Text"
                        )
            
            if not full_text.strip():
                error_msg = f"Kein Text aus {pdf_path.name} extrahiert (möglicherweise gescanntes Bild)"
                logger.error(error_msg)
                raise PDFExtractionError(error_msg)
            
            logger.info(
                f"Text aus {pdf_path.name} extrahiert: {len(full_text)} Zeichen"
            )
            return full_text
            
        except PDFExtractionError:
            raise
        except Exception as e:
            error_msg = f"Fehler beim Extrahieren von Text aus {pdf_path.name}: {str(e)}"
            logger.error(error_msg)
            raise PDFExtractionError(error_msg) from e
    
    def get_file_info(self, pdf_path: Path) -> Dict[str, Any]:
        """
        Holt Metadaten über PDF-Datei.
        
        Args:
            pdf_path: Pfad zur PDF-Datei
            
        Returns:
            Dictionary mit Schlüsseln: filename, size_bytes, page_count
        """
        info = {
            "filename": pdf_path.name,
            "size_bytes": 0,
            "page_count": 0
        }
        
        try:
            info["size_bytes"] = pdf_path.stat().st_size
            
            with pdfplumber.open(pdf_path) as pdf:
                info["page_count"] = len(pdf.pages)
            
            logger.debug(
                f"Info für {pdf_path.name}: {info['page_count']} Seiten, "
                f"{info['size_bytes']} Bytes"
            )
            
        except Exception as e:
            logger.warning(f"Fehler beim Abrufen von Info für {pdf_path.name}: {e}")
        
        return info
