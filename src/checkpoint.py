"""Checkpoint-Verwaltung für Qlassif-AI - Zwischenergebnisse bei Abbruch sichern"""

import json
import hashlib
from pathlib import Path
from typing import Dict
from models import AnalysisResult, MergedResult
from logging_config import get_logger

logger = get_logger("checkpoint")


def _config_hash(fingerprint: dict) -> str:
    """Stabiler Kurz-Hash über relevante Config-Bestandteile."""
    payload = json.dumps(fingerprint, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _sanitize_keywords(keywords) -> list:
    """Stellt sicher, dass die Keyword-Liste 2-4 Elemente hat (Validierung in AnalysisResult)."""
    kw = [k for k in (keywords or []) if k]
    if len(kw) < 2:
        kw = (kw + ["unbekannt", "unbekannt"])[:2]
    return kw[:4]


def result_to_dict(result: AnalysisResult) -> dict:
    """AnalysisResult in speicherbares Dict umwandeln."""
    return {
        "paraphrase": result.paraphrase,
        "sentiment": result.sentiment,
        "sentiment_reason": result.sentiment_reason,
        "keywords": list(result.keywords),
        "custom_checks": result.custom_checks,
        "custom_checks_reasons": result.custom_checks_reasons,
        "error": result.error,
        "prompt_tokens": result.prompt_tokens,
        "completion_tokens": result.completion_tokens,
        "total_tokens": result.total_tokens,
        "confidence_scores": result.confidence_scores,
        "confidence_reasons": result.confidence_reasons,
        "alternative_codes": result.alternative_codes,
        "low_confidence_flags": list(result.low_confidence_flags),
    }


def result_from_dict(data: dict) -> AnalysisResult:
    """Dict in AnalysisResult zurückwandeln."""
    return AnalysisResult(
        paraphrase=data.get("paraphrase", ""),
        sentiment=data.get("sentiment", "gemischt"),
        sentiment_reason=data.get("sentiment_reason", ""),
        keywords=_sanitize_keywords(data.get("keywords")),
        custom_checks=data.get("custom_checks", {}),
        custom_checks_reasons=data.get("custom_checks_reasons", {}),
        error=data.get("error"),
        prompt_tokens=data.get("prompt_tokens", 0),
        completion_tokens=data.get("completion_tokens", 0),
        total_tokens=data.get("total_tokens", 0),
        confidence_scores=data.get("confidence_scores", {}),
        confidence_reasons=data.get("confidence_reasons", {}),
        alternative_codes=data.get("alternative_codes", {}),
        low_confidence_flags=data.get("low_confidence_flags", []),
    )


def merged_to_dict(result: MergedResult) -> dict:
    """MergedResult (PDF-Modus) in speicherbares Dict umwandeln."""
    return {
        "filename": result.filename,
        "paraphrase": result.paraphrase,
        "sentiment": result.sentiment,
        "sentiment_reason": result.sentiment_reason,
        "keywords": list(result.keywords),
        "custom_checks": result.custom_checks,
        "custom_checks_reasons": result.custom_checks_reasons,
        "keyword_category": result.keyword_category,
        "chunk_count": result.chunk_count,
        "error": result.error,
    }


def merged_from_dict(data: dict) -> MergedResult:
    """Dict in MergedResult zurückwandeln."""
    return MergedResult(
        filename=data.get("filename", ""),
        paraphrase=data.get("paraphrase", ""),
        sentiment=data.get("sentiment", 0),
        sentiment_reason=data.get("sentiment_reason", ""),
        keywords=_sanitize_keywords(data.get("keywords")),
        custom_checks=data.get("custom_checks", {}),
        custom_checks_reasons=data.get("custom_checks_reasons", {}),
        keyword_category=data.get("keyword_category", ""),
        chunk_count=max(1, data.get("chunk_count", 1)),
        error=data.get("error"),
    )


class CheckpointManager:
    """
    Speichert Zwischenergebnisse JSON-basiert und lädt sie für die
    Wiederaufnahme nach einem Abbruch.

    Der Checkpoint ist an (a) die Quelldatei und (b) einen Hash der
    analyse-relevanten Config gebunden. Passt beides, werden bereits
    bearbeitete Fälle beim nächsten Lauf übersprungen.
    """

    def __init__(self, path: Path, source_id: str, fingerprint: dict):
        """
        Args:
            path: Pfad der Checkpoint-Datei
            source_id: Identifikation der Quelldatei (Name + Änderungszeit)
            fingerprint: Analyse-relevante Config (wird gehasht)
        """
        self.path = Path(path)
        self.source_id = source_id
        self._config_hash = _config_hash(fingerprint)
        self.entries: Dict[str, dict] = {}
        self._load()

    def _load(self):
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if data.get("source_id") == self.source_id and data.get("config_hash") == self._config_hash:
                self.entries = data.get("results", {})
                logger.info(f"Checkpoint geladen: {len(self.entries)} Einträge")
            else:
                logger.info("Checkpoint passt nicht zur Quelldatei/Config und wird ignoriert")
        except Exception as e:
            logger.warning(f"Checkpoint unlesbar ({e}), wird ignoriert")

    def __len__(self) -> int:
        return len(self.entries)

    def has_entries(self) -> bool:
        return bool(self.entries)

    def get(self, key: str):
        return self.entries.get(key)

    def add(self, key: str, result_dict: dict):
        self.entries[key] = result_dict

    def clear(self):
        """Alle Einträge verwerfen und Checkpoint-Datei löschen."""
        self.entries = {}
        self.delete_file()

    def delete_file(self):
        try:
            if self.path.exists():
                self.path.unlink()
                logger.info(f"Checkpoint gelöscht: {self.path}")
        except OSError as e:
            logger.warning(f"Checkpoint konnte nicht gelöscht werden: {e}")

    def save(self):
        """Checkpoint atomar speichern (erst tmp, dann ersetzen)."""
        data = {
            "source_id": self.source_id,
            "config_hash": self._config_hash,
            "results": self.entries,
        }
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self.path)
