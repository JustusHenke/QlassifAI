"""Unit Tests für ReproducibilityManager"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from reproducibility_manager import ReproducibilityManager, AuditEntry, MethodologyMetadata
import tempfile
import json


class TestReproducibilityManager:
    """Tests für ReproducibilityManager"""
    
    def test_initialization(self):
        """ReproducibilityManager wird korrekt initialisiert"""
        with tempfile.TemporaryDirectory() as tmpdir:
            rm = ReproducibilityManager(Path(tmpdir))
            
            assert rm.output_dir.exists()
            assert (rm.output_dir / "audit_trail").exists()
    
    def test_hash_content(self):
        """SHA256-Hash wird korrekt berechnet"""
        hash1 = ReproducibilityManager.hash_content("test")
        hash2 = ReproducibilityManager.hash_content("test")
        hash3 = ReproducibilityManager.hash_content("anderer Text")
        
        assert hash1 == hash2
        assert hash1 != hash3
        assert len(hash1) == 64  # SHA256 Hex Länge
    
    def test_record_analysis(self):
        """Analyse wird im Audit Trail aufgezeichnet"""
        with tempfile.TemporaryDirectory() as tmpdir:
            rm = ReproducibilityManager(Path(tmpdir))
            
            entry = rm.record_analysis(
                model="gpt-4o-mini",
                provider="openai",
                prompt="Test prompt",
                response="Test response",
                seed=42,
                input_text="Test input"
            )
            
            assert entry.model == "gpt-4o-mini"
            assert entry.seed == 42
            assert len(rm.audit_entries) == 1
    
    def test_save_audit_trail(self):
        """Audit Trail wird gespeichert"""
        with tempfile.TemporaryDirectory() as tmpdir:
            rm = ReproducibilityManager(Path(tmpdir))
            rm.record_analysis("gpt-4o-mini", "openai", "prompt", "response")
            
            filepath = rm.save_audit_trail()
            
            assert filepath.exists()
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            assert data["metadata"]["total_entries"] == 1
    
    def test_generate_methodology(self):
        """Methodology.md wird generiert"""
        with tempfile.TemporaryDirectory() as tmpdir:
            rm = ReproducibilityManager(Path(tmpdir))
            
            metadata = MethodologyMetadata(
                model="gpt-4o-mini",
                provider="openai",
                temperature=0.3,
                research_question="Testfrage?",
                check_attributes=[
                    {"question": "Q1?", "answer_type": "boolean"},
                    {"question": "Q2?", "answer_type": "categorical", "categories": ["A", "B"]}
                ],
                total_items=100,
                total_successful=95,
                total_failed=5,
                total_tokens=50000
            )
            
            filepath = rm.generate_methodology(metadata)
            
            assert filepath.exists()
            content = filepath.read_text(encoding='utf-8')
            assert "gpt-4o-mini" in content
            assert "Testfrage?" in content
            assert "Q1?" in content
    
    def test_export_codebook(self):
        """Codebook.json wird exportiert"""
        with tempfile.TemporaryDirectory() as tmpdir:
            rm = ReproducibilityManager(Path(tmpdir))
            
            check_attrs = [
                {"question": "Engagement?", "answer_type": "boolean"},
                {"question": "Kategorie?", "answer_type": "categorical", "categories": ["A", "B"]}
            ]
            
            filepath = rm.export_codebook(check_attrs)
            
            assert filepath.exists()
            with open(filepath, 'r', encoding='utf-8') as f:
                codebook = json.load(f)
            assert len(codebook["check_attributes"]) == 2
    
    def test_export_frequency_tables(self):
        """Frequency Tables CSV wird exportiert"""
        with tempfile.TemporaryDirectory() as tmpdir:
            rm = ReproducibilityManager(Path(tmpdir))
            
            results = [
                {"custom_checks": {"Q1?": True, "Q2?": "A"}},
                {"custom_checks": {"Q1?": False, "Q2?": "B"}},
                {"custom_checks": {"Q1?": True, "Q2?": "A"}}
            ]
            check_attrs = [
                {"question": "Q1?", "answer_type": "boolean"},
                {"question": "Q2?", "answer_type": "categorical", "categories": ["A", "B"]}
            ]
            
            filepath = rm.export_frequency_tables(results, check_attrs)
            
            assert filepath.exists()
            content = filepath.read_text(encoding='utf-8')
            assert "Q1?" in content
            assert "Q2?" in content
    
    def test_save_all(self):
        """Alle Dateien werden gespeichert"""
        with tempfile.TemporaryDirectory() as tmpdir:
            rm = ReproducibilityManager(Path(tmpdir))
            rm.record_analysis("gpt-4o-mini", "openai", "prompt", "response")
            
            metadata = MethodologyMetadata(
                model="gpt-4o-mini",
                provider="openai"
            )
            
            output = rm.save_all(
                metadata,
                [{"question": "Q1?", "answer_type": "boolean"}],
                [{"custom_checks": {"Q1?": True}}]
            )
            
            assert "methodology" in output
            assert "codebook" in output
            assert "frequency_tables" in output
            assert "audit_trail" in output
            assert all(p.exists() for p in output.values())


def run_tests():
    """Führt alle Tests aus"""
    test = TestReproducibilityManager()
    tests = [
        test.test_initialization,
        test.test_hash_content,
        test.test_record_analysis,
        test.test_save_audit_trail,
        test.test_generate_methodology,
        test.test_export_codebook,
        test.test_export_frequency_tables,
        test.test_save_all,
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
    print("=== test_reproducibility.py ===")
    passed, failed = run_tests()
    print(f"\n{passed} bestanden, {failed} fehlgeschlagen")
