"""
FASE 6: Reflection Mínima

Objetivo:
- Auto-inspección del estado del sistema
- Capacidad de detectar inconsistencias
- Explicar cómo se tomó una decisión
- Reportar estado de componentes

Sin LLMs, sin abstracciones metafísicas: reflection = introspección de estructuras.

Helpers:
1. SystemHealth: Reporta estado de componentes (OK, WARNING, FAILED)
2. DecisionExplainer: Convierte Decision en explicación humana
3. StateSnapshot: Captura estado del sistema en un momento dado
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum


# ========== 1. SYSTEM HEALTH ==========

class ComponentStatus(Enum):
    """Estado de un componente"""
    OK = "ok"
    WARNING = "warning"
    FAILED = "failed"
    UNKNOWN = "unknown"


@dataclass
class ComponentHealth:
    """
    Reporte de salud de un componente del sistema.
    
    Attributes:
        name: Nombre del componente (ej: "NLU", "Dispatcher", "EventBus")
        status: Estado actual (OK, WARNING, FAILED, UNKNOWN)
        message: Mensaje descriptivo
        metrics: Métricas actuales (ej: {"uptime_ms": 5000, "errors": 0})
        last_check: Timestamp del último health check
    """
    name: str
    status: ComponentStatus
    message: str = ""
    metrics: Dict[str, Any] = field(default_factory=dict)
    last_check: datetime = field(default_factory=datetime.now)
    
    def is_healthy(self) -> bool:
        """Componente está operativo"""
        return self.status == ComponentStatus.OK
    
    def to_dict(self) -> dict:
        """Serializar a dict"""
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "metrics": self.metrics,
            "last_check": self.last_check.isoformat()
        }


class SystemHealth:
    """
    Agregador de salud de todos los componentes del sistema.
    
    Permite registrar componentes y reportar estado global.
    """
    
    def __init__(self):
        self.components: Dict[str, ComponentHealth] = {}
    
    def register(self, component: ComponentHealth):
        """Registrar/actualizar componente"""
        self.components[component.name] = component
    
    def get(self, name: str) -> Optional[ComponentHealth]:
        """Obtener salud de un componente"""
        return self.components.get(name)
    
    def is_system_healthy(self) -> bool:
        """Sistema está completamente operativo"""
        return all(c.is_healthy() for c in self.components.values())
    
    def get_failed_components(self) -> List[ComponentHealth]:
        """Componentes en FAILED"""
        return [c for c in self.components.values() if c.status == ComponentStatus.FAILED]
    
    def get_warnings(self) -> List[ComponentHealth]:
        """Componentes en WARNING"""
        return [c for c in self.components.values() if c.status == ComponentStatus.WARNING]
    
    def summary(self) -> dict:
        """Resumen global de salud"""
        total = len(self.components)
        ok = sum(1 for c in self.components.values() if c.status == ComponentStatus.OK)
        warnings = len(self.get_warnings())
        failed = len(self.get_failed_components())
        
        return {
            "total_components": total,
            "ok": ok,
            "warnings": warnings,
            "failed": failed,
            "system_healthy": self.is_system_healthy(),
            "components": {name: c.to_dict() for name, c in self.components.items()}
        }


# ========== 2. DECISION EXPLAINER ==========

class DecisionExplainer:
    """
    Convierte estructuras Decision en explicaciones humanas.
    
    Sin LLMs: usa templates y datos estructurados.
    """
    
    @staticmethod
    def explain(decision: Any) -> str:
        """
        Genera explicación legible de una Decision.
        
        Args:
            decision: Objeto Decision con reasoning, confidence, alternatives
        
        Returns:
            String explicativo en español
        """
        # Extraer datos del decision (adaptado a Decision FASE 2)
        # Decision FASE 2 usa: decision_type, chosen_candidate, all_candidates, reasoning
        
        chosen = getattr(decision, 'chosen_candidate', None)
        if chosen:
            intent = getattr(chosen, 'intent', 'unknown')
            confidence = getattr(chosen, 'confidence', 0.0)
        else:
            # Fallback para otras estructuras
            intent = getattr(decision, 'intent', 'unknown')
            confidence = getattr(decision, 'confidence', 0.0)
        
        reasoning = getattr(decision, 'reasoning', '')
        alternatives = getattr(decision, 'all_candidates', [])
        
        # Template base
        explanation = f"Elegí '{intent}' con confianza {confidence:.2f}.\n"
        
        # Agregar reasoning si existe
        if reasoning:
            explanation += f"Razonamiento: {reasoning}\n"
        
        # Agregar alternativas consideradas (excluir el elegido)
        if alternatives:
            other_alts = [alt for alt in alternatives if alt != chosen]
            if other_alts:
                alt_names = [alt.intent if hasattr(alt, 'intent') else str(alt) for alt in other_alts]
                explanation += f"Otras opciones consideradas: {', '.join(alt_names[:3])}"
                if len(alt_names) > 3:
                    explanation += f" (+{len(alt_names) - 3} más)"
        
        return explanation
    
    @staticmethod
    def explain_failure(error_context: Any) -> str:
        """
        Explica por qué falló una operación.
        
        Args:
            error_context: ErrorContext con type, message, suggestion
        
        Returns:
            Explicación legible
        """
        message = getattr(error_context, 'message', str(error_context))
        suggestion = getattr(error_context, 'suggestion', '')
        
        explanation = f"Falló: {message}"
        if suggestion:
            explanation += f"\nSugerencia: {suggestion}"
        
        return explanation


# ========== 3. STATE SNAPSHOT ==========

@dataclass
class StateSnapshot:
    """
    Captura del estado del sistema en un momento dado.
    
    Útil para debugging: qué estaba pasando cuando ocurrió X.
    
    Attributes:
        timestamp: Cuándo se tomó el snapshot
        command: Comando que estaba ejecutándose
        mode: Modo operacional activo
        intent: Intent detectado (si aplica)
        entities: Entities extraídas
        components: Estado de componentes
        metadata: Cualquier info adicional
    """
    timestamp: datetime = field(default_factory=datetime.now)
    command: str = ""
    mode: str = "UNKNOWN"
    intent: str = ""
    entities: Dict[str, Any] = field(default_factory=dict)
    components: Dict[str, str] = field(default_factory=dict)  # {component: status}
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Serializar para logging/storage"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "command": self.command,
            "mode": self.mode,
            "intent": self.intent,
            "entities": self.entities,
            "components": self.components,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_context(cls, context: Any, components: Dict[str, str]) -> "StateSnapshot":
        """
        Crear snapshot desde un SkillContext.
        
        Args:
            context: SkillContext u objeto similar
            components: {component_name: status}
        
        Returns:
            StateSnapshot con estado capturado
        """
        return cls(
            command=getattr(context, 'command', ''),
            mode=str(getattr(context, 'mode', 'UNKNOWN')),
            intent=getattr(context, 'intent', ''),
            entities=dict(getattr(context, 'entities', {})),
            components=components
        )


# ========== EXPORTS ==========

__all__ = [
    'ComponentStatus',
    'ComponentHealth',
    'SystemHealth',
    'DecisionExplainer',
    'StateSnapshot'
]
