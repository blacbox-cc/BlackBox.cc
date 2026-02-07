"""
SkillContext: Contrato explícito de dependencias para skills.

En lugar de pasar (entities, core) por separado, encapsulamos todo en un objeto inmutable.

Objetivos:
- Reducir acoplamiento: Skills reciben 1 objeto en vez de N parámetros
- Preparar multi-threading: Context es snapshot inmutable
- Explícito: Se ve qué información tiene cada skill disponible
- Testeable: Fácil crear contextos mock

Uso:
    context = SkillContext(
        entities={"app_name": "chrome"},
        core=jarvis_core,
        command="abrir chrome"
    )
    skill.run(context)
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, List


@dataclass(frozen=True)
class SkillContext:
    """
    Contexto inmutable para ejecución de skills.
    
    Atributos:
        entities: Parámetros extraídos del comando (ej: {"app_name": "chrome"})
        core: Referencia a JarvisCore (para acceder servicios)
        command: Comando original del usuario
        history: Historial reciente de comandos (opcional)
        user_context: Información de sesión/preferencias (opcional)
        metadata: Cualquier metadata adicional (tracing, logging, etc)
    """
    entities: Dict[str, Any]
    core: Any  # JarvisCore, pero evitamos import circular
    command: str
    history: List[str] = field(default_factory=list)
    user_context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Acceso tipo dict para compatibilidad con código legacy.
        
        Legacy:
            entities = kwargs.get("entities", {})
        
        Nuevo:
            entities = context.get("entities", {})
        """
        if key == "entities":
            return self.entities
        elif key == "core":
            return self.core
        elif key == "command":
            return self.command
        elif key == "history":
            return self.history
        elif key == "user_context":
            return self.user_context
        elif key == "metadata":
            return self.metadata
        else:
            return default
    
    def get_entity(self, name: str, default: Any = None) -> Any:
        """Helper para acceder entities sin dict lookup."""
        return self.entities.get(name, default)
    
    def with_metadata(self, **kwargs) -> "SkillContext":
        """
        Retorna nuevo SkillContext con metadata adicional (inmutable).
        
        Útil para agregar tracing sin mutar el contexto original.
        """
        new_metadata = {**self.metadata, **kwargs}
        return SkillContext(
            entities=self.entities,
            core=self.core,
            command=self.command,
            history=self.history,
            user_context=self.user_context,
            metadata=new_metadata
        )
    
    @classmethod
    def from_legacy(cls, entities: Dict[str, Any], core: Any, command: str = "", **kwargs) -> "SkillContext":
        """
        Crea SkillContext desde firma legacy de skills.
        
        Legacy:
            skill.run(entities={"app": "chrome"}, system_state=core)
        
        Nuevo:
            context = SkillContext.from_legacy(entities, core)
            skill.run(context)
        """
        return cls(
            entities=entities,
            core=core,
            command=command,
            history=kwargs.get("history", []),
            user_context=kwargs.get("user_context", {}),
            metadata=kwargs.get("metadata", {})
        )
    
    def __repr__(self) -> str:
        return f"SkillContext(command='{self.command}', entities={list(self.entities.keys())})"
