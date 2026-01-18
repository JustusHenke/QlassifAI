"""Keyword Categorizer für thematische Gruppierung"""

import json
from typing import List, Dict, Set
from models import AnalysisResult, CategoryMapping
from llm_analyzer import LLMAnalyzer
from logging_config import get_logger

logger = get_logger("keyword_categorizer")


class KeywordCategorizer:
    """Gruppiert Keywords in Überkategorien"""
    
    def __init__(self, llm_analyzer: LLMAnalyzer):
        """
        Initialisiert KeywordCategorizer.
        
        Args:
            llm_analyzer: LLMAnalyzer-Instanz für Kategorisierung
        """
        self.llm_analyzer = llm_analyzer
    
    def collect_all_keywords(self, results: List[AnalysisResult]) -> List[str]:
        """
        Sammelt und dedupliziert alle Keywords.
        
        Args:
            results: Liste von AnalysisResult-Objekten
            
        Returns:
            Deduplizierte Liste von Keywords
        """
        keywords_set = set()
        
        for result in results:
            if result.error:
                continue
            for keyword in result.keywords:
                keywords_set.add(keyword.lower().strip())
        
        keywords_list = sorted(list(keywords_set))
        logger.info(f"{len(keywords_list)} eindeutige Keywords gesammelt")
        
        return keywords_list
    
    def generate_categories(self, keywords: List[str]) -> Dict[str, List[str]]:
        """
        Generiert Überkategorien mittels LLM.
        
        Args:
            keywords: Liste von Keywords
            
        Returns:
            Dictionary mit Kategorien und zugeordneten Keywords
        """
        if not keywords:
            logger.warning("Keine Keywords zum Kategorisieren")
            return {}
        
        # Baue Prompt
        keywords_str = ", ".join(keywords[:100])  # Limitiere auf 100 Keywords
        if len(keywords) > 100:
            keywords_str += f" ... (und {len(keywords) - 100} weitere)"
        
        prompt = f"""Gegeben ist folgende Liste von Keywords:
{keywords_str}

Entwickle 5-10 Überkategorien, die diese Keywords thematisch gruppieren.
Jedes Keyword sollte genau einer Kategorie zugeordnet werden.

Antwortformat (strikt einhalten):
{{
  "Kategorie_1": ["keyword1", "keyword2", ...],
  "Kategorie_2": ["keyword3", "keyword4", ...],
  ...
}}

WICHTIG: Antworte NUR mit dem JSON-Objekt, ohne zusätzlichen Text."""
        
        try:
            logger.info("Generiere Kategorien mit LLM...")
            
            response = self.llm_analyzer.client.chat.completions.create(
                model=self.llm_analyzer.model,
                messages=[
                    {"role": "system", "content": "Du bist ein Experte für thematische Kategorisierung. Antworte immer im JSON-Format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            response_text = response.choices[0].message.content.strip()
            categories = json.loads(response_text)
            
            logger.info(f"{len(categories)} Kategorien generiert")
            return categories
            
        except Exception as e:
            logger.error(f"Fehler bei Kategorie-Generierung: {e}")
            # Fallback: Erstelle einfache Kategorien
            return {"Allgemein": keywords}
    
    def assign_categories(self, result: AnalysisResult, 
                         category_mapping: Dict[str, List[str]]) -> List[str]:
        """
        Ordnet Keywords einer Antwort zu Kategorien zu.
        
        Args:
            result: AnalysisResult mit Keywords
            category_mapping: Mapping von Kategorien zu Keywords
            
        Returns:
            Liste von zugeordneten Kategorien
        """
        if result.error or not result.keywords:
            return ["Keine"]
        
        assigned_categories = set()
        
        # Suche für jedes Keyword die passende Kategorie
        for keyword in result.keywords:
            keyword_lower = keyword.lower().strip()
            
            for category, category_keywords in category_mapping.items():
                if keyword_lower in [k.lower() for k in category_keywords]:
                    assigned_categories.add(category)
                    break
        
        if not assigned_categories:
            return ["Keine"]
        
        return sorted(list(assigned_categories))
    
    def categorize_all(self, results: List[AnalysisResult]) -> tuple:
        """
        Führt vollständige Kategorisierung durch.
        
        Args:
            results: Liste von AnalysisResult-Objekten
            
        Returns:
            Tuple (category_mapping, category_assignments)
        """
        # Sammle Keywords
        all_keywords = self.collect_all_keywords(results)
        
        if not all_keywords:
            logger.warning("Keine Keywords gefunden, überspringe Kategorisierung")
            return {}, [["Keine"] for _ in results]
        
        # Generiere Kategorien
        category_mapping = self.generate_categories(all_keywords)
        
        # Ordne Kategorien zu
        category_assignments = []
        for result in results:
            categories = self.assign_categories(result, category_mapping)
            category_assignments.append(categories)
        
        logger.info("Kategorisierung abgeschlossen")
        return category_mapping, category_assignments
