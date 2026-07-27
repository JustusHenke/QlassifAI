"""Config Manager für Prüfmerkmale-Verwaltung"""

import json
from pathlib import Path
from typing import Optional
from models import CheckAttribute, Config, ScientificConfig
from logging_config import get_logger
from exceptions import InvalidConfigError, ConfigError

logger = get_logger("config_manager")


class ConfigManager:
    """Verwaltet benutzerdefinierte Prüfmerkmale (laden, erstellen, speichern)"""
    
    def __init__(self):
        """Initialisiert ConfigManager"""
        pass
    
    def find_config_file(self, directory: Path = Path(".")) -> Optional[Path]:
        """Sucht nach QlassifAI_config.json im Verzeichnis."""
        config_path = directory / "QlassifAI_config.json"
        
        if config_path.exists() and config_path.is_file():
            logger.info(f"Config-Datei gefunden: {config_path}")
            return config_path
        
        logger.info(f"Keine QlassifAI_config.json gefunden in {directory}")
        return None
    
    def load_config(self, config_path: Path) -> Config:
        """Lädt und validiert Config-Datei."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.info(f"Config-Datei geladen: {config_path}")
            
            if "check_attributes" not in data:
                raise InvalidConfigError("Fehlendes Feld: 'check_attributes'")
            
            check_attributes = []
            for attr_data in data["check_attributes"]:
                try:
                    attr = CheckAttribute(
                        question=attr_data["question"],
                        answer_type=attr_data["answer_type"],
                        categories=attr_data.get("categories"),
                        definition=attr_data.get("definition")
                    )
                    check_attributes.append(attr)
                except (KeyError, ValueError) as e:
                    raise InvalidConfigError(f"Ungültiges Prüfmerkmal: {e}")
            
            version = data.get("version", "1.0")
            model = data.get("model", "gpt-4o-mini")
            provider = data.get("provider", "openai")
            text_column_name = data.get("text_column_name")
            research_question = data.get("research_question")
            include_reasoning = data.get("include_reasoning", True)
            
            scientific = None
            scientific_data = data.get("scientific")
            if scientific_data:
                try:
                    scientific = ScientificConfig(
                        multi_coder=scientific_data.get("multi_coder", False),
                        coder_models=scientific_data.get("coder_models", ["gpt-4o-mini"]),
                        primary_coder=scientific_data.get("primary_coder", "model_1"),
                        confidence_threshold=scientific_data.get("confidence_threshold", 70),
                        seed=scientific_data.get("seed"),
                        output_dir=scientific_data.get("output_dir")
                    )
                    logger.info(f"Wissenschaftliche Config geladen: multi_coder={scientific.multi_coder}, "
                              f"confidence_threshold={scientific.confidence_threshold}")
                except ValueError as e:
                    raise InvalidConfigError(f"Ungültige wissenschaftliche Konfiguration: {e}")
            
            config = Config(
                check_attributes=check_attributes,
                version=version,
                model=model,
                provider=provider,
                text_column_name=text_column_name,
                research_question=research_question,
                include_reasoning=include_reasoning,
                scientific=scientific
            )
            
            logger.info(f"{len(check_attributes)} Prüfmerkmal(e) geladen, Provider: {provider}, Modell: {model}")
            return config
            
        except json.JSONDecodeError as e:
            error_msg = f"Ungültige JSON-Datei: {e}"
            logger.error(error_msg)
            raise InvalidConfigError(error_msg)
        except FileNotFoundError:
            error_msg = f"Config-Datei nicht gefunden: {config_path}"
            logger.error(error_msg)
            raise InvalidConfigError(error_msg)
        except Exception as e:
            error_msg = f"Fehler beim Laden der Config: {e}"
            logger.error(error_msg)
            raise InvalidConfigError(error_msg)
    
    def save_config(self, config: Config, path: Path = Path("QlassifAI_config.json")) -> None:
        """Speichert Config als JSON."""
        data = {
            "version": config.version,
            "model": config.model,
            "provider": config.provider,
            "check_attributes": []
        }
        
        if config.text_column_name:
            data["text_column_name"] = config.text_column_name
        if config.research_question:
            data["research_question"] = config.research_question
        if not config.include_reasoning:
            data["include_reasoning"] = False
        
        if config.scientific:
            scientific_data = {}
            if config.scientific.multi_coder:
                scientific_data["multi_coder"] = True
            if config.scientific.coder_models != ["gpt-4o-mini"]:
                scientific_data["coder_models"] = config.scientific.coder_models
            if config.scientific.primary_coder != "model_1":
                scientific_data["primary_coder"] = config.scientific.primary_coder
            if config.scientific.confidence_threshold != 70:
                scientific_data["confidence_threshold"] = config.scientific.confidence_threshold
            if config.scientific.seed is not None:
                scientific_data["seed"] = config.scientific.seed
            if config.scientific.output_dir:
                scientific_data["output_dir"] = config.scientific.output_dir
            
            if scientific_data:
                data["scientific"] = scientific_data
        
        for attr in config.check_attributes:
            attr_data = {
                "question": attr.question,
                "answer_type": attr.answer_type
            }
            if attr.categories:
                attr_data["categories"] = attr.categories
            if attr.definition:
                attr_data["definition"] = attr.definition
            data["check_attributes"].append(attr_data)
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Config gespeichert: {path}")
        print(f"\n✓ Konfiguration gespeichert: {path}")
    
    def create_config_interactive(self) -> Config:
        """Interaktiver Dialog zur Erstellung neuer Prüfmerkmale + wissenschaftlicher Parameter."""
        print("\n" + "=" * 60)
        print("Prüfmerkmale definieren")
        print("=" * 60)
        print("\nSie können eigene Prüfmerkmale definieren, die für jede")
        print("Textantwort ausgewertet werden.")
        print()
        
        print("\n--- Untersuchungsfrage (optional) ---")
        print("Eine übergeordnete Forschungsfrage kann zusätzlichen Kontext")
        print("für alle Prüffragen liefern.")
        research_question = input("Untersuchungsfrage (Enter zum Überspringen): ").strip()
        research_question = research_question if research_question else None
        
        if research_question:
            print(f"✓ Untersuchungsfrage gesetzt: {research_question}")
        
        check_attributes = []
        
        while True:
            print(f"\n--- Prüfmerkmal {len(check_attributes) + 1} ---")
            
            question = input("Prüffrage (oder Enter zum Beenden): ").strip()
            if not question:
                if not check_attributes:
                    print("Mindestens ein Prüfmerkmal muss definiert werden.")
                    continue
                break
            
            print("\nAntworttyp:")
            print("  1. Boolean (Ja/Nein)")
            print("  2. Kategorial (mehrere Kategorien)")
            
            while True:
                choice = input("Wählen Sie (1 oder 2): ").strip()
                if choice in ["1", "2"]:
                    break
                print("Ungültige Eingabe. Bitte 1 oder 2 wählen.")
            
            if choice == "1":
                print("\nDefinition/Regeln (optional, Enter zum Überspringen):")
                definition = input("Definition: ").strip()
                definition = definition if definition else None
                
                try:
                    attr = CheckAttribute(
                        question=question,
                        answer_type="boolean",
                        definition=definition
                    )
                    check_attributes.append(attr)
                    print(f"✓ Boolean-Prüfmerkmal hinzugefügt: {question}")
                    if definition:
                        print(f"  Definition: {definition}")
                except ValueError as e:
                    print(f"✗ Fehler: {e}")
                    continue
            else:
                print("\nKategorien eingeben (mindestens 2, durch Komma getrennt):")
                categories_input = input("Kategorien: ").strip()
                categories = [cat.strip() for cat in categories_input.split(",")]
                categories = [cat for cat in categories if cat]
                
                if len(categories) < 2:
                    print("✗ Mindestens 2 Kategorien erforderlich.")
                    continue
                
                print("\nMehrfachkodierung zulässig?")
                print("  j = Ja (mehrere Kategorien können gleichzeitig zutreffen)")
                print("  n = Nein (nur eine Kategorie kann zutreffen)")
                while True:
                    multi_choice = input("Mehrfachkodierung (j/n): ").strip().lower()
                    if multi_choice in ["j", "ja", "y", "yes", "n", "nein", "no"]:
                        break
                    print("Ungültige Eingabe. Bitte j oder n wählen.")
                
                allow_multi = multi_choice in ["j", "ja", "y", "yes"]
                answer_type = "multi_categorical" if allow_multi else "categorical"
                
                print("\nDefinition/Regeln (optional, Enter zum Überspringen):")
                definition = input("Definition: ").strip()
                definition = definition if definition else None
                
                try:
                    attr = CheckAttribute(
                        question=question,
                        answer_type=answer_type,
                        categories=categories,
                        definition=definition
                    )
                    check_attributes.append(attr)
                    multi_text = " (Mehrfachkodierung)" if allow_multi else ""
                    print(f"✓ Kategoriales Prüfmerkmal hinzugefügt{multi_text}: {question}")
                    print(f"  Kategorien: {', '.join(categories)}")
                    if definition:
                        print(f"  Definition: {definition}")
                except ValueError as e:
                    print(f"✗ Fehler: {e}")
                    continue
        
        # Wissenschaftliche Konfiguration (optional)
        print("\n--- Wissenschaftliche Parameter (optional) ---")
        print("Aktivieren Sie optionale Parameter für methodische Robustheit.")
        print()
        
        scientific = None
        science_choice = input("Wissenschaftlichen Modus aktivieren? (j/n): ").strip().lower()
        
        if science_choice in ["j", "ja", "y", "yes"]:
            multi_choice = input("Multi-Model-Intercoder aktivieren? (j/n): ").strip().lower()
            multi_coder = multi_choice in ["j", "ja", "y", "yes"]
            
            coder_models = ["gpt-4o-mini"]
            primary_coder = "model_1"
            if multi_coder:
                models_input = input("Modelle (kommagetrennt, default: gpt-4o-mini,gpt-4o): ").strip()
                if models_input:
                    coder_models = [m.strip() for m in models_input.split(",") if m.strip()]
                else:
                    coder_models = ["gpt-4o-mini", "gpt-4o"]
                
                print(f"  Kodierer-Modelle: {', '.join(coder_models)}")
                
                print("\nPrimärer Kodierer:")
                print("  1. model_1 (erstes Modell in der Liste)")
                print("  2. highest_confidence (hoechste Konfidenz)")
                strategy_choice = input("Strategie (1/2, default: 1): ").strip()
                primary_coder = "highest_confidence" if strategy_choice == "2" else "model_1"
                print(f"  Strategie: {primary_coder}")
            
            threshold_input = input("Konfidenz-Schwellwert (0-100, default: 70): ").strip()
            confidence_threshold = 70
            if threshold_input:
                try:
                    confidence_threshold = int(threshold_input)
                    if not 0 <= confidence_threshold <= 100:
                        print("  Ungueltiger Wert, verwende 70")
                        confidence_threshold = 70
                    else:
                        print(f"  Schwellwert: {confidence_threshold}%")
                except ValueError:
                    print("  Ungueltige Eingabe, verwende 70")
            
            seed_input = input("Seed fuer Reproduzierbarkeit (Enter fuer None): ").strip()
            seed = None
            if seed_input:
                try:
                    seed = int(seed_input)
                    print(f"  Seed: {seed}")
                except ValueError:
                    print("  Ungueltiger Seed, ignoriere")
            
            scientific = ScientificConfig(
                multi_coder=multi_coder,
                coder_models=coder_models,
                primary_coder=primary_coder if multi_coder else "model_1",
                confidence_threshold=confidence_threshold,
                seed=seed
            )
            
            print(f"\n  Wissenschaftlicher Modus aktiviert")
            print(f"    Multi-Coder: {multi_coder}")
            print(f"    Konfidenz-Schwellwert: {confidence_threshold}%")
        
        # Erstelle Config
        config = Config(
            check_attributes=check_attributes,
            research_question=research_question,
            scientific=scientific
        )
        
        print("\n" + "=" * 60)
        if research_question:
            print(f"  Untersuchungsfrage: {research_question}")
        print(f"  {len(check_attributes)} Prüfmerkmal(e) definiert")
        if scientific:
            print(f"  Wissenschaftlicher Modus aktiviert")
            print(f"    Multi-Coder: {scientific.multi_coder}")
            print(f"    Konfidenz-Schwellwert: {scientific.confidence_threshold}%")
        print("=" * 60)
        
        logger.info(f"{len(check_attributes)} Prüfmerkmal(e) interaktiv erstellt")
        
        return config
    
    def load_or_create_config(self, directory: Path = Path(".")) -> Config:
        """Lädt existierende Config oder erstellt neue interaktiv."""
        config_path = self.find_config_file(directory)
        
        if config_path:
            print(f"\n✓ Config-Datei gefunden: {config_path}")
            choice = input("Möchten Sie diese laden? (j/n): ").strip().lower()
            
            if choice in ["j", "ja", "y", "yes"]:
                try:
                    config = self.load_config(config_path)
                    print(f"✓ {len(config.check_attributes)} Prüfmerkmal(e) geladen")
                    print(f"✓ Provider: {config.provider}")
                    print(f"✓ Verwendetes Modell: {config.model}")
                    if config.text_column_name:
                        print(f"✓ Textspaltenname: {config.text_column_name}")
                    if config.research_question:
                        print(f"✓ Untersuchungsfrage: {config.research_question}")
                    if config.scientific:
                        print(f"✓ Wissenschaftlicher Modus: aktiviert")
                    return config
                except InvalidConfigError as e:
                    print(f"✗ Fehler beim Laden: {e}")
                    print("Erstelle neue Konfiguration...")
        
        config = self.create_config_interactive()
        
        save_choice = input("\nMöchten Sie die Konfiguration speichern? (j/n): ").strip().lower()
        if save_choice in ["j", "ja", "y", "yes"]:
            save_path = directory / "QlassifAI_config.json"
            self.save_config(config, save_path)
        
        return config
