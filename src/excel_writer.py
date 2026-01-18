"""Excel Writer für Ergebnisse"""

from pathlib import Path
from typing import Dict, List, Tuple
from openpyxl import Workbook
from openpyxl.worksheet.worksheet import Worksheet
from openpyxl.styles import Font, PatternFill, Alignment
from models import CheckAttribute, AnalysisResult, SheetInfo
from logging_config import get_logger

logger = get_logger("excel_writer")


class ExcelWriter:
    """Schreibt Analyseergebnisse in neue Excel-Datei"""
    
    def __init__(self):
        """Initialisiert ExcelWriter"""
        pass
    
    def create_new_workbook_with_results(self, 
                                        sheet_infos: List[SheetInfo],
                                        all_results: List[AnalysisResult],
                                        category_assignments: List[List[str]],
                                        check_attributes: List[CheckAttribute],
                                        output_path: Path) -> None:
        """
        Erstellt eine komplett neue Excel-Datei mit Originaldaten und Analyseergebnissen.
        
        Args:
            sheet_infos: Liste der SheetInfo-Objekte mit Originaldaten
            all_results: Liste aller AnalysisResult-Objekte
            category_assignments: Liste der Kategorie-Zuordnungen
            check_attributes: Prüfmerkmale
            output_path: Pfad für die neue Datei
        """
        # Erstelle neues Workbook
        new_workbook = Workbook()
        new_workbook.remove(new_workbook.active)  # Entferne Standard-Sheet
        
        # Definiere bläuliches Theme
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF")
        header_alignment = Alignment(horizontal="center", vertical="center")
        
        result_idx = 0
        
        for sheet_info in sheet_infos:
            # Erstelle neues Sheet
            new_sheet = new_workbook.create_sheet(title=sheet_info.name)
            
            # Kopiere Header-Zeile aus Original
            original_sheet = sheet_info.sheet
            header_row_idx = sheet_info.header_row_index
            
            # Kopiere alle Spalten der Header-Zeile
            col_count = original_sheet.max_column
            for col_idx in range(1, col_count + 1):
                cell_value = original_sheet.cell(row=header_row_idx, column=col_idx).value
                header_cell = new_sheet.cell(row=1, column=col_idx, value=cell_value)
                # Wende bläuliches Theme auf Header an
                header_cell.fill = header_fill
                header_cell.font = header_font
                header_cell.alignment = header_alignment
            
            # Füge neue Spaltenüberschriften hinzu
            result_columns = ["Paraphrase", "Sentiment", "Sentiment_Begründung", "Keywords"]
            for attr in check_attributes:
                result_columns.append(attr.question)
            result_columns.append("Keyword_Kategorie")
            
            start_col = col_count + 1
            for idx, col_name in enumerate(result_columns):
                header_cell = new_sheet.cell(row=1, column=start_col + idx, value=col_name)
                # Wende bläuliches Theme auf neue Spalten an
                header_cell.fill = header_fill
                header_cell.font = header_font
                header_cell.alignment = header_alignment
            
            # Kopiere Datenzeilen und füge Ergebnisse hinzu
            new_row_idx = 2
            for original_row_idx in sheet_info.data_rows:
                # Kopiere Originaldaten
                for col_idx in range(1, col_count + 1):
                    cell_value = original_sheet.cell(row=original_row_idx, column=col_idx).value
                    new_sheet.cell(row=new_row_idx, column=col_idx, value=cell_value)
                
                # Füge Analyseergebnisse hinzu
                result = all_results[result_idx]
                categories = category_assignments[result_idx]
                
                # Paraphrase
                new_sheet.cell(row=new_row_idx, column=start_col, value=result.paraphrase)
                
                # Sentiment
                new_sheet.cell(row=new_row_idx, column=start_col + 1, value=result.sentiment)
                
                # Sentiment_Begründung
                new_sheet.cell(row=new_row_idx, column=start_col + 2, value=result.sentiment_reason)
                
                # Keywords
                keywords_str = ", ".join(result.keywords)
                new_sheet.cell(row=new_row_idx, column=start_col + 3, value=keywords_str)
                
                # Custom Checks
                attr_map = {attr.question: attr for attr in check_attributes}
                col_offset = 4
                for attr in check_attributes:
                    question = attr.question
                    value = result.custom_checks.get(question)
                    
                    if value is None:
                        new_sheet.cell(row=new_row_idx, column=start_col + col_offset, value="")
                    else:
                        # Boolean zu Ja/Nein konvertieren
                        if attr.answer_type == "boolean":
                            if isinstance(value, bool):
                                display_value = "Ja" if value else "Nein"
                            elif str(value).lower() == "true":
                                display_value = "Ja"
                            elif str(value).lower() == "false":
                                display_value = "Nein"
                            else:
                                display_value = str(value)
                            new_sheet.cell(row=new_row_idx, column=start_col + col_offset, value=display_value)
                        else:
                            new_sheet.cell(row=new_row_idx, column=start_col + col_offset, value=str(value))
                    
                    col_offset += 1
                
                # Keyword_Kategorie
                categories_str = ", ".join(categories)
                new_sheet.cell(row=new_row_idx, column=start_col + col_offset, value=categories_str)
                
                new_row_idx += 1
                result_idx += 1
            
            # Aktiviere Autofilter
            if new_sheet.max_row > 0 and new_sheet.max_column > 0:
                new_sheet.auto_filter.ref = new_sheet.dimensions
                logger.info(f"Autofilter aktiviert für Sheet '{new_sheet.title}'")
        
        # Speichere neue Datei
        new_workbook.save(output_path)
        logger.info(f"Neue Workbook erstellt und gespeichert: {output_path}")
        print(f"\n✓ Neue Excel-Datei erstellt: {output_path}")
