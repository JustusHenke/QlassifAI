"""Unit Tests für MultiCoder"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from multi_coder import MultiCoder, CoderResult, IntercoderResult
from models import ScientificConfig, CheckAttribute, AnalysisResult


class MockAnalyzer:
    """Mock LLMAnalyzer für Tests"""
    
    def __init__(self, sentiment="positiv", check_value=True):
        self.sentiment = sentiment
        self.check_value = check_value
    
    def analyze_text(self, text, check_attributes, **kwargs):
        return AnalysisResult(
            paraphrase="Test Paraphrase",
            sentiment=self.sentiment,
            sentiment_reason="Test Grund",
            keywords=["test", "wort"],
            custom_checks={attr.question: self.check_value for attr in check_attributes},
            custom_checks_reasons={attr.question: "Test" for attr in check_attributes}
        )


class TestMultiCoder:
    """Tests für MultiCoder"""
    
    def test_initialization(self):
        """MultiCoder wird korrekt initialisiert"""
        sc = ScientificConfig(multi_coder=True, coder_models=["m1", "m2"])
        mc = MultiCoder(sc)
        
        assert mc.config.multi_coder == True
        assert len(mc._analyzers) == 0
    
    def test_add_analyzer(self):
        """Analyzer wird hinzugefügt"""
        sc = ScientificConfig(multi_coder=True, coder_models=["m1", "m2"])
        mc = MultiCoder(sc)
        
        mc.add_analyzer("m1", MockAnalyzer())
        
        assert "m1" in mc._analyzers
    
    def test_encode_text(self):
        """Kodierung mit 2 Modellen"""
        sc = ScientificConfig(multi_coder=True, coder_models=["m1", "m2"])
        mc = MultiCoder(sc)
        mc.add_analyzer("m1", MockAnalyzer("positiv", True))
        mc.add_analyzer("m2", MockAnalyzer("positiv", True))
        
        attrs = [CheckAttribute(question="Q1?", answer_type="boolean")]
        result = mc.encode_text("Testtext", attrs)
        
        assert isinstance(result, IntercoderResult)
        assert len(result.coder_results) == 2
        assert result.agreements.get("Q1?") == True
    
    def test_encode_text_disagreement(self):
        """Kodierung mit verschiedenen Ergebnissen"""
        sc = ScientificConfig(multi_coder=True, coder_models=["m1", "m2"])
        mc = MultiCoder(sc)
        mc.add_analyzer("m1", MockAnalyzer("positiv", True))
        mc.add_analyzer("m2", MockAnalyzer("positiv", False))
        
        attrs = [CheckAttribute(question="Q1?", answer_type="boolean")]
        result = mc.encode_text("Testtext", attrs)
        
        assert result.agreements.get("Q1?") == False
    
    def test_primary_coder_model_1(self):
        """Primärer Kodierer ist model_1"""
        sc = ScientificConfig(multi_coder=True, coder_models=["m1", "m2"], primary_coder="model_1")
        mc = MultiCoder(sc)
        mc.add_analyzer("m1", MockAnalyzer())
        mc.add_analyzer("m2", MockAnalyzer())
        
        attrs = [CheckAttribute(question="Q1?", answer_type="boolean")]
        result = mc.encode_text("Test", attrs)
        
        assert result.primary_coder_idx == 0
    
    def test_primary_coder_highest_confidence(self):
        """Primärer Kodierer ist höchste Konfidenz"""
        sc = ScientificConfig(multi_coder=True, coder_models=["m1", "m2"], primary_coder="highest_confidence")
        mc = MultiCoder(sc)
        mc.add_analyzer("m1", MockAnalyzer())
        mc.add_analyzer("m2", MockAnalyzer())
        
        attrs = [CheckAttribute(question="Q1?", answer_type="boolean")]
        result = mc.encode_text("Test", attrs)
        
        assert result.primary_coder_idx in [0, 1]
    
    def test_get_coder_by_model(self):
        """Kodierer nach Modellname abrufen"""
        sc = ScientificConfig(multi_coder=True, coder_models=["m1", "m2"])
        mc = MultiCoder(sc)
        mc.add_analyzer("m1", MockAnalyzer())
        mc.add_analyzer("m2", MockAnalyzer())
        
        attrs = [CheckAttribute(question="Q1?", answer_type="boolean")]
        result = mc.encode_text("Test", attrs)
        
        assert result.get_coder_by_model("m1") is not None
        assert result.get_coder_by_model("m2") is not None
        assert result.get_coder_by_model("m3") is None
    
    def test_encode_batch(self):
        """Batch-Kodierung"""
        sc = ScientificConfig(multi_coder=True, coder_models=["m1", "m2"])
        mc = MultiCoder(sc)
        mc.add_analyzer("m1", MockAnalyzer())
        mc.add_analyzer("m2", MockAnalyzer())
        
        attrs = [CheckAttribute(question="Q1?", answer_type="boolean")]
        results = mc.encode_batch(["Text 1", "Text 2", "Text 3"], attrs)
        
        assert len(results) == 3
        assert all(isinstance(r, IntercoderResult) for r in results)
    
    def test_aggregate_batch_results(self):
        """Aggregation von Batch-Ergebnissen"""
        # Erstelle Mock-Ergebnisse
        sc = ScientificConfig(multi_coder=True, coder_models=["m1", "m2"])
        mc = MultiCoder(sc)
        mc.add_analyzer("m1", MockAnalyzer())
        mc.add_analyzer("m2", MockAnalyzer())
        
        attrs = [CheckAttribute(question="Q1?", answer_type="boolean")]
        results = mc.encode_batch(["Text 1", "Text 2"], attrs)
        
        aggregated = MultiCoder.aggregate_batch_results(results)
        
        assert "__overall__" in aggregated
        assert aggregated["__overall__"]["mean_kappa"] >= 0


def run_tests():
    """Führt alle Tests aus"""
    test = TestMultiCoder()
    tests = [
        test.test_initialization,
        test.test_add_analyzer,
        test.test_encode_text,
        test.test_encode_text_disagreement,
        test.test_primary_coder_model_1,
        test.test_primary_coder_highest_confidence,
        test.test_get_coder_by_model,
        test.test_encode_batch,
        test.test_aggregate_batch_results,
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
    print("=== test_multi_coder.py ===")
    passed, failed = run_tests()
    print(f"\n{passed} bestanden, {failed} fehlgeschlagen")
