"""Result Merger für Qlassif-AI - Führt Chunk-Analyseergebnisse zusammen"""

import logging
from typing import List, Dict, Union
from collections import Counter
from models import AnalysisResult, CheckAttribute, MergedResult

logger = logging.getLogger(__name__)


class ResultMerger:
    """Führt Chunk-Analyseergebnisse zusammen"""
    
    # Sentiment-Mapping für Durchschnittsberechnung
    SENTIMENT_MAP = {
        "positiv": 1,
        "gemischt": 0,
        "negativ": -1
    }
    
    SENTIMENT_REVERSE_MAP = {
        1: "positiv",
        0: "gemischt",
        -1: "negativ"
    }
    
    def merge_results(
        self,
        filename: str,
        chunk_results: List[AnalysisResult],
        check_attributes: List[CheckAttribute]
    ) -> MergedResult:
        """
        Führt mehrere Chunk-Ergebnisse zu einem Dokument-Ergebnis zusammen.
        
        Args:
            filename: PDF-Dateiname
            chunk_results: Liste von AnalysisResult von jedem Chunk
            check_attributes: Konfiguration für benutzerdefinierte Prüfungen
            
        Returns:
            MergedResult mit kombinierter Analyse
        """
        if not chunk_results:
            logger.error(f"Keine Chunk-Ergebnisse zum Zusammenführen für {filename}")
            return MergedResult(
                filename=filename,
                paraphrase="",
                sentiment=0,
                sentiment_reason="",
                keywords=[],
                custom_checks={},
                custom_checks_reasons={},
                keyword_category="",
                chunk_count=0,
                error="Keine Chunk-Ergebnisse verfügbar"
            )
        
        try:
            # Führe Felder zusammen
            paraphrase = self._merge_paraphrases(chunk_results)
            sentiment = self._merge_sentiments(chunk_results)
            sentiment_reason = self._merge_sentiment_reasons(chunk_results)
            keywords = self._merge_keywords(chunk_results)
            custom_checks = self._merge_custom_checks(chunk_results, check_attributes)
            custom_checks_reasons = self._merge_custom_checks_reasons(chunk_results, check_attributes)
            
            logger.info(
                f"Ergebnisse für {filename} zusammengeführt: "
                f"{len(chunk_results)} Chunks, Sentiment={sentiment}"
            )
            
            return MergedResult(
                filename=filename,
                paraphrase=paraphrase,
                sentiment=sentiment,
                sentiment_reason=sentiment_reason,
                keywords=keywords,
                custom_checks=custom_checks,
                custom_checks_reasons=custom_checks_reasons,
                keyword_category="",  # Wird später von KeywordCategorizer gesetzt
                chunk_count=len(chunk_results)
            )
            
        except Exception as e:
            error_msg = f"Fehler beim Zusammenführen von Ergebnissen für {filename}: {e}"
            logger.error(error_msg)
            return MergedResult(
                filename=filename,
                paraphrase="",
                sentiment=0,
                sentiment_reason="",
                keywords=[],
                custom_checks={},
                custom_checks_reasons={},
                keyword_category="",
                chunk_count=len(chunk_results),
                error=error_msg
            )
    
    def _merge_paraphrases(self, results: List[AnalysisResult]) -> str:
        """
        Verkettet Paraphrasen mit Trennzeichen.
        
        Args:
            results: Liste von AnalysisResult
            
        Returns:
            Zusammengeführte Paraphrase
        """
        paraphrases = [r.paraphrase for r in results if r.paraphrase]
        return " | ".join(paraphrases)
    
    def _merge_sentiments(self, results: List[AnalysisResult]) -> int:
        """
        Berechnet mittleres Sentiment als -1, 0 oder 1.
        
        Args:
            results: Liste von AnalysisResult
            
        Returns:
            -1 (negativ), 0 (gemischt) oder 1 (positiv)
        """
        numeric_sentiments = [
            self.SENTIMENT_MAP[r.sentiment] for r in results
        ]
        mean_sentiment = sum(numeric_sentiments) / len(numeric_sentiments)
        
        # Runde auf nächste Ganzzahl
        if mean_sentiment > 0.5:
            return 1  # positiv
        elif mean_sentiment < -0.5:
            return -1  # negativ
        else:
            return 0  # gemischt
    
    def _merge_sentiment_reasons(self, results: List[AnalysisResult]) -> str:
        """
        Verkettet Sentiment-Gründe mit Trennzeichen.
        
        Args:
            results: Liste von AnalysisResult
            
        Returns:
            Zusammengeführte Sentiment-Gründe
        """
        reasons = [r.sentiment_reason for r in results if r.sentiment_reason]
        return " | ".join(reasons)
    
    def _merge_keywords(self, results: List[AnalysisResult]) -> List[str]:
        """
        Kombiniert und dedupliziert Keywords.
        
        Args:
            results: Liste von AnalysisResult
            
        Returns:
            Liste der häufigsten Keywords (max 4)
        """
        # Sammle alle Keywords
        all_keywords = []
        for result in results:
            all_keywords.extend(result.keywords)
        
        # Zähle Häufigkeiten
        keyword_counts = Counter(all_keywords)
        
        # Nimm die 4 häufigsten Keywords
        most_common = keyword_counts.most_common(4)
        
        # Extrahiere nur die Keywords (ohne Counts)
        merged_keywords = [keyword for keyword, count in most_common]
        
        # Stelle sicher, dass mindestens 2 Keywords vorhanden sind
        if len(merged_keywords) < 2:
            # Fülle mit "unbekannt" auf
            while len(merged_keywords) < 2:
                merged_keywords.append("unbekannt")
        
        logger.debug(
            f"Keywords zusammengeführt: {len(all_keywords)} gesamt -> "
            f"{len(merged_keywords)} eindeutig"
        )
        
        return merged_keywords
    
    def _merge_custom_checks(
        self,
        results: List[AnalysisResult],
        check_attributes: List[CheckAttribute]
    ) -> Dict[str, Union[str, bool, List[str]]]:
        """
        Wendet feldspezifische Zusammenführungsregeln an.
        
        Args:
            results: Liste von AnalysisResult
            check_attributes: Konfiguration für benutzerdefinierte Prüfungen
            
        Returns:
            Dictionary mit zusammengeführten benutzerdefinierten Prüfungen
        """
        merged_checks = {}
        
        for attr in check_attributes:
            question = attr.question
            
            # Sammle alle Werte für diese Prüfung
            values = [
                r.custom_checks.get(question)
                for r in results
                if question in r.custom_checks
            ]
            
            if not values:
                merged_checks[question] = None
                continue
            
            if attr.answer_type == "boolean":
                # Boolean: OR-Logik (true wenn irgendein Chunk true ist)
                merged_checks[question] = any(
                    v is True for v in values if v is not None
                )
            
            elif attr.answer_type == "multi_categorical":
                # Multi-Categorical: Sammle alle Kategorien aus allen Chunks
                all_categories = []
                for v in values:
                    if v is not None:
                        if isinstance(v, list):
                            all_categories.extend(v)
                        elif v != "":
                            all_categories.append(v)
                
                if all_categories:
                    # Dedupliziere und behalte Reihenfolge
                    unique_categories = list(dict.fromkeys(all_categories))
                    merged_checks[question] = unique_categories
                else:
                    merged_checks[question] = None
            
            elif attr.answer_type == "categorical":
                # Categorical: Sammle alle Nicht-Null-Werte
                non_null_values = [v for v in values if v is not None and v != ""]
                if non_null_values:
                    # Entferne Duplikate und verbinde mit Komma
                    unique_values = list(dict.fromkeys(non_null_values))
                    merged_checks[question] = ", ".join(unique_values)
                else:
                    merged_checks[question] = None
        
        return merged_checks
    
    def _merge_custom_checks_reasons(
        self,
        results: List[AnalysisResult],
        check_attributes: List[CheckAttribute]
    ) -> Dict[str, str]:
        """
        Führt Begründungen für custom_checks zusammen.
        
        Args:
            results: Liste von AnalysisResult
            check_attributes: Konfiguration für benutzerdefinierte Prüfungen
            
        Returns:
            Dictionary mit zusammengeführten Begründungen
        """
        merged_reasons = {}
        
        for attr in check_attributes:
            question = attr.question
            
            # Sammle alle Begründungen für diese Prüfung
            reasons = [
                r.custom_checks_reasons.get(question, "")
                for r in results
                if question in r.custom_checks_reasons and r.custom_checks_reasons.get(question)
            ]
            
            if reasons:
                # Verknüpfe Begründungen mit Pipe-Zeichen
                merged_reasons[question] = " | ".join(reasons)
            else:
                merged_reasons[question] = ""
        
        return merged_reasons
