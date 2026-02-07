# brain/nlu/parser.py
import re
from brain.nlu.normalizer import Normalizer
from brain.nlu.soft_phrases import get_intent_for_phrase, get_phrases_for_intent, SOFT_PHRASE_CONFIDENCE_BOOST, SOFT_PHRASE_PARTIAL_CONFIDENCE


class IntentParser:
    """
    IntentParser v2 - Adaptive learning con fallback inteligente
    
    Features:
    - Carga patrones dinámicamente desde skills
    - Aprende de entidades (prioridad)
    - Fallback con keywords
    - Sistema de confianza
    """
    
    def __init__(self, skills_registry, debug=False):
        self.norm = Normalizer()
        self.skills = skills_registry
        self.debug = debug
        
        # Cargar patrones desde skills
        self.mapping = self._load_patterns(skills_registry)
        
        # Keywords de fallback (se expanden con uso)
        self.keyword_fallback = {
            "get_time": ["hora", "time", "reloj", "fecha", "date"],
            "open_app": ["abrir", "abre", "ejecuta", "inicia", "lanza", "open", "launch", "calculadora", "calculator"],
            "system_status": ["estado", "status", "info", "cpu", "memoria", "ram", "disco"],
            "create_note": ["nota", "anota", "escribe", "note", "write"],
            "search_file": ["busca", "encuentra", "search", "find", "donde esta"],
            "system_auto_optimization": ["optimizar", "optimize", "limpiar", "cleanup", "tune", "ajustar", "auto", "automatico"]
        }
        
        # Soft phrase mapping para frases conversacionales
        self.soft_phrase_maps = {
            "summarize_recent_activity": [
                "que estuve haciendo",
                "que hice ultimamente", 
                "resumir la sesion",
                "actividad reciente",
                "que ha pasado",
                "que hicimos",
                "recuerda lo que hice",
                "resumen de actividad"
            ],
            "summarize_last_session": [
                "resumir la sesion",
                "sesion actual",
                "ultima sesion",
                "resumen de sesion",
                "que paso en la sesion"
            ],
            "get_time": [
                "que hora es",
                "dime la hora",
                "hora actual"
            ],
            "system_status": [
                "como esta el sistema",
                "estado del pc",
                "info del sistema"
            ],
            "system_auto_optimization": [
                "optimiza el sistema",
                "limpia el pc",
                "ajusta los recursos",
                "optimizar automaticamente",
                "limpieza automatica",
                "tune up del sistema",
                "mejorar rendimiento",
                "optimizar pc",
                "limpiar archivos temporales",
                "defragmentar disco"
            ]
        }
        
        # Historial de intents (para aprendizaje)
        self.intent_history = []
    
    def _load_patterns(self, skills_registry):
        """Carga patrones declarados por cada skill"""
        patterns = {}
        
        for intent, SkillClass in skills_registry.items():
            skill_patterns = getattr(SkillClass, "patterns", None)
            
            if skill_patterns and isinstance(skill_patterns, list):
                patterns[intent] = skill_patterns
                if self.debug:
                    print(f"[PARSER] Loaded {len(skill_patterns)} patterns for {intent}")
        
        return patterns
    
    def _infer_from_entities(self, entities):
        """
        Inferencia por entidades (prioridad máxima).
        Las entidades son evidencia fuerte de intent.
        """
        if not entities:
            return None, 0.0
        
        # Reglas de inferencia con confianza
        if entities.get("app"):
            return "open_app", 0.95
        
        if entities.get("file") or entities.get("path"):
            return "search_file", 0.9
        
        if entities.get("time") or entities.get("date"):
            return "schedule", 0.85
        
        if entities.get("note_content"):
            return "create_note", 0.9
        
        if entities.get("number") and entities.get("duration"):
            return "reminder", 0.8
        
        return None, 0.0
    
    def _match_patterns(self, text):
        """Matchea contra patrones de skills"""
        for intent, patterns in self.mapping.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return intent, 0.9  # Alta confianza en patterns
        return None, 0.0
    
    def _fallback_keywords(self, text):
        """Fallback basado en keywords"""
        text_lower = text.lower()
        scores = {}
        
        for intent, keywords in self.keyword_fallback.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                scores[intent] = score
        
        if scores:
            best_intent = max(scores, key=scores.get)
            confidence = min(0.7, scores[best_intent] * 0.3)  # Max 0.7 para fallback
            return best_intent, confidence
        
        return None, 0.0
    
    def _soft_phrase_match(self, text):
        """Soft matching para frases conversacionales completas"""
        text_lower = text.lower().strip()
        
        # Use new soft_phrases database
        intent, confidence_boost, is_exact = get_intent_for_phrase(text_lower, self.norm)
        
        if intent:
            base_confidence = 0.85 if is_exact else 0.65
            final_confidence = min(0.95, base_confidence + confidence_boost)
            return intent, final_confidence
        
        # Fallback a soft_phrase_maps original
        for intent, phrases in self.soft_phrase_maps.items():
            for phrase in phrases:
                # Match exacto o contiene la frase
                if phrase.lower() in text_lower or text_lower == phrase.lower():
                    return intent, 0.8  # Alta confianza para frases exactas
        
        return None, 0.0
    
    def parse(self, text: str, entities: dict):
        """
        Pipeline principal con sistema de confianza.
        
        Returns:
            str: Intent detectado
        """
        intent, conf = self.parse_with_confidence(text, entities)
        return intent
    
    def parse_with_confidence(self, text: str, entities: dict) -> tuple:
        """
        Pipeline principal con sistema de confianza mejorado.
        
        Prioridad:
        1. Entidades (95%)
        2. Soft phrases exactas (80%)
        3. Patrones skill (90%)
        4. Keywords mejorado (70%)
        5. Unknown (0%)
        
        Returns:
            tuple: (intent: str, confidence: float)
        """
        t = self.norm.run(text)
        
        # 1. PRIORIDAD MÁXIMA: Entidades
        intent, conf = self._infer_from_entities(entities)
        if intent:
            self._log(f"Intent from entities: {intent} (conf: {conf:.2f})")
            self._record_intent(intent, conf, "entities")
            return intent, conf
        
        # 2. Soft phrase matching (antes de patrones)
        intent, conf = self._soft_phrase_match(t)
        if intent and conf >= 0.75:
            self._log(f"Intent from soft phrases: {intent} (conf: {conf:.2f})")
            self._record_intent(intent, conf, "soft_phrase")
            return intent, conf
        
        # 3. Patrones dinámicos por skill
        intent, conf = self._match_patterns(t)
        if intent:
            self._log(f"Intent from patterns: {intent} (conf: {conf:.2f})")
            self._record_intent(intent, conf, "patterns")
            return intent, conf
        
        # 4. Enhanced keyword fallback
        intent, conf = self._enhanced_keyword_fallback(t)
        if intent:
            self._log(f"Intent from keywords: {intent} (conf: {conf:.2f})")
            self._record_intent(intent, conf, "keywords")
            return intent, conf
        
        # 5. Unknown
        self._log(f"No intent detected for: '{text}'")
        self._record_intent("unknown", 0.0, "none")
        return "unknown", 0.0
    
    def parse_all_matches(self, text: str, entities: dict) -> List[Tuple[str, float, List[str]]]:
        """
        V0.0.3.1: Generate ALL possible intent matches (hypothesis generation).
        Returns list of (intent_name, score, matched_patterns).
        """
        t = self.norm.run(text)
        all_matches = []
        
        # 1. Check entity inference
        intent, conf = self._infer_from_entities(entities)
        if intent:
            all_matches.append((intent, conf, ["entity_inference"]))
        
        # 2. Check soft phrases
        intent, conf = self._soft_phrase_match(t)
        if intent and conf > 0:
            all_matches.append((intent, conf, ["soft_phrase_match"]))
        
        # 3. Check all pattern matches
        for intent_name, patterns in self.mapping.items():
            matched_patterns = []
            for pattern in patterns:
                if re.search(pattern, t, re.IGNORECASE):
                    matched_patterns.append(pattern)
            
            if matched_patterns:
                conf = 0.9  # Pattern match confidence
                all_matches.append((intent_name, conf, matched_patterns))
        
        # 4. Check keyword matches
        text_lower = t.lower()
        text_words = set(text_lower.split())
        
        for intent_name, keywords in self.keyword_fallback.items():
            matches = sum(1 for kw in keywords if kw in text_lower)
            exact_matches = sum(1 for kw in keywords if kw in text_words)
            score = matches + (exact_matches * 0.5)
            
            if score > 0:
                confidence = min(0.7, (score / len(keywords)) * 0.8)
                matched_kw = [kw for kw in keywords if kw in text_lower]
                all_matches.append((intent_name, confidence, matched_kw))
        
        # Sort by confidence
        all_matches.sort(key=lambda x: x[1], reverse=True)
        
        return all_matches
    
    def _enhanced_keyword_fallback(self, text):
        """Enhanced fallback with better scoring"""
        text_lower = text.lower()
        text_words = set(text_lower.split())
        scores = {}
        
        for intent, keywords in self.keyword_fallback.items():
            # Count occurrences
            matches = sum(1 for kw in keywords if kw in text_lower)
            
            # Count exact word matches
            exact_matches = sum(1 for kw in keywords if kw in text_words)
            
            # Combined score
            score = matches + (exact_matches * 0.5)
            
            if score > 0:
                confidence = min(0.7, (score / len(keywords)) * 0.8)
                scores[intent] = (confidence, score)
        
        if scores:
            best_intent, (conf, _) = max(scores.items(), key=lambda x: x[1][1])
            return best_intent, conf
        
        return None, 0.0
    
    def get_alternatives(self, text: str, entities: dict, top_n: int = 2) -> list:
        """
        Get alternative intent matches ranked by confidence.
        
        Args:
            text: Input text
            entities: Extracted entities
            top_n: Number of alternatives to return
            
        Returns:
            List of (intent, confidence) tuples
        """
        t = self.norm.run(text)
        candidates = []
        
        # Collect all possible matches with confidence
        intent, conf = self._infer_from_entities(entities)
        if intent:
            candidates.append((intent, conf, "entities"))
        
        intent, conf = self._match_patterns(t)
        if intent:
            candidates.append((intent, conf, "patterns"))
        
        intent, conf = self._fallback_keywords(t)
        if intent and conf > 0.3:
            candidates.append((intent, conf, "keywords"))
        
        intent, conf = self._soft_phrase_match(t)
        if intent:
            candidates.append((intent, conf, "soft_phrase"))
        
        # Sort by confidence descending and remove duplicates
        seen = set()
        unique_candidates = []
        for intent, conf, source in sorted(candidates, key=lambda x: x[1], reverse=True):
            if intent not in seen:
                unique_candidates.append((intent, conf))
                seen.add(intent)
        
        return unique_candidates[:top_n]
    
    def _record_intent(self, intent: str, confidence: float, source: str):
        """Registra intent para análisis posterior"""
        self.intent_history.append({
            "intent": intent,
            "confidence": confidence,
            "source": source
        })
        
        # Mantener solo últimos 100
        if len(self.intent_history) > 100:
            self.intent_history.pop(0)
    
    def add_keyword(self, intent: str, keyword: str):
        """Aprende un nuevo keyword para un intent"""
        if intent not in self.keyword_fallback:
            self.keyword_fallback[intent] = []
        
        if keyword.lower() not in self.keyword_fallback[intent]:
            self.keyword_fallback[intent].append(keyword.lower())
            if self.debug:
                print(f"[PARSER] Learned keyword '{keyword}' for {intent}")
    
    def get_stats(self):
        """Estadísticas del parser"""
        total = len(self.intent_history)
        if total == 0:
            return {"total": 0}
        
        by_source = {}
        by_intent = {}
        
        for record in self.intent_history:
            source = record["source"]
            intent = record["intent"]
            
            by_source[source] = by_source.get(source, 0) + 1
            by_intent[intent] = by_intent.get(intent, 0) + 1
        
        return {
            "total": total,
            "by_source": by_source,
            "by_intent": by_intent,
            "unknown_rate": by_intent.get("unknown", 0) / total
        }
    
    def _log(self, msg):
        if self.debug:
            print(f"[PARSER] {msg}")