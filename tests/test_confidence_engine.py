"""Unit Tests für ConfidenceEngine"""

import sys
from pathlib import Path

# Füge src zum Pfad hinzu
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from confidence_engine import ConfidenceEngine
from models import CheckAttribute, AnalysisResult


class TestConfidenceEngine:
    """Tests für ConfidenceEngine"""
    
    def test_normalize_score_float(self):
        """Score als Float (0.0-1.0) bleibt unverändert"""
        assert ConfidenceEngine._normalize_score(0.85) == 0.85
        assert ConfidenceEngine._normalize_score(0.0) == 0.0
        assert ConfidenceEngine._normalize_score(1.0) == 1.0
    
    def test_normalize_score_int(self):
        """Score als Int (0-100) wird normalisiert"""
        assert ConfidenceEngine._normalize_score(85) == 0.85
        assert ConfidenceEngine._normalize_score(0) == 0.0
        assert ConfidenceEngine._normalize_score(100) == 1.0
    
    def test_normalize_score_none(self):
        """Score None wird zu 0.0"""
        assert ConfidenceEngine._normalize_score(None) == 0.0
    
    def test_normalize_score_invalid(self):
        """Ungültiger Score wird zu 0.0"""
        assert ConfidenceEngine._normalize_score("invalid") == 0.0
    
    def test_normalize_score_capped(self):
        """Score wird auf 0.0-1.0 begrenzt"""
        assert ConfidenceEngine._normalize_score(150) == 1.0
        assert ConfidenceEngine._normalize_score(-10) == 0.0
    
    def test_extract_confidence(self):
        """Konfidenz wird korrekt aus LLM-Antwort extrahiert"""
        response = {
            "confidence": {"Frage 1": 85, "Frage 2": 45},
            "confidence_reasons": {"Frage 1": "Sicher", "Frage 2": "Unsicher"},
            "alternatives": {"Frage 2": ["A", "B"]}
        }
        attrs = [{"question": "Frage 1", "answer_type": "boolean"}]
        
        results = ConfidenceEngine.extract_confidence_from_response(response, attrs, threshold=0.7)
        
        assert results["Frage 1"]["score"] == 0.85
        assert results["Frage 1"]["reasoning"] == "Sicher"
        assert results["Frage 1"]["is_low"] == False
    
    def test_extract_confidence_low(self):
        """Niedrige Konfidenz wird markiert"""
        response = {
            "confidence": {"Frage 1": 45},
            "confidence_reasons": {},
            "alternatives": {}
        }
        attrs = [{"question": "Frage 1", "answer_type": "boolean"}]
        
        results = ConfidenceEngine.extract_confidence_from_response(response, attrs, threshold=0.7)
        
        assert results["Frage 1"]["score"] == 0.45
        assert results["Frage 1"]["is_low"] == True
    
    def test_extract_confidence_missing(self):
        """Fehlende Konfidenz wird behandelt"""
        response = {"confidence": {}}
        attrs = [{"question": "Frage 1", "answer_type": "boolean"}]
        
        results = ConfidenceEngine.extract_confidence_from_response(response, attrs)
        
        assert results["Frage 1"]["score"] is None
    
    def test_build_prompt_section(self):
        """Prompt-Sektion wird korrekt generiert"""
        attrs = [{"question": "Q1?", "answer_type": "boolean"}]
        
        prompt = ConfidenceEngine.build_confidence_prompt_section(attrs)
        
        assert "confidence" in prompt
        assert "confidence_reasons" in prompt
        assert "alternatives" in prompt
        assert "Q1?" in prompt
    
    def test_mark_low_confidence(self):
        """Niedrige Konfidenz wird korrekt markiert"""
        results = {
            "Q1": {"score": 0.8, "reasoning": "", "alternatives": []},
            "Q2": {"score": 0.4, "reasoning": "", "alternatives": []}
        }
        
        low = ConfidenceEngine.mark_low_confidence_items(results, threshold=0.7)
        
        assert "Q1" not in low
        assert "Q2" in low
    
    def test_summary_statistics(self):
        """Zusammenfassungsstatistiken werden korrekt berechnet"""
        results = {
            "Q1": {"score": 0.8, "reasoning": "", "alternatives": []},
            "Q2": {"score": 0.6, "reasoning": "", "alternatives": []},
            "Q3": {"score": 0.9, "reasoning": "", "alternatives": []}
        }
        
        stats = ConfidenceEngine.get_summary_statistics(results)
        
        assert stats["count"] == 3
        assert stats["min"] == 0.6
        assert stats["max"] == 0.9
        assert abs(stats["mean"] - 0.7667) < 0.01
    
    def test_merge_multiple_coders_highest_confidence(self):
        """Merge mit highest_confidence Strategie"""
        coder1 = {"Q1": {"score": 0.8, "reasoning": "Gut", "alternatives": []}}
        coder2 = {"Q1": {"score": 0.9, "reasoning": "Sehr gut", "alternatives": []}}
        
        merged = ConfidenceEngine.merge_multiple_coders([coder1, coder2], strategy="highest_confidence")
        
        assert merged["Q1"]["score"] == 0.9
        assert merged["Q1"]["agreement"] == True  # diff < 0.2
    
    def test_merge_multiple_coders_low_agreement(self):
        """Merge mit niedriger Übereinstimmung"""
        coder1 = {"Q1": {"score": 0.5, "reasoning": "", "alternatives": []}}
        coder2 = {"Q1": {"score": 0.9, "reasoning": "", "alternatives": []}}
        
        merged = ConfidenceEngine.merge_multiple_coders([coder1, coder2])
        
        assert merged["Q1"]["agreement"] == False  # diff > 0.2
        assert merged["Q1"]["coder_count"] == 2


def run_tests():
    """Führt alle Tests aus"""
    test = TestConfidenceEngine()
    tests = [
        test.test_normalize_score_float,
        test.test_normalize_score_int,
        test.test_normalize_score_none,
        test.test_normalize_score_invalid,
        test.test_normalize_score_capped,
        test.test_extract_confidence,
        test.test_extract_confidence_low,
        test.test_extract_confidence_missing,
        test.test_build_prompt_section,
        test.test_mark_low_confidence,
        test.test_summary_statistics,
        test.test_merge_multiple_coders_highest_confidence,
        test.test_merge_multiple_coders_low_agreement,
    ]
    
    passed = 0
    failed = 0
    
    for t in tests:
        try:
            t()
            passed += 1
            print(f"  OK {t.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"  FAIL {t.__name__}: {e}")
        except Exception as e:
            failed += 1
            print(f"  FAIL {t.__name__}: {type(e).__name__}: {e}")
    
    return passed, failed


if __name__ == "__main__":
    print("=== test_confidence_engine.py ===")
    passed, failed = run_tests()
    print(f"\n{passed} bestanden, {failed} fehlgeschlagen")
