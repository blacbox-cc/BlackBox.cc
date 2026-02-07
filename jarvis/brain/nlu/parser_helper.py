"""
ParserHelper: Funciones helper para parser usando FASE 3 helpers.

En lugar de modificar parser.py directamente (alto riesgo), creamos helpers
que parser.py puede adoptar gradualmente.

Objetivos:
- Proof-of-concept: mostrar cómo usar ConfidenceHelper y MatchResult
- Sin regresiones: parser.py sigue funcionando sin cambios
- Gradual: parser.py puede migrar método por método
"""

import re
from typing import Tuple, Dict, Any, Optional, List
from core.helpers import ConfidenceHelper, ConfidenceScore, MatchResult


class ParserHelper:
    """
    Helper functions para IntentParser usando nuevos helpers FASE 3.
    
    Provee versiones alternativas de métodos del parser que usan
    ConfidenceHelper y MatchResult en lugar de floats y dicts.
    """
    
    @staticmethod
    def match_pattern_with_confidence(
        text: str,
        patterns: List[str],
        intent: str
    ) -> MatchResult:
        """
        Versión mejorada de pattern matching con ConfidenceHelper.
        
        Args:
            text: Texto normalizado a matchear
            patterns: Lista de regex patterns
            intent: Intent asociado a estos patterns
        
        Returns:
            MatchResult con confidence explícito
        """
        text_lower = text.lower()
        
        for pattern in patterns:
            try:
                match = re.search(pattern, text_lower, re.IGNORECASE)
                if match:
                    # Calcular confianza basada en calidad del match
                    pattern_quality = ParserHelper._assess_pattern_quality(
                        pattern, text_lower, match
                    )
                    
                    confidence = ConfidenceHelper.from_pattern_match(
                        pattern_quality=pattern_quality
                    )
                    
                    return MatchResult.success(
                        intent=intent,
                        confidence=confidence,
                        entities={},
                        pattern_used=pattern,
                        metadata={
                            "match_start": match.start(),
                            "match_end": match.end(),
                            "matched_text": match.group(0)
                        }
                    )
            except re.error:
                # Pattern inválido, skip
                continue
        
        # No match
        return MatchResult.no_match(reason=f"Sin patterns que matcheen para {intent}")
    
    @staticmethod
    def _assess_pattern_quality(pattern: str, text: str, match: re.Match) -> float:
        """
        Evalúa calidad de un pattern match.
        
        Factores:
        - Match cubre mucho del texto: mejor calidad
        - Pattern específico (no catch-all): mejor calidad
        - Match al inicio del texto: mejor calidad
        
        Returns:
            float: calidad [0.0 - 1.0]
        """
        # Coverage: qué porcentaje del texto matcheó
        matched_text = match.group(0)
        coverage = len(matched_text) / len(text) if text else 0.0
        
        # Specificity: patterns largos son más específicos
        pattern_length = len(pattern)
        specificity = min(1.0, pattern_length / 20.0)  # 20+ chars = máxima especificidad
        
        # Position: matches al inicio son más relevantes
        position_score = 1.0 if match.start() == 0 else 0.8
        
        # Combinar factores (pesos ajustables)
        quality = (
            coverage * 0.5 +
            specificity * 0.3 +
            position_score * 0.2
        )
        
        # Normalizar a [0.6 - 1.0] (nunca muy bajo si matcheó)
        return 0.6 + (quality * 0.4)
    
    @staticmethod
    def infer_from_entities_with_confidence(
        entities: Dict[str, Any]
    ) -> MatchResult:
        """
        Infiere intent desde entities con confianza explícita.
        
        Ejemplo: si entities tiene "app_name", probablemente sea "open_app".
        
        Args:
            entities: Dict de entities extraídos
        
        Returns:
            MatchResult con intent inferido o no_match
        """
        # Mapeo de entities → intent
        entity_intent_map = {
            "app_name": "open_app",
            "app": "open_app",
            "file_name": "search_file",
            "file": "search_file",
            "path": "search_file",
            "time_query": "get_time",
            "date_query": "get_time",
            "note_content": "create_note",
            "search_query": "web_search",
        }
        
        for entity_key, intent in entity_intent_map.items():
            if entity_key in entities and entities[entity_key]:
                # Entity encontrado: alta confianza
                confidence = ConfidenceHelper.from_pattern_match(
                    pattern_quality=0.95,  # Entities son muy confiables
                    entity_match=1.0
                )
                
                return MatchResult.success(
                    intent=intent,
                    confidence=confidence,
                    entities=entities,
                    metadata={"inference_source": f"entity:{entity_key}"}
                )
        
        # Sin entities relevantes
        return MatchResult.no_match(reason="Sin entities que infieran intent")
    
    @staticmethod
    def soft_match_with_confidence(
        text: str,
        phrase_mappings: Dict[str, List[str]]
    ) -> MatchResult:
        """
        Soft phrase matching con ConfidenceHelper.
        
        Args:
            text: Texto del usuario (normalizado)
            phrase_mappings: Dict de {intent: [phrases]}
        
        Returns:
            MatchResult con mejor match
        """
        text_lower = text.lower()
        best_match = None
        best_similarity = 0.0
        best_intent = None
        
        for intent, phrases in phrase_mappings.items():
            for phrase in phrases:
                # Exact match
                if text_lower == phrase.lower():
                    confidence = ConfidenceHelper.perfect(
                        reasoning=f"Exact match con '{phrase}'"
                    )
                    return MatchResult.success(
                        intent=intent,
                        confidence=confidence,
                        entities={},
                        metadata={"match_type": "exact", "phrase": phrase}
                    )
                
                # Contains match
                if phrase.lower() in text_lower:
                    # Calcular similarity basado en coverage
                    similarity = len(phrase) / len(text_lower)
                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_intent = intent
                        best_match = phrase
        
        if best_intent:
            confidence = ConfidenceHelper.from_soft_match(
                similarity=best_similarity,
                threshold=0.5,
                matched_tokens=len(best_match.split()),
                total_tokens=len(text_lower.split())
            )
            
            return MatchResult.success(
                intent=best_intent,
                confidence=confidence,
                entities={},
                pattern_used=best_match,
                metadata={"match_type": "contains", "phrase": best_match}
            )
        
        return MatchResult.no_match(reason="Sin soft phrases que matcheen")
    
    @staticmethod
    def combine_matches(
        matches: List[MatchResult],
        strategy: str = "highest_confidence"
    ) -> MatchResult:
        """
        Combina múltiples MatchResults para elegir el mejor.
        
        Args:
            matches: Lista de MatchResults
            strategy: "highest_confidence" o "weighted_average"
        
        Returns:
            Mejor MatchResult según estrategia
        """
        # Filtrar solo matches exitosos
        valid_matches = [m for m in matches if m.matched]
        
        if not valid_matches:
            return MatchResult.no_match(reason="Sin matches válidos para combinar")
        
        if strategy == "highest_confidence":
            # Elegir match con mayor confianza
            best = max(valid_matches, key=lambda m: m.confidence.value)
            
            # Si hay candidatos cercanos, ajustar confianza por ambigüedad
            if len(valid_matches) > 1:
                scores_sorted = sorted(
                    [m.confidence.value for m in valid_matches],
                    reverse=True
                )
                
                adjusted_confidence = ConfidenceHelper.from_multiple_candidates(
                    top_score=scores_sorted[0],
                    second_score=scores_sorted[1]
                )
                
                return MatchResult.success(
                    intent=best.intent,
                    confidence=adjusted_confidence,
                    entities=best.entities,
                    pattern_used=best.pattern_used,
                    alternatives=[m.intent for m in valid_matches if m != best],
                    metadata={
                        **best.metadata,
                        "combination_strategy": strategy,
                        "total_candidates": len(valid_matches)
                    }
                )
            
            return best
        
        # Otros strategies pueden agregarse aquí
        return valid_matches[0]
