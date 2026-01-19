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
                                        category_mapping: Dict[str, List[str]],
                                        output_path: Path) -> None:
        """
        Erstellt eine komplett neue Excel-Datei mit Originaldaten, Analyseergebnissen und Statistiken.
        
        Args:
            sheet_infos: Liste der SheetInfo-Objekte mit Originaldaten
            all_results: Liste aller AnalysisResult-Objekte
            category_assignments: Liste der Kategorie-Zuordnungen
            check_attributes: Prüfmerkmale
            category_mapping: Kategorie-Keyword-Mapping
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
                result_columns.append(f"{attr.question} (Begründung)")
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
                    reason = result.custom_checks_reasons.get(question, "")
                    
                    # Wert
                    if value is None:
                        new_sheet.cell(row=new_row_idx, column=start_col + col_offset, value="nicht kodiert")
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
                        elif attr.answer_type == "multi_categorical":
                            # Array zu kommasepariertem String konvertieren
                            if isinstance(value, list):
                                display_value = ", ".join(str(v) for v in value)
                            else:
                                display_value = str(value)
                            new_sheet.cell(row=new_row_idx, column=start_col + col_offset, value=display_value)
                        else:  # categorical
                            # Bereinige Pipe-Zeichen (falls LLM sie verwendet hat)
                            display_value = str(value).replace("|", ", ")
                            new_sheet.cell(row=new_row_idx, column=start_col + col_offset, value=display_value)
                    
                    col_offset += 1
                    
                    # Begründung
                    new_sheet.cell(row=new_row_idx, column=start_col + col_offset, value=reason if reason else "")
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
        
        # Füge Statistiken-Sheet hinzu
        stats_sheet = new_workbook.create_sheet(title="Statistiken")
        current_row = 1
        
        # Überschrift
        cell = stats_sheet.cell(row=current_row, column=1, value="Kategorie-Statistiken")
        cell.font = Font(bold=True, size=14)
        current_row += 2
        
        # Gesamt-Übersicht
        cell = stats_sheet.cell(row=current_row, column=1, value="Gesamt-Übersicht")
        cell.font = Font(bold=True)
        current_row += 1
        
        total_rows = len(all_results)
        stats_sheet.cell(row=current_row, column=1, value="Gesamt Zeilen:")
        stats_sheet.cell(row=current_row, column=2, value=total_rows)
        current_row += 2
        
        # Keyword-Kategorie-Häufigkeiten
        cell = stats_sheet.cell(row=current_row, column=1, value="Keyword-Kategorien")
        cell.font = Font(bold=True)
        current_row += 1
        
        # Header
        for col_idx, header in enumerate(["Kategorie", "Häufigkeit", "Keywords"], start=1):
            cell = stats_sheet.cell(row=current_row, column=col_idx, value=header)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = header_alignment
        current_row += 1
        
        # Zähle Kategorie-Häufigkeiten
        category_frequencies = {}
        for categories in category_assignments:
            for category in categories:
                if category:
                    category_frequencies[category] = category_frequencies.get(category, 0) + 1
        
        # Sortiere nach Häufigkeit
        sorted_categories = sorted(category_frequencies.items(), key=lambda x: x[1], reverse=True)
        
        # Schreibe Kategorie-Daten
        for category, frequency in sorted_categories:
            stats_sheet.cell(row=current_row, column=1, value=category)
            stats_sheet.cell(row=current_row, column=2, value=frequency)
            
            if category in category_mapping:
                keywords_str = ", ".join(sorted(category_mapping[category]))
                stats_sheet.cell(row=current_row, column=3, value=keywords_str)
            
            current_row += 1
        
        current_row += 1
        
        # Custom Check Zusammenfassungen
        if check_attributes:
            cell = stats_sheet.cell(row=current_row, column=1, value="Prüfmerkmale-Zusammenfassung")
            cell.font = Font(bold=True)
            current_row += 1
            
            # Header
            for col_idx, header in enumerate(["Prüfmerkmal", "Wert", "Häufigkeit"], start=1):
                cell = stats_sheet.cell(row=current_row, column=col_idx, value=header)
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = header_alignment
            current_row += 1
            
            for attr in check_attributes:
                question = attr.question
                
                # Zähle Werte für dieses Prüfmerkmal
                value_counts = {}
                for result in all_results:
                    value = result.custom_checks.get(question)
                    if value is not None:
                        # Konvertiere Boolean zu Ja/Nein
                        if attr.answer_type == "boolean":
                            if isinstance(value, bool):
                                display_value = "Ja" if value else "Nein"
                            else:
                                display_value = str(value)
                            value_counts[display_value] = value_counts.get(display_value, 0) + 1
                        elif attr.answer_type == "multi_categorical":
                            # Bei multi_categorical: Jede Kategorie einzeln zählen
                            if isinstance(value, list):
                                for v in value:
                                    display_value = str(v)
                                    value_counts[display_value] = value_counts.get(display_value, 0) + 1
                            else:
                                display_value = str(value)
                                value_counts[display_value] = value_counts.get(display_value, 0) + 1
                        else:
                            display_value = str(value)
                            value_counts[display_value] = value_counts.get(display_value, 0) + 1
                
                # Schreibe Prüfmerkmal-Daten
                if value_counts:
                    sorted_values = sorted(value_counts.items(), key=lambda x: x[1], reverse=True)
                    for idx, (value, count) in enumerate(sorted_values):
                        if idx == 0:
                            stats_sheet.cell(row=current_row, column=1, value=question)
                        stats_sheet.cell(row=current_row, column=2, value=value)
                        stats_sheet.cell(row=current_row, column=3, value=count)
                        current_row += 1
                else:
                    stats_sheet.cell(row=current_row, column=1, value=question)
                    stats_sheet.cell(row=current_row, column=2, value="(keine Daten)")
                    current_row += 1
        
        # Speichere neue Datei
        new_workbook.save(output_path)
        logger.info(f"Neue Workbook mit Statistiken erstellt und gespeichert: {output_path}")
        print(f"\n✓ Neue Excel-Datei mit Statistiken erstellt: {output_path}")

    def create_pdf_results_workbook(self,
                                    merged_results: List,  # List[MergedResult]
                                    check_attributes: List[CheckAttribute],
                                    category_mapping: Dict[str, List[str]],
                                    output_path: Path) -> None:
        """
        Erstellt Excel-Datei mit PDF-Analyseergebnissen und Statistiken.
        
        Args:
            merged_results: Liste von MergedResult-Objekten
            check_attributes: Prüfmerkmale
            category_mapping: Kategorie-Keyword-Mapping
            output_path: Pfad für die neue Datei
        """
        # Erstelle neues Workbook
        workbook = Workbook()
        
        # Sheet 1: Analyseergebnisse
        sheet = workbook.active
        sheet.title = "Analyseergebnisse"
        
        # Definiere bläuliches Theme
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF")
        header_alignment = Alignment(horizontal="center", vertical="center")
        
        # Erstelle Header-Zeile
        headers = ["Dateiname", "Paraphrase", "Sentiment", "Sentiment_Begründung", "Keywords"]
        for attr in check_attributes:
            headers.append(attr.question)
            headers.append(f"{attr.question} (Begründung)")
        headers.extend(["Keyword_Kategorie", "Chunk_Anzahl"])
        
        for col_idx, header in enumerate(headers, start=1):
            cell = sheet.cell(row=1, column=col_idx, value=header)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = header_alignment
        
        # Füge Datenzeilen hinzu
        for row_idx, result in enumerate(merged_results, start=2):
            col_idx = 1
            
            # Dateiname
            sheet.cell(row=row_idx, column=col_idx, value=result.filename)
            col_idx += 1
            
            # Paraphrase
            sheet.cell(row=row_idx, column=col_idx, value=result.paraphrase)
            col_idx += 1
            
            # Sentiment (konvertiere -1, 0, 1 zu Text)
            sentiment_map = {-1: "negativ", 0: "gemischt", 1: "positiv"}
            sentiment_str = sentiment_map.get(result.sentiment, "gemischt")
            sheet.cell(row=row_idx, column=col_idx, value=sentiment_str)
            col_idx += 1
            
            # Sentiment_Begründung
            sheet.cell(row=row_idx, column=col_idx, value=result.sentiment_reason)
            col_idx += 1
            
            # Keywords
            keywords_str = ", ".join(result.keywords) if result.keywords else ""
            sheet.cell(row=row_idx, column=col_idx, value=keywords_str)
            col_idx += 1
            
            # Custom Checks
            for attr in check_attributes:
                question = attr.question
                value = result.custom_checks.get(question)
                reason = result.custom_checks_reasons.get(question, "")
                
                # Wert
                if value is None:
                    sheet.cell(row=row_idx, column=col_idx, value="nicht kodiert")
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
                        sheet.cell(row=row_idx, column=col_idx, value=display_value)
                    elif attr.answer_type == "multi_categorical":
                        # Array zu kommasepariertem String konvertieren
                        if isinstance(value, list):
                            display_value = ", ".join(str(v) for v in value)
                        else:
                            display_value = str(value)
                        sheet.cell(row=row_idx, column=col_idx, value=display_value)
                    else:  # categorical
                        # Bereinige Pipe-Zeichen (falls LLM sie verwendet hat)
                        display_value = str(value).replace("|", ", ")
                        sheet.cell(row=row_idx, column=col_idx, value=display_value)
                
                col_idx += 1
                
                # Begründung
                sheet.cell(row=row_idx, column=col_idx, value=reason if reason else "")
                col_idx += 1
            
            # Keyword_Kategorie
            sheet.cell(row=row_idx, column=col_idx, value=result.keyword_category)
            col_idx += 1
            
            # Chunk_Anzahl
            sheet.cell(row=row_idx, column=col_idx, value=result.chunk_count)
        
        # Aktiviere Autofilter
        if sheet.max_row > 0 and sheet.max_column > 0:
            sheet.auto_filter.ref = sheet.dimensions
            logger.info(f"Autofilter aktiviert für PDF-Ergebnisse")
        
        # Sheet 2: Statistiken
        stats_sheet = workbook.create_sheet(title="Statistiken")
        current_row = 1
        
        # Überschrift
        cell = stats_sheet.cell(row=current_row, column=1, value="PDF-Analyse Statistiken")
        cell.font = Font(bold=True, size=14)
        current_row += 2
        
        # Gesamt-Übersicht
        cell = stats_sheet.cell(row=current_row, column=1, value="Gesamt-Übersicht")
        cell.font = Font(bold=True)
        current_row += 1
        
        total_pdfs = len(merged_results)
        total_chunks = sum(r.chunk_count for r in merged_results)
        
        stats_sheet.cell(row=current_row, column=1, value="Gesamt PDFs:")
        stats_sheet.cell(row=current_row, column=2, value=total_pdfs)
        current_row += 1
        
        stats_sheet.cell(row=current_row, column=1, value="Gesamt Chunks:")
        stats_sheet.cell(row=current_row, column=2, value=total_chunks)
        current_row += 2
        
        # Keyword-Kategorie-Häufigkeiten
        cell = stats_sheet.cell(row=current_row, column=1, value="Keyword-Kategorien")
        cell.font = Font(bold=True)
        current_row += 1
        
        # Header
        for col_idx, header in enumerate(["Kategorie", "Häufigkeit", "Keywords"], start=1):
            cell = stats_sheet.cell(row=current_row, column=col_idx, value=header)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = header_alignment
        current_row += 1
        
        # Zähle Kategorie-Häufigkeiten
        category_frequencies = {}
        for result in merged_results:
            if result.keyword_category:
                categories = [c.strip() for c in result.keyword_category.split(",")]
                for category in categories:
                    if category:
                        category_frequencies[category] = category_frequencies.get(category, 0) + 1
        
        # Sortiere nach Häufigkeit
        sorted_categories = sorted(category_frequencies.items(), key=lambda x: x[1], reverse=True)
        
        # Schreibe Kategorie-Daten
        for category, frequency in sorted_categories:
            stats_sheet.cell(row=current_row, column=1, value=category)
            stats_sheet.cell(row=current_row, column=2, value=frequency)
            
            if category in category_mapping:
                keywords_str = ", ".join(sorted(category_mapping[category]))
                stats_sheet.cell(row=current_row, column=3, value=keywords_str)
            
            current_row += 1
        
        current_row += 1
        
        # Custom Check Zusammenfassungen
        if check_attributes:
            cell = stats_sheet.cell(row=current_row, column=1, value="Prüfmerkmale-Zusammenfassung")
            cell.font = Font(bold=True)
            current_row += 1
            
            # Header
            for col_idx, header in enumerate(["Prüfmerkmal", "Wert", "Häufigkeit"], start=1):
                cell = stats_sheet.cell(row=current_row, column=col_idx, value=header)
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = header_alignment
            current_row += 1
            
            for attr in check_attributes:
                question = attr.question
                
                # Zähle Werte für dieses Prüfmerkmal
                value_counts = {}
                for result in merged_results:
                    value = result.custom_checks.get(question)
                    if value is not None:
                        # Konvertiere Boolean zu Ja/Nein
                        if attr.answer_type == "boolean":
                            if isinstance(value, bool):
                                display_value = "Ja" if value else "Nein"
                            else:
                                display_value = str(value)
                            value_counts[display_value] = value_counts.get(display_value, 0) + 1
                        elif attr.answer_type == "multi_categorical":
                            # Bei multi_categorical: Jede Kategorie einzeln zählen
                            if isinstance(value, list):
                                for v in value:
                                    display_value = str(v)
                                    value_counts[display_value] = value_counts.get(display_value, 0) + 1
                            else:
                                display_value = str(value)
                                value_counts[display_value] = value_counts.get(display_value, 0) + 1
                        else:
                            display_value = str(value)
                            value_counts[display_value] = value_counts.get(display_value, 0) + 1
                
                # Schreibe Prüfmerkmal-Daten
                if value_counts:
                    sorted_values = sorted(value_counts.items(), key=lambda x: x[1], reverse=True)
                    for idx, (value, count) in enumerate(sorted_values):
                        if idx == 0:
                            stats_sheet.cell(row=current_row, column=1, value=question)
                        stats_sheet.cell(row=current_row, column=2, value=value)
                        stats_sheet.cell(row=current_row, column=3, value=count)
                        current_row += 1
                else:
                    stats_sheet.cell(row=current_row, column=1, value=question)
                    stats_sheet.cell(row=current_row, column=2, value="(keine Daten)")
                    current_row += 1
        
        # Speichere Datei
        workbook.save(output_path)
        logger.info(f"PDF-Ergebnisse mit Statistiken gespeichert: {output_path}")
        print(f"\n✓ PDF-Analysedatei mit Statistiken erstellt: {output_path}")
