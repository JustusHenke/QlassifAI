"""Custom Exceptions für Qlassif-AI"""


class QlassifError(Exception):
    """Basis-Exception für alle Qlassif-AI Fehler"""
    pass


class ConfigError(QlassifError):
    """Fehler bei der Konfiguration"""
    pass


class InvalidConfigError(ConfigError):
    """Fehler bei ungültiger Config-Datei"""
    pass


class APIKeyError(QlassifError):
    """Fehler bei API-Key-Verwaltung"""
    pass


class MissingAPIKeyError(APIKeyError):
    """Fehler wenn kein API-Key gefunden wird"""
    pass


class ExcelError(QlassifError):
    """Fehler bei Excel-Operationen"""
    pass


class NoCompatibleSheetsError(ExcelError):
    """Fehler wenn keine kompatiblen Sheets gefunden werden"""
    pass


class PDFError(QlassifError):
    """Fehler bei PDF-Operationen"""
    pass


class PDFExtractionError(PDFError):
    """Fehler bei PDF-Textextraktion"""
    pass


class LLMError(QlassifError):
    """Fehler bei LLM-Operationen"""
    pass


class FileDiscoveryError(QlassifError):
    """Fehler bei der Dateisuche"""
    pass
