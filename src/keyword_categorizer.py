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
    
    def generate_categories(self, keywords: List[str]) -> Dict[str, str]:
        """
        Generiert Überkategorien mittels LLM.
        WICHTIG: Jedes Keyword wird GENAU EINER Kategorie zugeordnet (1:1 Mapping).
        
        Args:
            keywords: Liste von Keywords
            
        Returns:
            Dictionary mit Keyword -> Kategorie Mapping
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
WICHTIG: 
- Jedes Keyword muss GENAU EINER Kategorie zugeordnet werden (1:1 Mapping)
- Mehrdeutige Keywords, die nicht eindeutig zuordenbar sind, ordne der Kategorie "Diverse" zu
- Achte auf Multi-Word-Keywords (z.B. "finanzielle Unterstützung", "soziales Engagement")

Antwortformat (strikt einhalten):
{{
  "keyword1": "Kategorie_1",
  "keyword2": "Kategorie_1",
  "multi word keyword": "Kategorie_2",
  "mehrdeutiges keyword": "Diverse",
  ...
}}

WICHTIG: 
- Antworte NUR mit dem JSON-Objekt, ohne zusätzlichen Text
- Verwende die EXAKTEN Keywords aus der Liste als Keys
- Jedes Keyword muss genau einmal vorkommen"""
        
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
            keyword_to_category = json.loads(response_text)
            
            # Zähle Kategorien
            categories = set(keyword_to_category.values())
            logger.info(f"{len(categories)} Kategorien generiert")
            logger.info(f"{len(keyword_to_category)} von {len(keywords)} Keywords zugeordnet")
            
            return keyword_to_category
            
        except Exception as e:
            logger.error(f"Fehler bei Kategorie-Generierung: {e}")
            # Fallback: Ordne alle Keywords zu "Allgemein" zu
            return {kw: "Allgemein" for kw in keywords}
    
    def assign_categories(self, result: AnalysisResult, 
                         keyword_to_category: Dict[str, str]) -> List[str]:
        """
        Ordnet Keywords einer Antwort zu Kategorien zu.
        WICHTIG: Jedes Keyword hat genau eine Kategorie (1:1 Mapping).
        Für jede Zeile werden alle Kategorien ihrer Keywords gesammelt.
        
        Args:
            result: AnalysisResult mit Keywords
            keyword_to_category: Mapping von Keyword -> Kategorie
            
        Returns:
            Liste von zugeordneten Kategorien (dedupliziert und sortiert)
            - "Keine": Wenn Fehler oder keine Keywords vorhanden
            - "Sonstiges": Wenn Keywords vorhanden, aber keine Kategorie gefunden
        """
        # Fall 1: Fehler oder keine Keywords -> "Keine"
        if result.error or not result.keywords:
            return ["Keine"]
        
        assigned_categories = set()
        unmatched_keywords = []
        
        # Verarbeite JEDES Keyword einzeln
        for keyword in result.keywords:
            keyword_lower = keyword.lower().strip()
            category_found = False
            
            # Exakte Suche (case-insensitive)
            for kw, category in keyword_to_category.items():
                if kw.lower() == keyword_lower:
                    assigned_categories.add(category)
                    category_found = True
                    break
            
            # Falls nicht gefunden: Teil-Match (für Multi-Word-Keywords)
            if not category_found:
                for kw, category in keyword_to_category.items():
                    kw_lower = kw.lower()
                    # Prüfe ob eines im anderen enthalten ist
                    if (kw_lower in keyword_lower or keyword_lower in kw_lower):
                        assigned_categories.add(category)
                        category_found = True
                        break
            
            # Falls immer noch nicht gefunden: Wort-für-Wort-Vergleich
            if not category_found:
                keyword_words = set(keyword_lower.split())
                for kw, category in keyword_to_category.items():
                    kw_words = set(kw.lower().split())
                    # Wenn mindestens ein Wort übereinstimmt
                    if keyword_words & kw_words:
                        assigned_categories.add(category)
                        category_found = True
                        break
            
            # Tracke nicht zugeordnete Keywords
            if not category_found:
                unmatched_keywords.append(keyword)
        
        # Fall 2: Keywords vorhanden, aber keine Kategorie gefunden -> "Sonstiges"
        if not assigned_categories:
            logger.warning(f"Keine Kategorie gefunden für Keywords: {result.keywords}")
            return ["Sonstiges"]
        
        # Logge nicht zugeordnete Keywords (falls vorhanden)
        if unmatched_keywords:
            logger.debug(f"Nicht zugeordnete Keywords: {unmatched_keywords}")
        
        return sorted(list(assigned_categories))
    
    def categorize_all(self, results: List[AnalysisResult]) -> tuple:
        """
        Führt vollständige Kategorisierung durch.
        
        Args:
            results: Liste von AnalysisResult-Objekten
            
        Returns:
            Tuple (keyword_to_category, category_assignments)
            - keyword_to_category: Dict[str, str] - Mapping von Keyword -> Kategorie
            - category_assignments: List[List[str]] - Kategorien pro Zeile
        """
        # Sammle Keywords
        all_keywords = self.collect_all_keywords(results)
        
        if not all_keywords:
            logger.warning("Keine Keywords gefunden, überspringe Kategorisierung")
            return {}, [["Keine"] for _ in results]
        
        # Generiere Kategorien (1:1 Mapping: Keyword -> Kategorie)
        keyword_to_category = self.generate_categories(all_keywords)
        
        # Ordne Kategorien zu (sammle alle Kategorien der Keywords pro Zeile)
        category_assignments = []
        for result in results:
            categories = self.assign_categories(result, keyword_to_category)
            category_assignments.append(categories)
        
        logger.info("Kategorisierung abgeschlossen")
        return keyword_to_category, category_assignments
