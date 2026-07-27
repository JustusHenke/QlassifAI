"""Unit Tests für KappaCalculator"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from kappa_calculator import KappaCalculator


class TestKappaCalculator:
    """Tests für KappaCalculator"""
    
    def test_cohens_kappa_perfect(self):
        """Perfekte Übereinstimmung: Kappa = 1.0"""
        coder1 = ["A", "B", "C", "A", "B"]
        coder2 = ["A", "B", "C", "A", "B"]
        
        kappa, ci, interp = KappaCalculator.cohens_kappa(coder1, coder2)
        
        assert kappa == 1.0
        assert interp == "almost perfect"
    
    def test_cohens_kappa_partial(self):
        """Teilweise Übereinstimmung"""
        coder1 = ["A", "B", "A", "B", "A"]
        coder2 = ["A", "B", "B", "B", "A"]
        
        kappa, ci, interp = KappaCalculator.cohens_kappa(coder1, coder2)
        
        assert 0.0 <= kappa <= 1.0
        assert interp in ["poor", "slight", "fair", "moderate", "substantial", "almost perfect"]
    
    def test_cohens_kappa_different_lengths(self):
        """Unterschiedliche Längen werfen Fehler"""
        try:
            KappaCalculator.cohens_kappa(["A", "B"], ["A"])
            assert False, "Hätte ValueError werfen sollen"
        except ValueError:
            pass
    
    def test_cohens_kappa_empty(self):
        """Leere Listen werfen Fehler"""
        try:
            KappaCalculator.cohens_kappa([], [])
            assert False, "Hätte ValueError werfen sollen"
        except ValueError:
            pass
    
    def test_fleiss_kappa(self):
        """Fleiss' Kappa für mehr als 2 Kodierer"""
        codings = [
            ["A", "B", "A", "A"],
            ["A", "B", "A", "B"],
            ["A", "B", "A", "A"]
        ]
        
        kappa, ci, interp = KappaCalculator.fleiss_kappa(codings)
        
        assert 0.0 <= kappa <= 1.0
        assert interp in ["poor", "slight", "fair", "moderate", "substantial", "almost perfect"]
    
    def test_fleiss_kappa_too_few_coders(self):
        """Weniger als 2 Kodierer werfen Fehler"""
        try:
            KappaCalculator.fleiss_kappa([["A", "B"]])
            assert False, "Hätte ValueError werfen sollen"
        except ValueError:
            pass
    
    def test_interpret_kappa(self):
        """Sprachliche Interpretation"""
        assert KappaCalculator.interpret_kappa(0.9) == "almost perfect"
        assert KappaCalculator.interpret_kappa(0.7) == "substantial"
        assert KappaCalculator.interpret_kappa(0.5) == "moderate"
        assert KappaCalculator.interpret_kappa(0.3) == "fair"
        assert KappaCalculator.interpret_kappa(0.1) == "slight"
        assert KappaCalculator.interpret_kappa(-0.1) == "poor"
    
    def test_interpret_kappa_de(self):
        """Deutsche Interpretation"""
        assert KappaCalculator.interpret_kappa_de(0.9) == "sehr gut"
        assert KappaCalculator.interpret_kappa_de(0.7) == "gut"
        assert KappaCalculator.interpret_kappa_de(0.5) == "akzeptabel"
        assert KappaCalculator.interpret_kappa_de(0.3) == "mäßig"
        assert KappaCalculator.interpret_kappa_de(0.1) == "gering"
    
    def test_agreement_percentage(self):
        """Prozentuale Übereinstimmung"""
        coder1 = ["A", "B", "A", "B"]
        coder2 = ["A", "B", "B", "B"]
        
        agreement = KappaCalculator.calculate_agreement_percentage(coder1, coder2)
        
        assert agreement == 0.75  # 3 von 4 übereinstimmend
    
    def test_per_attribute_kappa(self):
        """Kappa pro Prüfmerkmal"""
        codings = {
            "Q1": (["A", "B", "A"], ["A", "B", "B"]),
            "Q2": (["X", "Y"], ["X", "Y"])
        }
        
        results = KappaCalculator.calculate_per_attribute_kappa(codings)
        
        assert "Q1" in results
        assert "Q2" in results
        assert results["Q2"]["kappa"] == 1.0  # Perfekte Übereinstimmung
    
    def test_kappa_summary(self):
        """Zusammenfassung der Kappa-Ergebnisse"""
        kappa_results = {
            "Q1": {"kappa": 0.8, "interpretation": "substantial"},
            "Q2": {"kappa": 0.6, "interpretation": "moderate"}
        }
        
        summary = KappaCalculator.get_kappa_summary(kappa_results)
        
        assert summary["count"] == 2
        assert summary["mean_kappa"] == 0.7
        assert summary["substantial_or_better"] == 1


def run_tests():
    """Führt alle Tests aus"""
    test = TestKappaCalculator()
    tests = [
        test.test_cohens_kappa_perfect,
        test.test_cohens_kappa_partial,
        test.test_cohens_kappa_different_lengths,
        test.test_cohens_kappa_empty,
        test.test_fleiss_kappa,
        test.test_fleiss_kappa_too_few_coders,
        test.test_interpret_kappa,
        test.test_interpret_kappa_de,
        test.test_agreement_percentage,
        test.test_per_attribute_kappa,
        test.test_kappa_summary,
    ]
    
    passed = 0
    failed = 0
    
    for t in tests:
        try:
            t()
            passed += 1
            print(f"  ✓ {t.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"  ✗ {t.__name__}: {e}")
        except Exception as e:
            failed += 1
            print(f"  ✗ {t.__name__}: {type(e).__name__}: {e}")
    
    return passed, failed


if __name__ == "__main__":
    print("=== test_kappa_calculator.py ===")
    passed, failed = run_tests()
    print(f"\n{passed} bestanden, {failed} fehlgeschlagen")
