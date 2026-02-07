"""
Proof-of-Concept: FASE 5 - Execution Wrapper

Demuestra el wrapper uniforme SkillExecutor sin dependencias de core.
Enfoque: Validar la capa de ejecución uniforme (trace, duration, status).
"""

from core.helpers import (
    SkillExecutor, ExecutionResult, ExecutionStatus,
    ExecutionPolicy, PolicyResult, Tracer
)
from dataclasses import dataclass, field
from typing import Dict, Any


# ========== CONTEXTO SIMPLIFICADO ==========

@dataclass
class SimpleContext:
    """Contexto mínimo para POC (sin depender de SkillContext completo)"""
    command: str
    entities: Dict[str, Any] = field(default_factory=dict)
    skill_name: str = "demo_skill"


# ========== MOCK SKILLS ==========

class WeatherSkill:
    """Skill de ejemplo: obtener clima"""
    def run(self, entities: dict, _system_state: dict):
        location = entities.get("location", "desconocida")
        return {
            "success": True,
            "temperature": 22,
            "conditions": "sunny",
            "location": location
        }


class SearchSkill:
    """Skill de ejemplo: búsqueda web"""
    def run(self, entities: dict, _system_state: dict):
        query = entities.get("query", "")
        if not query:
            return {
                "success": False,
                "error": "Query vacío"
            }
        return {
            "success": True,
            "results": [
                {"title": f"Resultado para: {query}", "url": "https://example.com"}
            ]
        }


class FileSkill:
    """Skill de ejemplo: operaciones de archivo"""
    def run(self, entities: dict, _system_state: dict):
        # Simula error de permiso
        raise PermissionError("No tienes permisos para acceder al archivo")


# ========== POLÍTICA PERSONALIZADA ==========

class QueryRequiredPolicy(ExecutionPolicy):
    """Política: Bloquea ejecución si no hay query en el contexto"""
    
    def should_execute(self, context: Any) -> PolicyResult:
        # Verificar que haya query en entities
        if not context.entities.get("query"):
            return PolicyResult(
                allowed=False,
                reason="Falta query requerido para ejecutar skill"
            )
        
        return PolicyResult(allowed=True)


# ========== DEMO ==========

def main():
    print("=" * 60)
    print("Proof-of-Concept: FASE 5 - Execution Wrapper")
    print("=" * 60)
    print()
    
    # ========== 1. EJECUCIÓN EXITOSA ==========
    print("📊 1. Ejecución exitosa con trace completo")
    print("-" * 60)
    
    executor = SkillExecutor()
    context = SimpleContext(
        command="¿Qué clima hay en Madrid?",
        entities={"location": "Madrid"},
        skill_name="WeatherSkill"
    )
    
    result = executor.execute(
        skill=WeatherSkill(),
        context=context,
        skill_name="WeatherSkill"
    )
    
    print(f"Status: {result.status.value}")
    print(f"Data: {result.data}")
    print(f"Duration: {result.duration_ms}ms")
    print(f"Trace events: {len(result.trace.get('events', []))}")
    print()
    
    # ========== 2. SKILL FAILURE ==========
    print("⚠️ 2. Skill failure (query vacío)")
    print("-" * 60)
    
    context = SimpleContext(
        command="buscar",
        entities={},  # query vacío → failure
        skill_name="SearchSkill"
    )
    
    result = executor.execute(
        skill=SearchSkill(),
        context=context,
        skill_name="SearchSkill"
    )
    
    print(f"Status: {result.status.value}")
    print(f"Error: {result.error}")
    print(f"Data: {result.data}")
    print()
    
    # ========== 3. EXCEPCIÓN CAPTURADA ==========
    print("💥 3. Excepción capturada y estructurada")
    print("-" * 60)
    
    context = SimpleContext(
        command="leer archivo secreto",
        entities={"path": "/root/secret.txt"},
        skill_name="FileSkill"
    )
    
    result = executor.execute(
        skill=FileSkill(),
        context=context,
        skill_name="FileSkill"
    )
    
    print(f"Status: {result.status.value}")
    print(f"Error: {result.error}")
    print(f"Metadata: {result.metadata}")
    print()
    
    # ========== 4. POLÍTICA DE EJECUCIÓN ==========
    print("🛡️ 4. Aplicación de política (bloqueo sin query)")
    print("-" * 60)
    
    executor_with_policy = SkillExecutor(policy=QueryRequiredPolicy())
    
    context = SimpleContext(
        command="buscar algo",
        entities={},  # Sin query → bloqueado
        skill_name="SearchSkill"
    )
    
    result = executor_with_policy.execute(
        skill=SearchSkill(),  # No se ejecutará
        context=context,
        skill_name="SearchSkill"
    )
    
    print(f"Status: {result.status.value}")
    print(f"Error: {result.error}")
    print(f"Policy reason: {result.metadata.get('policy_reason', 'N/A')}")
    print()
    
    # ========== 5. BACKWARD COMPATIBILITY ==========
    print("🔄 5. Formato legacy para dispatcher antiguo")
    print("-" * 60)
    
    context = SimpleContext(
        command="clima",
        entities={"location": "Barcelona"},
        skill_name="WeatherSkill"
    )
    
    result = executor.execute(
        skill=WeatherSkill(),
        context=context,
        skill_name="WeatherSkill"
    )
    
    legacy = result.to_legacy_dict()
    print(f"Legacy format: {legacy}")
    print()
    
    # ========== RESUMEN ==========
    print("=" * 60)
    print("✅ Proof-of-Concept completado")
    print("=" * 60)
    print()
    print("Validaciones exitosas:")
    print("  ✓ Ejecución uniforme con trace automático")
    print("  ✓ Manejo estructurado de failures y excepciones")
    print("  ✓ Aplicación de políticas pre-ejecución")
    print("  ✓ Metadata completo (duration, skill_name, policy)")
    print("  ✓ Backward compatibility con formato legacy")
    print()
    print("Beneficios observados:")
    print("  - Observabilidad: todos los eventos tienen trace")
    print("  - Debugging: errores estructurados con contexto")
    print("  - Seguridad: políticas aplicadas antes de ejecutar")
    print("  - Performance: duración de ejecución trackeada")
    print("  - Migración: formato legacy mantiene compatibilidad")


if __name__ == "__main__":
    main()
