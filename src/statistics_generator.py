"""Statistics Generator für Kategorie-Auswertung"""

from pathlib import Path
from typing import Dict, List, Set
from openpyxl import Workbook
from logging_config import get_logger

logger = get_logger("statistics_generator")


class StatisticsGenerator:
    """Erstellt Auswertungsdatei mit Kategorie-Häufigkeiten"""
    
    def __init__(self):
        """Initialisiert StatisticsGenerator"""
        pass
    
    def calculate_category_frequencies(self, 
                                      category_assignments: List[List[str]]) -> Dict[str, int]:
        """
        Berechnet Häufigkeit jeder Kategorie.
        
        Args:
            category_assignments: Liste von Kategorie-Listen pro Antwort
            
        Returns:
            Dictionary mit Kategorie-Häufigkeiten
        """
        frequencies = {}
        
        for categories in category_assignments:
            for category in categories:
                frequencies[category] = frequencies.get(category, 0) + 1
        
        logger.info(f"Häufigkeiten für {len(frequencies)} Kategorien berechnet")
        return frequencies
    
    def calculate_per_sheet_frequencies(self,
                                       sheet_names: List[str],
                                       sheet_row_counts: List[int],
                                       category_assignments: List[List[str]]) -> Dict[str, Dict[str, int]]:
        """
        Berechnet Häufigkeit jeder Kategorie pro Sheet.
        
        Args:
            sheet_names: Namen der Sheets
            sheet_row_counts: Anzahl Zeilen pro Sheet
            category_assignments: Liste von Kategorie-Listen pro Antwort
            
        Returns:
            Dictionary mit Sheet-Namen als Keys und Kategorie-Häufigkeiten als Values
        """
        per_sheet_frequencies = {}
        
        # Initialisiere für jedes Sheet
        for sheet_name in sheet_names:
            per_sheet_frequencies[sheet_name] = {}
        
        # Verarbeite Ergebnisse pro Sheet
        current_index = 0
        for sheet_name, row_count in zip(sheet_names, sheet_row_counts):
            # Hole die Kategorie-Zuordnungen für dieses Sheet
            sheet_assignments = category_assignments[current_index:current_index + row_count]
            
            # Zähle Kategorien für dieses Sheet
            for categories in sheet_assignments:
                for category in categories:
                    per_sheet_frequencies[sheet_name][category] = \
                        per_sheet_frequencies[sheet_name].get(category, 0) + 1
            
            current_index += row_count
        
        logger.info(f"Per-Sheet-Häufigkeiten für {len(sheet_names)} Sheets berechnet")
        return per_sheet_frequencies
    
    def collect_keywords_per_category(self,
                                     category_mapping: Dict[str, List[str]]) -> Dict[str, Set[str]]:
        """
        Sammelt alle Keywords pro Kategorie.
        
        Args:
            category_mapping: Mapping von Kategorien zu Keywords
            
        Returns:
            Dictionary mit Kategorien und deduplizierten Keywords
        """
        keywords_per_category = {}
        
        for category, keywords in category_mapping.items():
            # Dedupliziere Keywords
            keywords_per_category[category] = set(keywords)
        
        logger.info(f"Keywords für {len(keywords_per_category)} Kategorien gesammelt")
        return keywords_per_category
    
    def create_statistics_workbook(self, 
                                  per_sheet_frequencies: Dict[str, Dict[str, int]],
                                  total_frequencies: Dict[str, int],
                                  keywords_per_category: Dict[str, Set[str]]) -> Workbook:
        """
        Erstellt neue Excel-Datei mit Statistiken (per Sheet + Gesamt).
        
        Args:
            per_sheet_frequencies: Kategorie-Häufigkeiten pro Sheet
            total_frequencies: Gesamt-Kategorie-Häufigkeiten
            keywords_per_category: Keywords pro Kategorie
            
        Returns:
            Workbook mit Statistiken
        """
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Kategorie-Statistiken"
        
        current_row = 1
        
        # Für jedes Sheet eine Sektion erstellen
        for sheet_name, frequencies in per_sheet_frequencies.items():
            # Sheet-Überschrift
            sheet.cell(row=current_row, column=1, value=f"Sheet: {sheet_name}")
            current_row += 1
            
            # Spaltenüberschriften
            sheet.cell(row=current_row, column=1, value="Kategorie")
            sheet.cell(row=current_row, column=2, value="Häufigkeit")
            sheet.cell(row=current_row, column=3, value="Keywords")
            current_row += 1
            
            # Sortiere Kategorien nach Häufigkeit (absteigend)
            sorted_categories = sorted(frequencies.items(), key=lambda x: x[1], reverse=True)
            
            # Schreibe Daten
            for category, frequency in sorted_categories:
                sheet.cell(row=current_row, column=1, value=category)
                sheet.cell(row=current_row, column=2, value=frequency)
                
                # Keywords kommagetrennt
                if category in keywords_per_category:
                    keywords_str = ", ".join(sorted(keywords_per_category[category]))
                    sheet.cell(row=current_row, column=3, value=keywords_str)
                
                current_row += 1
            
            # Leerzeile nach jedem Sheet
            current_row += 1
        
        # "Zusammen" Sektion
        sheet.cell(row=current_row, column=1, value="Zusammen")
        current_row += 1
        
        # Spaltenüberschriften
        sheet.cell(row=current_row, column=1, value="Kategorie")
        sheet.cell(row=current_row, column=2, value="Häufigkeit")
        sheet.cell(row=current_row, column=3, value="Keywords")
        current_row += 1
        
        # Sortiere Gesamt-Kategorien nach Häufigkeit (absteigend)
        sorted_total = sorted(total_frequencies.items(), key=lambda x: x[1], reverse=True)
        
        # Schreibe Gesamt-Daten
        for category, frequency in sorted_total:
            sheet.cell(row=current_row, column=1, value=category)
            sheet.cell(row=current_row, column=2, value=frequency)
            
            # Keywords kommagetrennt
            if category in keywords_per_category:
                keywords_str = ", ".join(sorted(keywords_per_category[category]))
                sheet.cell(row=current_row, column=3, value=keywords_str)
            
            current_row += 1
        
        logger.info(f"Statistik-Workbook mit {len(per_sheet_frequencies)} Sheets und Gesamt-Statistik erstellt")
        return workbook
    
    def save_statistics(self, workbook: Workbook, output_path: Path) -> None:
        """
        Speichert Statistik-Datei.
        
        Args:
            workbook: Zu speicherndes Workbook
            output_path: Zielpfad
        """
        workbook.save(output_path)
        logger.info(f"Statistik-Datei gespeichert: {output_path}")
        print(f"\n✓ Statistik-Datei gespeichert: {output_path}")
    
    def generate_statistics(self,
                           sheet_names: List[str],
                           sheet_row_counts: List[int],
                           category_assignments: List[List[str]],
                           category_mapping: Dict[str, List[str]],
                           output_path: Path) -> None:
        """
        Führt vollständige Statistik-Generierung durch.
        
        Args:
            sheet_names: Namen der Sheets
            sheet_row_counts: Anzahl Zeilen pro Sheet
            category_assignments: Kategorie-Zuordnungen
            category_mapping: Kategorie-Keyword-Mapping
            output_path: Zielpfad
        """
        # Berechne Per-Sheet-Häufigkeiten
        per_sheet_frequencies = self.calculate_per_sheet_frequencies(
            sheet_names, sheet_row_counts, category_assignments
        )
        
        # Berechne Gesamt-Häufigkeiten
        total_frequencies = self.calculate_category_frequencies(category_assignments)
        
        # Sammle Keywords
        keywords_per_category = self.collect_keywords_per_category(category_mapping)
        
        # Erstelle Workbook
        workbook = self.create_statistics_workbook(
            per_sheet_frequencies, total_frequencies, keywords_per_category
        )
        
        # Speichere
        self.save_statistics(workbook, output_path)
