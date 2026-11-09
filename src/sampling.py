"""Sampling-Utilities für Qlassif-AI - Offset und Zufallsstichprobe"""

import random
from typing import Optional, Sequence
from logging_config import get_logger

logger = get_logger("sampling")


def apply_sampling(items: Sequence, sample_size: Optional[int] = None,
                   offset: int = 0, seed: Optional[int] = None) -> list:
    """
    Wendet Offset und Zufallsstichprobe auf eine Fall-Liste an.

    Reihenfolge: Zuerst werden die ersten `offset` Fälle übersprungen,
    danach wird aus dem Rest eine Zufallsstichprobe der Größe `sample_size`
    gezogen (falls gesetzt). Die Ergebnisliste behält die ursprüngliche
    Reihenfolge bei.

    Args:
        items: Liste von Fällen (z.B. Zeilen-Indizes oder Dateipfade)
        sample_size: Anzahl zufällig auszuwählender Fälle (None = alle)
        offset: Anzahl am Anfang zu überspringender Fälle
        seed: Optionaler Seed für reproduzierbare Stichproben

    Returns:
        Ausgewählte Fälle in ursprünglicher Reihenfolge
    """
    items = list(items)
    total = len(items)

    if offset:
        items = items[offset:]
        logger.info(f"Offset angewendet: {offset} Fälle übersprungen ({total} -> {len(items)})")

    if sample_size is not None and sample_size < len(items):
        rng = random.Random(seed)
        chosen = sorted(rng.sample(range(len(items)), sample_size))
        items = [items[i] for i in chosen]
        logger.info(f"Zufallsstichprobe: {sample_size} von {len(items)} Fällen gezogen (seed={seed})")

    return items
