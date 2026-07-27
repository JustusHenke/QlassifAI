"""Multi-Coder für parallele Kodierung durch mehrere LLM-Modelle"""

import json
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from models import CheckAttribute, AnalysisResult, ScientificConfig
from llm_analyzer import LLMAnalyzer
from confidence_engine import ConfidenceEngine
from kappa_calculator import KappaCalculator
from logging_config import get_logger

logger = get_logger("multi_coder")


@dataclass
class CoderResult:
    """Ergebnis eines einzelnen Kodierers"""
    model_name: str
    analysis_result: AnalysisResult
    confidence: Dict[str, dict]  # question -> confidence data


@dataclass
class IntercoderResult:
    """Vergleichsergebnis zwischen Kodierern"""
    coder_results: List[CoderResult]
    primary_coder_idx: int  # Index des primären Kodierers
    
    # Vergleichsdaten
    agreements: Dict[str, bool] = field(default_factory=dict)  # question -> übereinstimmend
    kappa_scores: Dict[str, dict] = field(default_factory=dict)  # question -> kappa results
    overall_kappa: float = 0.0
    overall_interpretation: str = ""
    
    @property
    def primary_coder(self) -> CoderResult:
        """Gibt den primären Kodierer zurück"""
        return self.coder_results[self.primary_coder_idx]
    
    @property
    def all_coder_results(self) -> List[CoderResult]:
        """Gibt alle Kodierer-Ergebnisse zurück"""
        return self.coder_results
    
    def get_coder_by_model(self, model_name: str) -> Optional[CoderResult]:
        """Gibt Kodierer nach Modellname zurück"""
        for coder in self.coder_results:
            if coder.model_name == model_name:
                return coder
        return None


class MultiCoder:
    """
    Verwaltet parallele Kodierung durch mehrere LLM-Modelle.
    
    Features:
    - Parallele Kodierung mit verschiedenen Modellen
    - Selektion des primären Kodierers
    - Berechnung von Kappa pro Prüfmerkmal
    - Identifikation von Übereinstimmungen und Abweichungen
    """
    
    def __init__(self, scientific_config: ScientificConfig):
        """
        Initialisiert MultiCoder.
        
        Args:
            scientific_config: Wissenschaftliche Konfiguration
        """
        self.config = scientific_config
        self._analyzers: Dict[str, LLMAnalyzer] = {}
    
    def add_analyzer(self, model_name: str, analyzer: LLMAnalyzer) -> None:
        """
        Fügt einen LLMAnalyzer für ein Modell hinzu.
        
        Args:
            model_name: Name des Modells
            analyzer: Initialisierter LLMAnalyzer
        """
        self._analyzers[model_name] = analyzer
        logger.info(f"Analyzer für Modell '{model_name}' hinzugefügt")
    
    def encode_text(self, text: str, check_attributes: List[CheckAttribute],
                    research_question: Optional[str] = None,
                    include_reasoning: bool = True) -> IntercoderResult:
        """
        Führt Kodierung durch alle Modelle durch.
        
        Args:
            text: Zu kodierender Text
            check_attributes: Prüfmerkmale
            research_question: Optionale Untersuchungsfrage
            include_reasoning: Ob Begründungen generiert werden sollen
            
        Returns:
            IntercoderResult mit allen Kodierungen und Vergleich
        """
        if len(self._analyzers) < 2:
            raise ValueError("Mindestens 2 Analyzer müssen hinzugefügt werden")
        
        logger.info(f"Multi-Coder Kodierung gestartet mit {len(self._analyzers)} Modellen")
        
        # Führe Kodierung durch alle Modelle durch
        coder_results = []
        
        for model_name, analyzer in self._analyzers.items():
            try:
                logger.info(f"Kodierung mit Modell '{model_name}'...")
                
                result = analyzer.analyze_text(
                    text=text,
                    check_attributes=check_attributes,
                    research_question=research_question,
                    include_reasoning=include_reasoning
                )
                
                # Extrahiere Konfidenz-Daten
                confidence = {}
                for attr in check_attributes:
                    question = attr.question
                    confidence[question] = {
                        "score": result.confidence_scores.get(question),
                        "reasoning": result.confidence_reasons.get(question, ""),
                        "alternatives": result.alternative_codes.get(question, [])
                    }
                
                coder_result = CoderResult(
                    model_name=model_name,
                    analysis_result=result,
                    confidence=confidence
                )
                
                coder_results.append(coder_result)
                logger.info(f"Kodierung mit '{model_name}' erfolgreich")
                
            except Exception as e:
                logger.error(f"Fehler bei Kodierung mit '{model_name}': {e}")
                # Erstelle Fehler-Ergebnis
                error_result = AnalysisResult(
                    paraphrase="",
                    sentiment="gemischt",
                    sentiment_reason="",
                    keywords=["fehler", model_name],
                    custom_checks={},
                    custom_checks_reasons={},
                    error=str(e)
                )
                coder_result = CoderResult(
                    model_name=model_name,
                    analysis_result=error_result,
                    confidence={}
                )
                coder_results.append(coder_result)
        
        # Selektiere primären Kodierer
        primary_idx = self._select_primary_coder(coder_results)
        
        # Erstelle IntercoderResult
        intercoder_result = IntercoderResult(
            coder_results=coder_results,
            primary_coder_idx=primary_idx
        )
        
        # Berechne Vergleichsstatistiken
        self._calculate_comparison(intercoder_result, check_attributes)
        
        logger.info(f"Multi-Coder Kodierung abgeschlossen, primärer Kodierer: {coder_results[primary_idx].model_name}")
        
        return intercoder_result
    
    def _select_primary_coder(self, coder_results: List[CoderResult]) -> int:
        """
        Wählt den primären Kodierer aus.
        
        Strategien:
        - "model_1": Erstes Modell in der Liste
        - "highest_confidence": Kodierer mit höchster Durchschnittskonfidenz
        
        Returns:
            Index des primären Kodierers
        """
        if self.config.primary_coder == "model_1":
            return 0
        
        # highest_confidence: Berechne Durchschnittskonfidenz pro Kodierer
        best_idx = 0
        best_confidence = -1
        
        for idx, coder in enumerate(coder_results):
            scores = [v.get("score", 0) for v in coder.confidence.values() if v.get("score") is not None]
            avg_confidence = sum(scores) / len(scores) if scores else 0
            
            if avg_confidence > best_confidence:
                best_confidence = avg_confidence
                best_idx = idx
        
        return best_idx
    
    def _calculate_comparison(self, intercoder_result: IntercoderResult,
                               check_attributes: List[CheckAttribute]) -> None:
        """
        Berechnet Vergleichsstatistiken zwischen Kodierern.
        """
        if len(intercoder_result.coder_results) < 2:
            return
        
        # Sammle Kodierungen pro Prüfmerkmal
        for attr in check_attributes:
            question = attr.question
            
            # Sammle Kodierungen aller Kodierer
            codings_per_coder = []
            for coder in intercoder_result.coder_results:
                coding = coder.analysis_result.custom_checks.get(question)
                if coding is not None:
                    codings_per_coder.append(str(coding))
                else:
                    codings_per_coder.append("nicht kodiert")
            
            # Prüfe Übereinstimmung (alle gleich?)
            agreements = [c == codings_per_coder[0] for c in codings_per_coder]
            intercoder_result.agreements[question] = all(agreements)
        
        # Berechne Kappa (paarweise für 2 Kodierer, Fleiss für >2)
        if len(intercoder_result.coder_results) == 2:
            self._calculate_pairwise_kappa(intercoder_result, check_attributes)
        else:
            self._calculate_fleiss_kappa(intercoder_result, check_attributes)
    
    def _calculate_pairwise_kappa(self, intercoder_result: IntercoderResult,
                                   check_attributes: List[CheckAttribute]) -> None:
        """Berechnet Cohen's Kappa für 2 Kodierer"""
        coder1 = intercoder_result.coder_results[0]
        coder2 = intercoder_result.coder_results[1]
        
        all_kappas = []
        
        for attr in check_attributes:
            question = attr.question
            
            # Sammle Kodierungen
            coding1 = str(coder1.analysis_result.custom_checks.get(question, "nicht kodiert"))
            coding2 = str(coder2.analysis_result.custom_checks.get(question, "nicht kodiert"))
            
            # Für Kappa brauchen wir mehrere Items
            # Hier: Ein Item pro Frage, daher vereinfachte Berechnung
            # In der Praxis: Über mehrere Texte hinweg berechnen
            
            # Vereinfachte Übereinstimmung
            agreement = 1.0 if coding1 == coding2 else 0.0
            
            intercoder_result.kappa_scores[question] = {
                "kappa": agreement,  # Vereinfacht: 1 bei Übereinstimmung, 0 sonst
                "ci_width": 0.0,
                "interpretation": KappaCalculator.interpret_kappa(agreement),
                "n": 1,
                "note": "Vereinfacht für einzelnes Item"
            }
            
            all_kappas.append(agreement)
        
        # Gesamt-Kappa (Durchschnitt)
        intercoder_result.overall_kappa = sum(all_kappas) / len(all_kappas) if all_kappas else 0.0
        intercoder_result.overall_interpretation = KappaCalculator.interpret_kappa(intercoder_result.overall_kappa)
    
    def _calculate_fleiss_kappa(self, intercoder_result: IntercoderResult,
                                 check_attributes: List[CheckAttribute]) -> None:
        """Berechnet vereinfachtes Kappa für >2 Kodierer"""
        # Für jedes Prüfmerkmal: Zähle Übereinstimmungen
        all_agreements = []
        
        for attr in check_attributes:
            question = attr.question
            
            # Sammle Kodierungen
            codings = []
            for coder in intercoder_result.coder_results:
                coding = str(coder.analysis_result.custom_checks.get(question, "nicht kodiert"))
                codings.append(coding)
            
            # Berechne Übereinstimmungsrate
            if codings:
                most_common = max(set(codings), key=codings.count)
                agreement = codings.count(most_common) / len(codings)
            else:
                agreement = 0.0
            
            intercoder_result.kappa_scores[question] = {
                "kappa": agreement,
                "ci_width": 0.0,
                "interpretation": KappaCalculator.interpret_kappa(agreement),
                "n": len(codings),
                "note": f"Vereinfacht für {len(codings)} Kodierer"
            }
            
            all_agreements.append(agreement)
        
        # Gesamt-Kappa
        intercoder_result.overall_kappa = sum(all_agreements) / len(all_agreements) if all_agreements else 0.0
        intercoder_result.overall_interpretation = KappaCalculator.interpret_kappa(intercoder_result.overall_kappa)
    
    def encode_batch(self, texts: List[str], check_attributes: List[CheckAttribute],
                     research_question: Optional[str] = None,
                     include_reasoning: bool = True) -> List[IntercoderResult]:
        """
        Führt Multi-Coder Kodierung für mehrere Texte durch.
        
        Args:
            texts: Liste von Texten
            check_attributes: Prüfmerkmale
            research_question: Optionale Untersuchungsfrage
            include_reasoning: Ob Begründungen generiert werden sollen
            
        Returns:
            Liste von IntercoderResult
        """
        results = []
        
        for idx, text in enumerate(texts):
            logger.info(f"Multi-Coder Kodierung {idx + 1}/{len(texts)}")
            
            result = self.encode_text(
                text=text,
                check_attributes=check_attributes,
                research_question=research_question,
                include_reasoning=include_reasoning
            )
            
            results.append(result)
        
        return results
    
    @staticmethod
    def aggregate_batch_results(batch_results: List[IntercoderResult]) -> Dict[str, dict]:
        """
        Aggregiert Ergebnisse aus einer Batch-Kodierung.
        
        Args:
            batch_results: Liste von IntercoderResult
            
        Returns:
            Aggregierte Statistiken
        """
        if not batch_results:
            return {}
        
        # Sammle alle Kappa-Ergebnisse
        all_kappas = {}
        for result in batch_results:
            for question, kappa_data in result.kappa_scores.items():
                if question not in all_kappas:
                    all_kappas[question] = []
                all_kappas[question].append(kappa_data["kappa"])
        
        # Aggregiere
        aggregated = {}
        for question, kappas in all_kappas.items():
            aggregated[question] = {
                "mean_kappa": sum(kappas) / len(kappas),
                "min_kappa": min(kappas),
                "max_kappa": max(kappas),
                "count": len(kappas)
            }
        
        # Gesamt-Statistiken
        if aggregated:
            mean_kappas = [v["mean_kappa"] for v in aggregated.values()]
            aggregated["__overall__"] = {
                "mean_kappa": sum(mean_kappas) / len(mean_kappas),
                "interpretation": KappaCalculator.interpret_kappa(sum(mean_kappas) / len(mean_kappas))
            }
        
        return aggregated
