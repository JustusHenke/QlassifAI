"""Config Manager für Prüfmerkmale-Verwaltung"""

import json
from pathlib import Path
from typing import Optional
from models import CheckAttribute, Config
from logging_config import get_logger

logger = get_logger("config_manager")


class InvalidConfigError(Exception):
    """Fehler bei ungültiger Config-Datei"""
    pass


class ConfigManager:
    """Verwaltet benutzerdefinierte Prüfmerkmale (laden, erstellen, speichern)"""
    
    def __init__(self):
        """Initialisiert ConfigManager"""
        pass
    
    def find_config_file(self, directory: Path = Path(".")) -> Optional[Path]:
        """
        Sucht nach QlassifAI_config.json im Verzeichnis.
        
        Args:
            directory: Verzeichnis zum Durchsuchen
            
        Returns:
            Pfad zur QlassifAI_config.json oder None
        """
        config_path = directory / "QlassifAI_config.json"
        
        if config_path.exists() and config_path.is_file():
            logger.info(f"Config-Datei gefunden: {config_path}")
            return config_path
        
        logger.info(f"Keine QlassifAI_config.json gefunden in {directory}")
        return None
    
    def load_config(self, config_path: Path) -> Config:
        """
        Lädt und validiert Config-Datei.
        
        Args:
            config_path: Pfad zur Config-Datei
            
        Returns:
            Config-Objekt
            
        Raises:
            InvalidConfigError: Bei ungültiger Config
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.info(f"Config-Datei geladen: {config_path}")
            
            # Validiere Struktur
            if "check_attributes" not in data:
                raise InvalidConfigError("Fehlendes Feld: 'check_attributes'")
            
            # Konvertiere zu CheckAttribute-Objekten
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
            
            # Erstelle Config
            version = data.get("version", "1.0")
            model = data.get("model", "gpt-4o-mini")
            provider = data.get("provider", "openai")
            text_column_name = data.get("text_column_name")
            research_question = data.get("research_question")
            include_reasoning = data.get("include_reasoning", True)  # Default: True
            config = Config(
                check_attributes=check_attributes,
                version=version,
                model=model,
                provider=provider,
                text_column_name=text_column_name,
                research_question=research_question,
                include_reasoning=include_reasoning
            )
            
            logger.info(f"{len(check_attributes)} Prüfmerkmal(e) geladen, Provider: {provider}, Modell: {model}")
            if text_column_name:
                logger.info(f"Textspaltenname: {text_column_name}")
            if research_question:
                logger.info(f"Untersuchungsfrage: {research_question}")
            logger.info(f"Begründungen einbeziehen: {include_reasoning}")
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
        """
        Speichert Config als JSON.
        
        Args:
            config: Zu speichernde Config
            path: Zielpfad (default: QlassifAI_config.json)
        """
        # Konvertiere zu Dictionary
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
        
        # Nur hinzufügen wenn nicht Default (True)
        if not config.include_reasoning:
            data["include_reasoning"] = False
        
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
        
        # Speichere als JSON
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Config gespeichert: {path}")
        print(f"\n✓ Konfiguration gespeichert: {path}")
    
    def create_config_interactive(self) -> Config:
        """
        Interaktiver Dialog zur Erstellung neuer Prüfmerkmale.
        
        Returns:
            Erstellte Config
        """
        print("\n" + "=" * 60)
        print("Prüfmerkmale definieren")
        print("=" * 60)
        print("\nSie können eigene Prüfmerkmale definieren, die für jede")
        print("Textantwort ausgewertet werden.")
        print()
        
        # Optionale Untersuchungsfrage
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
            
            # Frage eingeben
            question = input("Prüffrage (oder Enter zum Beenden): ").strip()
            if not question:
                if not check_attributes:
                    print("Mindestens ein Prüfmerkmal muss definiert werden.")
                    continue
                break
            
            # Antworttyp wählen
            print("\nAntworttyp:")
            print("  1. Boolean (Ja/Nein)")
            print("  2. Kategorial (mehrere Kategorien)")
            
            while True:
                choice = input("Wählen Sie (1 oder 2): ").strip()
                if choice in ["1", "2"]:
                    break
                print("Ungültige Eingabe. Bitte 1 oder 2 wählen.")
            
            if choice == "1":
                # Boolean
                print("\nDefinition/Regeln (optional, Enter zum Überspringen):")
                print("Hier können Sie Kontext geben, der für die Entscheidung wichtig ist.")
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
                # Categorical
                print("\nKategorien eingeben (mindestens 2, durch Komma getrennt):")
                categories_input = input("Kategorien: ").strip()
                categories = [cat.strip() for cat in categories_input.split(",")]
                categories = [cat for cat in categories if cat]  # Entferne leere
                
                if len(categories) < 2:
                    print("✗ Mindestens 2 Kategorien erforderlich.")
                    continue
                
                # Frage nach Mehrfachkodierung
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
                print("Hier können Sie Kontext geben, der für die Entscheidung wichtig ist.")
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
        
        # Erstelle Config
        config = Config(
            check_attributes=check_attributes,
            research_question=research_question
        )
        
        print("\n" + "=" * 60)
        if research_question:
            print(f"✓ Untersuchungsfrage: {research_question}")
        print(f"✓ {len(check_attributes)} Prüfmerkmal(e) definiert")
        print("=" * 60)
        
        logger.info(f"{len(check_attributes)} Prüfmerkmal(e) interaktiv erstellt")
        
        return config
    
    def load_or_create_config(self, directory: Path = Path(".")) -> Config:
        """
        Lädt existierende Config oder erstellt neue interaktiv.
        
        Args:
            directory: Verzeichnis zum Durchsuchen
            
        Returns:
            Config-Objekt
        """
        # Suche nach existierender Config
        config_path = self.find_config_file(directory)
        
        if config_path:
            # Frage Benutzer, ob laden
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
                    return config
                except InvalidConfigError as e:
                    print(f"✗ Fehler beim Laden: {e}")
                    print("Erstelle neue Konfiguration...")
        
        # Erstelle neue Config
        config = self.create_config_interactive()
        
        # Frage, ob speichern
        save_choice = input("\nMöchten Sie die Konfiguration speichern? (j/n): ").strip().lower()
        if save_choice in ["j", "ja", "y", "yes"]:
            save_path = directory / "QlassifAI_config.json"
            self.save_config(config, save_path)
        
        return config
