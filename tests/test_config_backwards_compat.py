"""Unit Tests für Config Backwards Compatibility"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config_manager import ConfigManager
from models import Config, CheckAttribute, ScientificConfig
import tempfile
import json


class TestConfigBackwardsCompat:
    """Tests für Config Abwärtskompatibilität"""
    
    def test_load_config_without_scientific(self):
        """Config ohne scientific Feld wird korrekt geladen"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_data = {
                "version": "1.0",
                "model": "gpt-4o-mini",
                "provider": "openai",
                "check_attributes": [
                    {"question": "Test?", "answer_type": "boolean"}
                ]
            }
            
            config_path = Path(tmpdir) / "test_config.json"
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f)
            
            cm = ConfigManager()
            config = cm.load_config(config_path)
            
            assert config.scientific is None
            assert config.model == "gpt-4o-mini"
            assert len(config.check_attributes) == 1
    
    def test_load_config_with_scientific(self):
        """Config mit scientific Feld wird korrekt geladen"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_data = {
                "version": "1.0",
                "model": "gpt-4o",
                "provider": "openai",
                "scientific": {
                    "multi_coder": True,
                    "coder_models": ["gpt-4o-mini", "gpt-4o"],
                    "confidence_threshold": 80,
                    "seed": 42
                },
                "check_attributes": [
                    {"question": "Test?", "answer_type": "boolean"}
                ]
            }
            
            config_path = Path(tmpdir) / "test_config.json"
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f)
            
            cm = ConfigManager()
            config = cm.load_config(config_path)
            
            assert config.scientific is not None
            assert config.scientific.multi_coder == True
            assert config.scientific.confidence_threshold == 80
            assert config.scientific.seed == 42
            assert len(config.scientific.coder_models) == 2
    
    def test_save_and_reload(self):
        """Config wird korrekt gespeichert und wieder geladen"""
        with tempfile.TemporaryDirectory() as tmpdir:
            attr = CheckAttribute(question="Test?", answer_type="boolean")
            sc = ScientificConfig(
                multi_coder=True,
                coder_models=["m1", "m2"],
                confidence_threshold=75,
                seed=123
            )
            config = Config(
                check_attributes=[attr],
                model="gpt-4o",
                scientific=sc
            )
            
            cm = ConfigManager()
            save_path = Path(tmpdir) / "test_config.json"
            cm.save_config(config, save_path)
            
            # Reload
            loaded = cm.load_config(save_path)
            
            assert loaded.scientific.multi_coder == True
            assert loaded.scientific.confidence_threshold == 75
            assert loaded.scientific.seed == 123
            assert loaded.model == "gpt-4o"
    
    def test_config_defaults(self):
        """Config-Defaults werden korrekt gesetzt"""
        attr = CheckAttribute(question="Q?", answer_type="boolean")
        config = Config(check_attributes=[attr])
        
        assert config.version == "1.0"
        assert config.model == "gpt-4o-mini"
        assert config.provider == "openai"
        assert config.include_reasoning == True
        assert config.scientific is None
    
    def test_scientific_config_defaults(self):
        """ScientificConfig-Defaults werden korrekt gesetzt"""
        sc = ScientificConfig()
        
        assert sc.multi_coder == False
        assert sc.coder_models == ["gpt-4o-mini"]
        assert sc.primary_coder == "model_1"
        assert sc.confidence_threshold == 70
        assert sc.seed is None
        assert sc.is_intercoder_active == False
    
    def test_scientific_config_intercoder_active(self):
        """is_intercoder_active wird korrekt berechnet"""
        sc1 = ScientificConfig(multi_coder=True, coder_models=["m1", "m2"])
        sc2 = ScientificConfig(multi_coder=False, coder_models=["m1", "m2"])
        sc3 = ScientificConfig(multi_coder=False, coder_models=["m1"])
        
        assert sc1.is_intercoder_active == True
        assert sc2.is_intercoder_active == False
        assert sc3.is_intercoder_active == False
    
    def test_invalid_scientific_config(self):
        """Ungültige ScientificConfig wirft Fehler"""
        try:
            ScientificConfig(primary_coder="invalid")
            assert False, "Hätte ValueError werfen sollen"
        except ValueError:
            pass
        
        try:
            ScientificConfig(confidence_threshold=150)
            assert False, "Hätte ValueError werfen sollen"
        except ValueError:
            pass
        
        try:
            ScientificConfig(multi_coder=True, coder_models=["m1"])
            assert False, "Hätte ValueError werfen sollen"
        except ValueError:
            pass


def run_tests():
    """Führt alle Tests aus"""
    test = TestConfigBackwardsCompat()
    tests = [
        test.test_load_config_without_scientific,
        test.test_load_config_with_scientific,
        test.test_save_and_reload,
        test.test_config_defaults,
        test.test_scientific_config_defaults,
        test.test_scientific_config_intercoder_active,
        test.test_invalid_scientific_config,
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
    print("=== test_config_backwards_compat.py ===")
    passed, failed = run_tests()
    print(f"\n{passed} bestanden, {failed} fehlgeschlagen")
