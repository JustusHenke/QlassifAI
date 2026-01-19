"""Text Chunker für Qlassif-AI - Teilt große Texte in Chunks"""

import logging
import re
from typing import List
from models import Chunk

logger = logging.getLogger(__name__)


class TextChunker:
    """Teilt Text in Chunks mit Satzgrenzen-Bewusstsein"""
    
    CHUNK_SIZE = 30000  # Ziel-Chunk-Größe in Zeichen
    SEARCH_WINDOW = 500  # Suchfenster für Satzgrenzen
    
    # Regex für Satzenden (. ! ?) gefolgt von Whitespace
    SENTENCE_ENDINGS = re.compile(r'[.!?]\s+')
    
    def chunk_text(self, text: str) -> List[Chunk]:
        """
        Teilt Text in Chunks an natürlichen Grenzen.
        
        Args:
            text: Vollständiger zu teilender Text
            
        Returns:
            Liste von Chunk-Objekten
        """
        text_length = len(text)
        
        # Wenn Text <= CHUNK_SIZE, gib einzelnen Chunk zurück
        if text_length <= self.CHUNK_SIZE:
            logger.info(f"Text ({text_length} Zeichen) passt in einen Chunk")
            return [Chunk(
                chunk_id=0,
                text=text,
                char_count=text_length,
                start_position=0,
                end_position=text_length
            )]
        
        chunks = []
        current_position = 0
        chunk_id = 0
        
        while current_position < text_length:
            target_end = current_position + self.CHUNK_SIZE
            
            # Letzter Chunk
            if target_end >= text_length:
                chunk_text = text[current_position:]
                chunks.append(Chunk(
                    chunk_id=chunk_id,
                    text=chunk_text,
                    char_count=len(chunk_text),
                    start_position=current_position,
                    end_position=text_length
                ))
                logger.debug(
                    f"Chunk {chunk_id} (letzter): {len(chunk_text)} Zeichen"
                )
                break
            
            # Finde Satzgrenze nahe target_end
            split_point = self._find_split_point(text, target_end)
            
            chunk_text = text[current_position:split_point]
            chunks.append(Chunk(
                chunk_id=chunk_id,
                text=chunk_text,
                char_count=len(chunk_text),
                start_position=current_position,
                end_position=split_point
            ))
            
            logger.debug(
                f"Chunk {chunk_id}: {len(chunk_text)} Zeichen "
                f"(Position {current_position}-{split_point})"
            )
            
            current_position = split_point
            chunk_id += 1
        
        logger.info(
            f"Text ({text_length} Zeichen) in {len(chunks)} Chunks geteilt"
        )
        return chunks
    
    def _find_split_point(self, text: str, target_position: int) -> int:
        """
        Findet nächste Satzgrenze zur Zielposition.
        
        Args:
            text: Zu durchsuchender Text
            target_position: Gewünschte Split-Position
            
        Returns:
            Tatsächliche Split-Position an Satzgrenze
        """
        text_length = len(text)
        
        # Definiere Suchfenster
        search_start = max(0, target_position - self.SEARCH_WINDOW)
        search_end = min(text_length, target_position + self.SEARCH_WINDOW)
        search_window = text[search_start:search_end]
        
        # Suche nach Satzenden im Fenster
        sentence_matches = list(self.SENTENCE_ENDINGS.finditer(search_window))
        
        if not sentence_matches:
            # Fallback: Finde nächstes Whitespace
            logger.debug(
                f"Keine Satzgrenze gefunden, verwende Whitespace-Fallback"
            )
            return self._find_nearest_whitespace(text, target_position)
        
        # Finde Grenze am nächsten zur Zielposition
        target_offset = target_position - search_start
        closest_match = min(
            sentence_matches,
            key=lambda m: abs(m.end() - target_offset)
        )
        
        split_position = search_start + closest_match.end()
        
        logger.debug(
            f"Satzgrenze gefunden bei Position {split_position} "
            f"(Ziel war {target_position})"
        )
        
        return split_position
    
    def _find_nearest_whitespace(self, text: str, target_position: int) -> int:
        """
        Findet nächstes Whitespace zur Zielposition (Fallback).
        
        Args:
            text: Zu durchsuchender Text
            target_position: Gewünschte Split-Position
            
        Returns:
            Position des nächsten Whitespace
        """
        text_length = len(text)
        
        # Suche vorwärts nach Whitespace
        for i in range(target_position, min(text_length, target_position + 1000)):
            if text[i].isspace():
                return i + 1  # Nach dem Whitespace
        
        # Suche rückwärts nach Whitespace
        for i in range(target_position, max(0, target_position - 1000), -1):
            if text[i].isspace():
                return i + 1  # Nach dem Whitespace
        
        # Letzter Fallback: Verwende Zielposition
        logger.warning(
            f"Kein Whitespace in der Nähe von Position {target_position} gefunden, "
            f"verwende Zielposition"
        )
        return target_position
