"""Mode Selector für Qlassif-AI - Wahl zwischen Excel und PDF Modus"""

import logging

logger = logging.getLogger(__name__)


class ModeSelector:
    """Behandelt Moduswahl beim Anwendungsstart"""
    
    def select_mode(self) -> str:
        """
        Fordert Benutzer auf, Verarbeitungsmodus zu wählen.
        
        Returns:
            "excel" oder "pdf"
        """
        print("\n" + "="*60)
        print("Qlassif-AI - Moduswahl")
        print("="*60)
        
        while True:
            print("\nSollen Excel-Tabellen oder PDF-Dateien ausgewertet werden?")
            print("  [1] Excel-Tabellen")
            print("  [2] PDF-Dateien")
            
            choice = input("\nBitte wählen Sie (1 oder 2): ").strip()
            
            if choice == "1":
                logger.info("Excel-Modus gewählt")
                return "excel"
            elif choice == "2":
                logger.info("PDF-Modus gewählt")
                return "pdf"
            else:
                print("❌ Ungültige Eingabe. Bitte wählen Sie 1 oder 2.")
                logger.warning(f"Ungültige Moduswahl: {choice}")
