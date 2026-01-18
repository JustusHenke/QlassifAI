"""File Discovery Module für Excel-Dateien"""

from pathlib import Path
from typing import List
from logging_config import get_logger

logger = get_logger("file_discovery")


class FileDiscovery:
    """Durchsucht Verzeichnisse nach Excel-Dateien und präsentiert Auswahloptionen"""
    
    def __init__(self):
        """Initialisiert FileDiscovery"""
        pass
    
    def scan_directory(self, path: str = ".") -> List[Path]:
        """
        Scannt Verzeichnis nach .xlsx und .xls Dateien.
        
        Args:
            path: Pfad zum zu durchsuchenden Verzeichnis (default: aktuelles Verzeichnis)
            
        Returns:
            Liste von Pfaden zu gefundenen Excel-Dateien
        """
        directory = Path(path)
        
        if not directory.exists():
            logger.error(f"Verzeichnis existiert nicht: {directory}")
            return []
        
        if not directory.is_dir():
            logger.error(f"Pfad ist kein Verzeichnis: {directory}")
            return []
        
        # Suche nach Excel-Dateien
        excel_files = []
        
        # Suche .xlsx Dateien
        xlsx_files = list(directory.glob("*.xlsx"))
        excel_files.extend(xlsx_files)
        
        # Suche .xls Dateien
        xls_files = list(directory.glob("*.xls"))
        excel_files.extend(xls_files)
        
        # Sortiere alphabetisch
        excel_files.sort()
        
        logger.info(f"{len(excel_files)} Excel-Datei(en) gefunden in {directory}")
        
        return excel_files
    
    def present_file_selection(self, files: List[Path]) -> Path:
        """
        Zeigt interaktive Auswahl und gibt gewählte Datei zurück.
        
        Args:
            files: Liste von Excel-Dateien zur Auswahl
            
        Returns:
            Gewählte Datei als Path
            
        Raises:
            ValueError: Wenn keine Dateien vorhanden oder ungültige Auswahl
        """
        if not files:
            error_msg = "Keine Excel-Dateien zur Auswahl vorhanden"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        print("\n" + "=" * 60)
        print("Verfügbare Excel-Dateien:")
        print("=" * 60)
        
        for idx, file in enumerate(files, start=1):
            # Zeige Dateiname und Größe
            size_mb = file.stat().st_size / (1024 * 1024)
            print(f"{idx}. {file.name} ({size_mb:.2f} MB)")
        
        print("=" * 60)
        
        while True:
            try:
                choice = input(f"\nBitte wählen Sie eine Datei (1-{len(files)}): ").strip()
                
                # Erlaube auch direkte Eingabe des Dateinamens
                if choice in [f.name for f in files]:
                    selected_file = next(f for f in files if f.name == choice)
                    logger.info(f"Datei ausgewählt: {selected_file}")
                    return selected_file
                
                # Versuche als Nummer zu parsen
                choice_num = int(choice)
                
                if 1 <= choice_num <= len(files):
                    selected_file = files[choice_num - 1]
                    logger.info(f"Datei ausgewählt: {selected_file}")
                    return selected_file
                else:
                    print(f"Ungültige Auswahl. Bitte wählen Sie eine Zahl zwischen 1 und {len(files)}.")
                    
            except ValueError:
                print("Ungültige Eingabe. Bitte geben Sie eine Zahl ein.")
            except KeyboardInterrupt:
                print("\n\nAbbruch durch Benutzer.")
                logger.info("Dateiauswahl abgebrochen")
                raise
    
    def find_and_select_file(self, directory: str = ".") -> Path:
        """
        Kombiniert Scan und Auswahl in einer Methode.
        
        Args:
            directory: Verzeichnis zum Durchsuchen
            
        Returns:
            Gewählte Excel-Datei
            
        Raises:
            ValueError: Wenn keine Dateien gefunden
        """
        files = self.scan_directory(directory)
        
        if not files:
            error_msg = f"Keine Excel-Dateien gefunden in: {directory}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        return self.present_file_selection(files)
