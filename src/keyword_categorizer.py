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
        
        # Baue Prompt mit allen Keywords
        keywords_str = "\n".join([f"- {kw}" for kw in keywords[:150]])  # Limitiere auf 150 Keywords
        if len(keywords) > 150:
            keywords_str += f"\n... (und {len(keywords) - 150} weitere)"
        
        prompt = f"""Gegeben ist folgende Liste von Keywords aus Textantworten:
{keywords_str}

Entwickle 5-10 thematische Überkategorien, die diese Keywords sinnvoll gruppieren.
WICHTIG: Jedes Keyword aus der Liste muss GENAU EINER Kategorie zugeordnet werden.
Achte besonders auf Multi-Word-Keywords (z.B. "finanzielle Unterstützung", "soziales Engagement").

Antwortformat (strikt einhalten):
{{
  "Kategorie_1": ["keyword1", "keyword2", "multi word keyword", ...],
  "Kategorie_2": ["keyword3", "keyword4", ...],
  ...
}}

WICHTIG: 
- Antworte NUR mit dem JSON-Objekt, ohne zusätzlichen Text
- Verwende die EXAKTEN Keywords aus der Liste (inklusive Groß-/Kleinschreibung)
- Jedes Keyword muss zugeordnet werden"""
        
        try:
            logger.info("Generiere Kategorien mit LLM...")
            
            response = self.llm_analyzer.client.chat.completions.create(
                model=self.llm_analyzer.model,
                messages=[
                    {"role": "system", "content": "Du bist ein Experte für thematische Kategorisierung. Antworte immer im JSON-Format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=3000
            )
            
            response_text = response.choices[0].message.content.strip()
            categories = json.loads(response_text)
            
            logger.info(f"{len(categories)} Kategorien generiert")
            
            # Zähle zugeordnete Keywords
            total_assigned = sum(len(kws) for kws in categories.values())
            logger.info(f"{total_assigned} von {len(keywords)} Keywords zugeordnet")
            
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
            - "Keine": Wenn Fehler oder keine Keywords vorhanden
            - "Sonstiges": Wenn Keywords vorhanden, aber keine Kategorie gefunden
        """
        # Fall 1: Fehler oder keine Keywords -> "Keine"
        if result.error or not result.keywords:
            return ["Keine"]
        
        assigned_categories = set()
        
        # Suche für jedes Keyword die passende Kategorie
        for keyword in result.keywords:
            keyword_lower = keyword.lower().strip()
            category_found = False
            
            # Exakte Suche
            for category, category_keywords in category_mapping.items():
                if keyword_lower in [k.lower() for k in category_keywords]:
                    assigned_categories.add(category)
                    category_found = True
                    break
            
            # Falls nicht gefunden: Teil-Match (für Multi-Word-Keywords)
            if not category_found:
                for category, category_keywords in category_mapping.items():
                    for cat_keyword in category_keywords:
                        cat_keyword_lower = cat_keyword.lower()
                        # Prüfe ob eines im anderen enthalten ist
                        if (cat_keyword_lower in keyword_lower or 
                            keyword_lower in cat_keyword_lower):
                            assigned_categories.add(category)
                            category_found = True
                            break
                    if category_found:
                        break
            
            # Falls immer noch nicht gefunden: Wort-für-Wort-Vergleich
            if not category_found:
                keyword_words = set(keyword_lower.split())
                for category, category_keywords in category_mapping.items():
                    for cat_keyword in category_keywords:
                        cat_words = set(cat_keyword.lower().split())
                        # Wenn mindestens ein Wort übereinstimmt
                        if keyword_words & cat_words:
                            assigned_categories.add(category)
                            category_found = True
                            break
                    if category_found:
                        break
        
        # Fall 2: Keywords vorhanden, aber keine Kategorie gefunden -> "Sonstiges"
        if not assigned_categories:
            logger.warning(f"Keine Kategorie gefunden für Keywords: {result.keywords}")
            return ["Sonstiges"]
        
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
