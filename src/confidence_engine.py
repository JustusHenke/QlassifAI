"""Confidence Engine für wissenschaftliche Kodierungsqualität"""

import json
from typing import Dict, List, Optional, Tuple
from logging_config import get_logger

logger = get_logger("confidence_engine")


class ConfidenceEngine:
    """
    Extrahiert, validiert und verwaltet Konfidenz-Scores für LLM-Klassifikationen.
    
    Wird verwendet um:
    - Konfidenz aus LLM-JSON-Antworten zu extrahieren
    - Niedrige Konfidenz zu markieren
    - Alternative Klassifikationen bei Unsicherheit zu erfassen
    """
    
    # Standard-Schwellwerte
    DEFAULT_THRESHOLD = 0.7  # 70%
    
    @staticmethod
    def extract_confidence_from_response(response_data: dict, 
                                         check_attributes: List[dict],
                                         threshold: float = 0.7) -> Dict[str, dict]:
        """
        Extrahiert Konfidenz-Scores aus LLM-Antwort.
        
        Args:
            response_data: Geparste JSON-Antwort vom LLM
            check_attributes: Liste der Prüfmerkmale
            threshold: Schwellwert für niedrige Konfidenz
            
        Returns:
            Dict mit question -> {score, reasoning, alternatives, is_low}
        """
        confidence_results = {}
        
        # Prüfe ob Konfidenz-Daten vorhanden sind
        confidence_data = response_data.get("confidence", {})
        confidence_reasons = response_data.get("confidence_reasons", {})
        alternatives_data = response_data.get("alternatives", {})
        
        for attr in check_attributes:
            question = attr.get("question", "") if isinstance(attr, dict) else attr.question
            
            # Extrahiere Score
            score_raw = confidence_data.get(question)
            if score_raw is None:
                # Keine Konfidenz vorhanden
                confidence_results[question] = {
                    "score": None,
                    "reasoning": "",
                    "alternatives": [],
                    "is_low": False
                }
                continue
            
            # Normalisiere Score auf 0.0-1.0
            score = ConfidenceEngine._normalize_score(score_raw)
            
            # Extrahiere Begründung
            reasoning = confidence_reasons.get(question, "")
            
            # Extrahiere Alternativen
            alternatives = alternatives_data.get(question, [])
            if not isinstance(alternatives, list):
                alternatives = [alternatives] if alternatives else []
            
            # Prüfe Schwellwert
            is_low = score < threshold
            
            confidence_results[question] = {
                "score": score,
                "reasoning": reasoning,
                "alternatives": alternatives,
                "is_low": is_low
            }
            
            if is_low:
                logger.debug(f"Niedrige Konfidenz für '{question}': {score:.0%}")
        
        return confidence_results
    
    @staticmethod
    def _normalize_score(score) -> float:
        """
        Normalisiert einen Score auf 0.0-1.0.
        
        Args:
            score: Score als float (0.0-1.0) oder int (0-100)
            
        Returns:
            Normalisierter Score (0.0-1.0)
        """
        if score is None:
            return 0.0
        
        try:
            score = float(score)
        except (ValueError, TypeError):
            logger.warning(f"Konnte Score nicht parsen: {score}")
            return 0.0
        
        # Normalisiere von 0-100 zu 0.0-1.0
        if score > 1.0:
            score = score / 100.0
        
        # Begrenze auf 0.0-1.0
        return max(0.0, min(1.0, score))
    
    @staticmethod
    def mark_low_confidence_items(confidence_results: Dict[str, dict], 
                                   threshold: float = 0.7) -> List[str]:
        """
        Gibt Liste der Fragen mit niedriger Konfidenz zurück.
        
        Args:
            confidence_results: Dict von ConfidenceEngine.extract_confidence_from_response()
            threshold: Schwellwert
            
        Returns:
            Liste der Fragen mit score < threshold
        """
        low_confidence = []
        for question, data in confidence_results.items():
            score = data.get("score")
            if score is not None and score < threshold:
                low_confidence.append(question)
        return low_confidence
    
    @staticmethod
    def get_summary_statistics(confidence_results: Dict[str, dict]) -> dict:
        """
        Berechnet Zusammenfassungsstatistiken für Konfidenz-Scores.
        
        Args:
            confidence_results: Dict von ConfidenceEngine.extract_confidence_from_response()
            
        Returns:
            Dict mit min, max, mean, std, count, low_count
        """
        scores = [data["score"] for data in confidence_results.values() 
                  if data.get("score") is not None]
        
        if not scores:
            return {
                "min": 0.0, "max": 0.0, "mean": 0.0,
                "std": 0.0, "count": 0, "low_count": 0
            }
        
        mean = sum(scores) / len(scores)
        variance = sum((s - mean) ** 2 for s in scores) / len(scores)
        std = variance ** 0.5
        
        return {
            "min": min(scores),
            "max": max(scores),
            "mean": mean,
            "std": std,
            "count": len(scores),
            "low_count": sum(1 for s in scores if s < 0.7)
        }
    
    @staticmethod
    def build_confidence_prompt_section(check_attributes: List[dict],
                                         include_alternatives: bool = True) -> str:
        """
        Erstellt den Prompt-Zusatz für Konfidenz-Abfrage.
        
        Args:
            check_attributes: Prüfmerkmale
            include_alternatives: Ob Alternativen abgefragt werden sollen
            
        Returns:
            Prompt-Text für Konfidenz-Sektion
        """
        if not check_attributes:
            return ""
        
        prompt = """
Zusätzlich zu jeder Klassifikation liefere einen Konfidenz-Score und Begründung:

"""
        prompt += '"confidence": {\n'
        
        for attr in check_attributes:
            question = attr.get("question", "") if isinstance(attr, dict) else attr.question
            prompt += f'    "{question}": <score_0_100>,\n'
        
        prompt += """  },
  "confidence_reasons": {
"""
        
        for attr in check_attributes:
            question = attr.get("question", "") if isinstance(attr, dict) else attr.question
            prompt += f'    "{question}": "<max. 15 Wörter>",\n'
        
        prompt += "  }"
        
        if include_alternatives:
            prompt += """,
  "alternatives": {
"""
            for attr in check_attributes:
                question = attr.get("question", "") if isinstance(attr, dict) else attr.question
                prompt += f'    "{question}": ["Alternative1", "Alternative2"],\n'
            
            prompt += "  }"
        
        prompt += """

WICHTIG für Konfidenz:
- Score von 0-100 (0 = sehr unsicher, 100 = sehr sicher)
- Bei Score < 70: Gib 1-3 alternative Klassifikationen an
- Begründe die Konfidenz kurz (max. 15 Wörter)"""
        
        return prompt
    
    @staticmethod
    def merge_multiple_coders(coder_results: List[Dict[str, dict]], 
                               strategy: str = "highest_confidence") -> Dict[str, dict]:
        """
        Verschmilzt Konfidenz-Ergebnisse mehrerer Kodierer.
        
        Args:
            coder_results: Liste von confidence_results (pro Kodierer)
            strategy: "highest_confidence" oder "majority_vote"
            
        Returns:
            Verschmolzene Konfidenz-Ergebnisse
        """
        if not coder_results:
            return {}
        
        if len(coder_results) == 1:
            return coder_results[0]
        
        # Sammle alle Fragen
        all_questions = set()
        for results in coder_results:
            all_questions.update(results.keys())
        
        merged = {}
        
        for question in all_questions:
            scores = []
            reasonings = []
            alternatives = []
            
            for results in coder_results:
                if question in results:
                    data = results[question]
                    if data.get("score") is not None:
                        scores.append(data["score"])
                    if data.get("reasoning"):
                        reasonings.append(data["reasoning"])
                    alternatives.extend(data.get("alternatives", []))
            
            if not scores:
                merged[question] = {
                    "score": None,
                    "reasoning": "",
                    "alternatives": [],
                    "is_low": False,
                    "coder_count": 0,
                    "agreement": None
                }
                continue
            
            if strategy == "highest_confidence":
                best_idx = scores.index(max(scores))
                merged_score = scores[best_idx]
                merged_reasoning = reasonings[best_idx] if best_idx < len(reasonings) else ""
            else:  # majority_vote oder average
                merged_score = sum(scores) / len(scores)
                merged_reasoning = reasonings[0] if reasonings else ""
            
            # Prüfe Übereinstimmung (alle Scores nahe beieinander)
            if len(scores) >= 2:
                score_range = max(scores) - min(scores)
                agreement = score_range < 0.2  # Weniger als 20% Differenz
            else:
                agreement = True
            
            merged[question] = {
                "score": merged_score,
                "reasoning": merged_reasoning,
                "alternatives": list(set(alternatives)),  # Dedupliziert
                "is_low": merged_score < 0.7,
                "coder_count": len(scores),
                "agreement": agreement
            }
        
        return merged
