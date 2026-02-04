"""LLM Analyzer für Textanalyse"""

import json
import time
from typing import List, Union
from openai import OpenAI, APIError, APITimeoutError, RateLimitError
from models import CheckAttribute, AnalysisResult
from logging_config import get_logger

logger = get_logger("llm_analyzer")


class LLMAnalyzer:
    """Führt alle LLM-basierten Analysen durch"""
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini", provider: str = "openai", timeout: float = 60.0):
        """
        Initialisiert LLMAnalyzer.
        
        Args:
            api_key: API-Key (OpenAI oder OpenRouter)
            model: Zu verwendendes Modell
            provider: "openai" oder "openrouter"
            timeout: Timeout in Sekunden
        """
        self.provider = provider
        self.model = model
        self.timeout = timeout
        
        if provider == "openrouter":
            # OpenRouter verwendet OpenAI-kompatible API
            self.client = OpenAI(
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1",
                timeout=timeout
            )
            logger.info(f"LLMAnalyzer initialisiert mit OpenRouter, Modell: {model}, Timeout: {timeout}s")
        else:
            # Standard OpenAI
            self.client = OpenAI(api_key=api_key, timeout=timeout)
            logger.info(f"LLMAnalyzer initialisiert mit OpenAI, Modell: {model}, Timeout: {timeout}s")
    
    def _build_analysis_prompt(self, text: str, check_attributes: List[CheckAttribute], 
                              research_question: str = None) -> str:
        """
        Erstellt strukturierten Prompt für LLM.
        
        Args:
            text: Zu analysierender Text
            check_attributes: Benutzerdefinierte Prüfmerkmale
            research_question: Optionale übergeordnete Untersuchungsfrage für Kontext
            
        Returns:
            Formatierter Prompt
        """
        prompt = f"""Analysiere folgenden Text und gib die Ergebnisse im JSON-Format zurück:

Text: "{text}"
"""
        
        # Füge Untersuchungsfrage hinzu, falls vorhanden
        if research_question:
            prompt += f"""
KONTEXT - Übergeordnete Untersuchungsfrage:
"{research_question}"

Beachte diese Untersuchungsfrage bei der Bewertung aller Prüfmerkmale.
"""
        
        prompt += """
Bitte liefere:
1. Paraphrase: Eine KOMPAKTE, umformulierte Version der Kernaussage (maximal 1-2 Sätze)
2. Sentiment: Klassifiziere als "positiv", "negativ" oder "gemischt"
3. Sentiment_Begründung: KURZE Begründung für die Sentiment-Klassifikation (maximal 30 Wörter)
4. Keywords: Extrahiere 2-4 Keywords (textnah, leicht abstrahiert)
"""
        
        # Füge benutzerdefinierte Prüfmerkmale hinzu
        if check_attributes:
            prompt += "\n5. Untersuche ob folgende Prüfmerkmale auf den Text zutreffen:\n"
            for idx, attr in enumerate(check_attributes, start=1):
                prompt += f"   - {attr.question}"
                if attr.answer_type == "boolean":
                    prompt += " (Antwort: true, false, oder null wenn kein Bezug zum Thema besteht)"
                elif attr.answer_type == "multi_categorical":
                    prompt += f" (Antwort: Array von Kategorien aus {attr.categories}, oder null wenn kein Bezug zum Thema besteht. Mehrere Kategorien können gleichzeitig zutreffen!)"
                else:  # categorical
                    prompt += f" (Antwort: eine von {attr.categories}, oder null wenn kein Bezug zum Thema besteht)"
                
                # Füge Definition hinzu, falls vorhanden
                if attr.definition:
                    prompt += f"\n     Definition/Regeln: {attr.definition}"
                prompt += "\n"
            
            prompt += "\n6. Begründungen für Prüfmerkmale:\n"
            prompt += "   Für jedes Prüfmerkmal: KURZE Begründung (maximal 20 Wörter) warum diese Antwort gewählt wurde.\n"
        
        prompt += """
Antwortformat (strikt einhalten):
{
  "paraphrase": "...",
  "sentiment": "positiv|negativ|gemischt",
  "sentiment_reason": "...",
  "keywords": ["keyword1", "keyword2", "keyword3"],
  "custom_checks": {
"""
        
        if check_attributes:
            for idx, attr in enumerate(check_attributes):
                # Verwende Frage als Key
                prompt += f'    "{attr.question}": '
                if attr.answer_type == "boolean":
                    prompt += "true|false|null"
                elif attr.answer_type == "multi_categorical":
                    prompt += f'["{attr.categories[0]}", ...]|null'
                else:  # categorical
                    prompt += f'"{attr.categories[0]}|..."|null'
                
                if idx < len(check_attributes) - 1:
                    prompt += ",\n"
                else:
                    prompt += "\n"
        
        prompt += """  },
  "custom_checks_reasons": {
"""
        
        if check_attributes:
            for idx, attr in enumerate(check_attributes):
                prompt += f'    "{attr.question}": "kurze Begründung (max 20 Wörter)"'
                if idx < len(check_attributes) - 1:
                    prompt += ",\n"
                else:
                    prompt += "\n"
        
        prompt += """  }
}

WICHTIG: 
- Antworte NUR mit dem JSON-Objekt, ohne zusätzlichen Text
- Halte die Paraphrase KOMPAKT (maximal 1-2 Sätze)
- Halte die Sentiment_Begründung KURZ (maximal 30 Wörter)
- Halte die Prüfmerkmal-Begründungen SEHR KURZ (maximal 20 Wörter)
- Setze Prüfmerkmale auf null, wenn der Text KEINEN Bezug zum Thema hat"""
        
        return prompt
    
    def _clean_json_response(self, response_text: str) -> str:
        """
        Bereinigt LLM-Antwort von Markdown-Code-Blöcken und anderen Formatierungen.
        
        Args:
            response_text: Rohe Antwort vom LLM
            
        Returns:
            Bereinigte JSON-String
        """
        # Entferne Markdown-Code-Blöcke (```json ... ``` oder ``` ... ```)
        if response_text.startswith("```"):
            # Finde Start und Ende der Code-Blöcke
            lines = response_text.split("\n")
            # Entferne erste Zeile (```json oder ```)
            if lines[0].strip().startswith("```"):
                lines = lines[1:]
            # Entferne letzte Zeile (```)
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            response_text = "\n".join(lines)
        
        return response_text.strip()
    
    def _parse_llm_response(self, response_text: str, check_attributes: List[CheckAttribute]) -> AnalysisResult:
        """
        Parst strukturierte LLM-Antwort.
        
        Args:
            response_text: JSON-Antwort vom LLM
            check_attributes: Prüfmerkmale für Validierung
            
        Returns:
            AnalysisResult-Objekt
            
        Raises:
            ValueError: Bei ungültigem JSON oder fehlenden Feldern
        """
        try:
            # Bereinige die Antwort von Markdown-Code-Blöcken
            response_text = self._clean_json_response(response_text)
            
            # Logge die rohe Antwort für Debugging (nur erste 200 Zeichen)
            logger.debug(f"LLM-Antwort (erste 200 Zeichen): {response_text[:200]}")
            
            # Prüfe ob Antwort leer ist
            if not response_text or not response_text.strip():
                error_msg = "LLM hat leere Antwort zurückgegeben"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # Versuche JSON zu parsen
            data = json.loads(response_text)
            
            # Extrahiere Felder
            paraphrase = data.get("paraphrase", "")
            sentiment = data.get("sentiment", "gemischt")
            sentiment_reason = data.get("sentiment_reason", "")
            keywords = data.get("keywords", [])
            custom_checks = data.get("custom_checks", {})
            custom_checks_reasons = data.get("custom_checks_reasons", {})
            
            # Validiere und korrigiere Sentiment
            valid_sentiments = ["positiv", "negativ", "gemischt"]
            if sentiment not in valid_sentiments:
                logger.warning(f"Ungültiges Sentiment '{sentiment}', setze auf 'gemischt'")
                sentiment = "gemischt"
            
            # Validiere Keywords-Anzahl
            if len(keywords) < 2:
                logger.warning(f"Zu wenige Keywords ({len(keywords)}), fülle auf")
                while len(keywords) < 2:
                    keywords.append("unbekannt")
            elif len(keywords) > 4:
                logger.warning(f"Zu viele Keywords ({len(keywords)}), kürze auf 4")
                keywords = keywords[:4]
            
            # Erstelle AnalysisResult
            result = AnalysisResult(
                paraphrase=paraphrase,
                sentiment=sentiment,
                sentiment_reason=sentiment_reason,
                keywords=keywords,
                custom_checks=custom_checks,
                custom_checks_reasons=custom_checks_reasons
            )
            
            return result
            
        except json.JSONDecodeError as e:
            error_msg = f"Ungültiges JSON vom LLM: {e}"
            logger.error(error_msg)
            logger.error(f"Rohe Antwort: {response_text[:500]}")  # Logge mehr für Debugging
            raise ValueError(error_msg)
        except Exception as e:
            error_msg = f"Fehler beim Parsen der LLM-Antwort: {e}"
            logger.error(error_msg)
            logger.error(f"Rohe Antwort: {response_text[:500]}")
            raise ValueError(error_msg)
    
    def analyze_text(self, text: str, check_attributes: List[CheckAttribute], 
                    research_question: str = None, max_retries: int = 3) -> AnalysisResult:
        """
        Führt vollständige Analyse eines Textes durch.
        
        Args:
            text: Zu analysierender Text
            check_attributes: Benutzerdefinierte Prüfmerkmale
            research_question: Optionale übergeordnete Untersuchungsfrage für Kontext
            max_retries: Maximale Anzahl Wiederholungsversuche
            
        Returns:
            AnalysisResult mit Analyseergebnissen
        """
        if not text or not text.strip():
            logger.warning("Leerer Text übergeben")
            return AnalysisResult(
                paraphrase="",
                sentiment="gemischt",
                sentiment_reason="",
                keywords=["leer", "keine"],
                custom_checks={},
                custom_checks_reasons={},
                error="Leerer Text"
            )
        
        # Baue Prompt
        prompt = self._build_analysis_prompt(text, check_attributes, research_question)
        
        # Versuche API-Aufruf mit Retries
        for attempt in range(max_retries):
            try:
                logger.info(f"LLM-Analyse Versuch {attempt + 1}/{max_retries}")
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "Du bist ein Experte für Textanalyse. Antworte immer im angegebenen JSON-Format."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=1000
                )
                
                # Extrahiere Antwort
                response_text = response.choices[0].message.content
                
                # Prüfe ob Antwort None ist
                if response_text is None:
                    logger.warning(f"LLM hat None zurückgegeben (Versuch {attempt + 1}/{max_retries})")
                    if attempt < max_retries - 1:
                        logger.info("Versuche erneut...")
                        continue
                    else:
                        error_msg = "LLM hat nach mehreren Versuchen None zurückgegeben"
                        logger.error(error_msg)
                        return AnalysisResult(
                            paraphrase="",
                            sentiment="gemischt",
                            sentiment_reason="",
                            keywords=["fehler", "keine-antwort"],
                            custom_checks={},
                            custom_checks_reasons={},
                            error=error_msg
                        )
                
                response_text = response_text.strip()
                
                # Extrahiere Token-Statistiken
                usage = response.usage
                prompt_tokens = usage.prompt_tokens if usage else 0
                completion_tokens = usage.completion_tokens if usage else 0
                total_tokens = usage.total_tokens if usage else 0
                
                # Parse Antwort
                result = self._parse_llm_response(response_text, check_attributes)
                
                # Füge Token-Statistiken hinzu
                result.prompt_tokens = prompt_tokens
                result.completion_tokens = completion_tokens
                result.total_tokens = total_tokens
                
                logger.info(f"LLM-Analyse erfolgreich (Tokens: {total_tokens})")
                return result
                
            except APITimeoutError as e:
                logger.warning(f"API-Timeout (Versuch {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.info(f"Warte {wait_time}s vor erneutem Versuch...")
                    time.sleep(wait_time)
                else:
                    error_msg = f"API-Timeout nach {max_retries} Versuchen"
                    logger.error(error_msg)
                    return AnalysisResult(
                        paraphrase="",
                        sentiment="gemischt",
                        sentiment_reason="",
                        keywords=["fehler", "timeout"],
                        custom_checks={},
                        custom_checks_reasons={},
                        error=error_msg
                    )
            
            except RateLimitError as e:
                logger.warning(f"Rate-Limit erreicht (Versuch {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    wait_time = 5 * (attempt + 1)  # Längere Wartezeit bei Rate-Limit
                    logger.info(f"Warte {wait_time}s vor erneutem Versuch...")
                    time.sleep(wait_time)
                else:
                    error_msg = f"Rate-Limit nach {max_retries} Versuchen"
                    logger.error(error_msg)
                    return AnalysisResult(
                        paraphrase="",
                        sentiment="gemischt",
                        sentiment_reason="",
                        keywords=["fehler", "rate-limit"],
                        custom_checks={},
                        custom_checks_reasons={},
                        error=error_msg
                    )
            
            except APIError as e:
                logger.error(f"API-Fehler: {e}")
                return AnalysisResult(
                    paraphrase="",
                    sentiment="gemischt",
                    sentiment_reason="",
                    keywords=["fehler", "api"],
                    custom_checks={},
                    custom_checks_reasons={},
                    error=str(e)
                )
            
            except ValueError as e:
                logger.error(f"Parse-Fehler: {e}")
                if attempt < max_retries - 1:
                    logger.info("Versuche erneut...")
                    time.sleep(1)
                else:
                    return AnalysisResult(
                        paraphrase="",
                        sentiment="gemischt",
                        sentiment_reason="",
                        keywords=["fehler", "parse"],
                        custom_checks={},
                        custom_checks_reasons={},
                        error=str(e)
                    )
            
            except Exception as e:
                logger.error(f"Unerwarteter Fehler: {e}")
                return AnalysisResult(
                    paraphrase="",
                    sentiment="gemischt",
                    sentiment_reason="",
                    keywords=["fehler", "unbekannt"],
                    custom_checks={},
                    custom_checks_reasons={},
                    error=str(e)
                )
        
        # Sollte nicht erreicht werden
        return AnalysisResult(
            paraphrase="",
            sentiment="gemischt",
            sentiment_reason="",
            keywords=["fehler", "unbekannt"],
            custom_checks={},
            custom_checks_reasons={},
            error="Maximale Versuche erreicht"
        )
