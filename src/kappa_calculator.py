"""Kappa Calculator für Intercoder-Reliabilität"""

import math
from typing import List, Dict, Tuple, Optional
from logging_config import get_logger

logger = get_logger("kappa_calculator")


class KappaCalculator:
    """
    Berechnet Interkoder-Reliabilität mittels Kappa-Statistiken.
    
    Unterstützt:
    - Cohen's Kappa (2 Kodierer)
    - Fleiss' Kappa (>=2 Kodierer)
    - Konfidenzintervalle
    - Sprachliche Interpretation
    """
    
    @staticmethod
    def cohens_kappa(coder1: List[str], coder2: List[str]) -> Tuple[float, float, str]:
        """
        Berechnet Cohen's Kappa mit Konfidenzintervall.
        
        Args:
            coder1: Kodierungen des ersten Kodierers
            coder2: Kodierungen des zweiten Kodierers
            
        Returns:
            Tuple mit (kappa, confidence_interval_width, interpretation)
            
        Raises:
            ValueError: Bei unterschiedlicher Listenlänge oder leeren Listen
        """
        if len(coder1) != len(coder2):
            raise ValueError(f"Listen haben unterschiedliche Längen: {len(coder1)} vs {len(coder2)}")
        
        if len(coder1) == 0:
            raise ValueError("Listen dürfen nicht leer sein")
        
        n = len(coder1)
        
        # Sammle alle eindeutigen Kategorien
        categories = sorted(set(coder1 + coder2))
        k = len(categories)
        
        if k < 2:
            logger.warning("Nur eine Kategorie vorhanden, Kappa = 1.0")
            return 1.0, 0.0, "perfect"
        
        # Erstelle Konfidenzmatrix
        conf_matrix = {}
        for cat1 in categories:
            conf_matrix[cat1] = {}
            for cat2 in categories:
                conf_matrix[cat1][cat2] = 0
        
        for c1, c2 in zip(coder1, coder2):
            conf_matrix[c1][c2] += 1
        
        # Berechne beobachtete Übereinstimmung (Po)
        po = sum(conf_matrix[c][c] for c in categories) / n
        
        # Berechne erwartete Übereinstimmung (Pe)
        pe = 0
        for cat in categories:
            row_sum = sum(conf_matrix[cat][c] for c in categories)
            col_sum = sum(conf_matrix[c][cat] for c in categories)
            pe += (row_sum / n) * (col_sum / n)
        
        # Berechne Kappa
        if pe == 1.0:
            kappa = 1.0
        else:
            kappa = (po - pe) / (1 - pe)
        
        # Berechne Konfidenzintervall (95%)
        # Varianz von Kappa nach Fleiss, Cohen, Landis (1969)
        var_kappa = (po * (1 - po)) / ((1 - pe) ** 2 * n)
        ci_width = 1.96 * math.sqrt(var_kappa) if var_kappa > 0 else 0
        
        # Interpretation
        interpretation = KappaCalculator.interpret_kappa(kappa)
        
        logger.info(f"Cohen's Kappa: {kappa:.3f} ({interpretation}), CI: ±{ci_width:.3f}")
        
        return kappa, ci_width, interpretation
    
    @staticmethod
    def fleiss_kappa(codings: List[List[str]]) -> Tuple[float, float, str]:
        """
        Berechnet Fleiss' Kappa für mehrere Kodierer.
        
        Args:
            codings: Liste von Kodierungen (jede Liste = ein Kodierer)
            
        Returns:
            Tuple mit (kappa, confidence_interval_width, interpretation)
            
        Raises:
            ValueError: Bei zu wenigen Kodierern oder unterschiedlichen Längen
        """
        if len(codings) < 2:
            raise ValueError("Mindestens 2 Kodierer erforderlich")
        
        # Prüfe ob alle Listen gleich lang sind
        lengths = [len(c) for c in codings]
        if len(set(lengths)) > 1:
            raise ValueError(f"Nicht alle Kodierungen haben die gleiche Länge: {lengths}")
        
        n = lengths[0]  # Anzahl Items
        
        if n == 0:
            raise ValueError("Kodierungen dürfen nicht leer sein")
        
        m = len(codings)  # Anzahl Kodierer
        
        # Sammle alle Kategorien
        all_categories = sorted(set(cat for coding in codings for cat in coding))
        k = len(all_categories)
        
        if k < 2:
            return 1.0, 0.0, "perfect"
        
        # Für jedes Item: Zähle Kategorie-Häufigkeiten
        # n_ij = Anzahl Kodierer die Item i in Kategorie j klassifiziert haben
        category_counts = []
        for i in range(n):
            counts = {cat: 0 for cat in all_categories}
            for coding in codings:
                counts[coding[i]] += 1
            category_counts.append(counts)
        
        # Berechne P_i (Übereinstimmungsgrad pro Item)
        p_items = []
        for counts in category_counts:
            p_i = (sum(count * count for count in counts.values()) - m) / (m * (m - 1))
            p_items.append(p_i)
        
        # Mittlere beobachtete Übereinstimmung (P_bar)
        p_bar = sum(p_items) / n
        
        # Berechne Kategorie-Häufigkeiten (p_j)
        category_totals = {cat: 0 for cat in all_categories}
        for counts in category_counts:
            for cat, count in counts.items():
                category_totals[cat] += count
        
        # p_j = Anteil der Kodierungen in Kategorie j
        p_j = {cat: total / (n * m) for cat, total in category_totals.items()}
        
        # Erwartete Übereinstimmung (P_e_bar)
        p_e_bar = sum(p * p for p in p_j.values())
        
        # Fleiss' Kappa
        if p_e_bar == 1.0:
            kappa = 1.0
        else:
            kappa = (p_bar - p_e_bar) / (1 - p_e_bar)
        
        # Näherungsweises Konfidenzintervall (95%)
        var_kappa = 2 / (n * m * (m - 1))
        ci_width = 1.96 * math.sqrt(var_kappa) if var_kappa > 0 else 0
        
        interpretation = KappaCalculator.interpret_kappa(kappa)
        
        logger.info(f"Fleiss' Kappa: {kappa:.3f} ({interpretation}), CI: ±{ci_width:.3f}")
        
        return kappa, ci_width, interpretation
    
    @staticmethod
    def interpret_kappa(kappa: float) -> str:
        """
        Gibt sprachliche Interpretation eines Kappa-Werts zurück.
        
        Basierend auf Landis & Koch (1977):
        - < 0.00: poor
        - 0.00-0.20: slight
        - 0.21-0.40: fair
        - 0.41-0.60: moderate
        - 0.61-0.80: substantial
        - 0.81-1.00: almost perfect
        
        Args:
            kappa: Kappa-Wert
            
        Returns:
            Sprachliche Interpretation
        """
        if kappa < 0.0:
            return "poor"
        elif kappa <= 0.20:
            return "slight"
        elif kappa <= 0.40:
            return "fair"
        elif kappa <= 0.60:
            return "moderate"
        elif kappa <= 0.80:
            return "substantial"
        else:
            return "almost perfect"
    
    @staticmethod
    def interpret_kappa_de(kappa: float) -> str:
        """
        Gibt deutsche sprachliche Interpretation eines Kappa-Werts zurück.
        
        Args:
            kappa: Kappa-Wert
            
        Returns:
            Deutsche Interpretation
        """
        if kappa < 0.0:
            return "schlecht"
        elif kappa <= 0.20:
            return "gering"
        elif kappa <= 0.40:
            return "mäßig"
        elif kappa <= 0.60:
            return "akzeptabel"
        elif kappa <= 0.80:
            return "gut"
        else:
            return "sehr gut"
    
    @staticmethod
    def calculate_per_attribute_kappa(codings_per_attribute: Dict[str, Tuple[List[str], List[str]]]) -> Dict[str, dict]:
        """
        Berechnet Kappa pro Prüfmerkmal.
        
        Args:
            codings_per_attribute: Dict mit Attribut-Name -> (coder1_kodierungen, coder2_kodierungen)
            
        Returns:
            Dict mit Attribut-Name -> {kappa, ci_width, interpretation, n}
        """
        results = {}
        
        for attr_name, (coder1, coder2) in codings_per_attribute.items():
            try:
                kappa, ci_width, interpretation = KappaCalculator.cohens_kappa(coder1, coder2)
                results[attr_name] = {
                    "kappa": kappa,
                    "ci_width": ci_width,
                    "interpretation": interpretation,
                    "n": len(coder1)
                }
            except ValueError as e:
                logger.warning(f"Fehler bei Kappa-Berechnung für '{attr_name}': {e}")
                results[attr_name] = {
                    "kappa": 0.0,
                    "ci_width": 0.0,
                    "interpretation": "error",
                    "n": 0,
                    "error": str(e)
                }
        
        return results
    
    @staticmethod
    def calculate_agreement_percentage(coder1: List[str], coder2: List[str]) -> float:
        """
        Berechnet prozentuale Übereinstimmung (einfachere Metrik).
        
        Args:
            coder1: Kodierungen des ersten Kodierers
            coder2: Kodierungen des zweiten Kodierers
            
        Returns:
            Übereinstimmungsprozent (0.0-1.0)
        """
        if len(coder1) != len(coder2):
            raise ValueError("Listen haben unterschiedliche Längen")
        
        if len(coder1) == 0:
            return 0.0
        
        agreements = sum(1 for c1, c2 in zip(coder1, coder2) if c1 == c2)
        return agreements / len(coder1)
    
    @staticmethod
    def get_kappa_summary(kappa_results: Dict[str, dict]) -> dict:
        """
        Erstellt Zusammenfassung der Kappa-Ergebnisse.
        
        Args:
            kappa_results: Dict von calculate_per_attribute_kappa()
            
        Returns:
            Dict mit Gesamt-Kappa und Statistiken
        """
        if not kappa_results:
            return {
                "overall_kappa": 0.0,
                "mean_kappa": 0.0,
                "min_kappa": 0.0,
                "max_kappa": 0.0,
                "count": 0,
                "substantial_or_better": 0
            }
        
        valid_results = [r for r in kappa_results.values() if "error" not in r]
        
        if not valid_results:
            return {
                "overall_kappa": 0.0,
                "mean_kappa": 0.0,
                "min_kappa": 0.0,
                "max_kappa": 0.0,
                "count": 0,
                "substantial_or_better": 0
            }
        
        kappas = [r["kappa"] for r in valid_results]
        
        return {
            "overall_kappa": sum(kappas) / len(kappas),
            "mean_kappa": sum(kappas) / len(kappas),
            "min_kappa": min(kappas),
            "max_kappa": max(kappas),
            "count": len(kappas),
            "substantial_or_better": sum(1 for k in kappas if k >= 0.61)
        }
