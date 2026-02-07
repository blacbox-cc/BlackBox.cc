# actions/skills/get_time.py
"""
GetTime Skill - Refactored FASE 1 + FASE 2
Usa helpers: Result, Tracer, SkillContext
"""
from datetime import datetime
from core.helpers import Result, Tracer, SkillContext


class GetTimeSkill:
    """Devuelve la hora y fecha actual"""
    
    # Patrones para detección
    patterns = [
        r"\b(hora|time|que hora|qué hora)\b",
        r"\b(fecha|date|dia|día)\b",
        r"\b(reloj)\b"
    ]
    
    # Hints de entidades (opcional, para auto-registro)
    entity_hints = {
        "time_query": {"pattern": r"\b(hora|time)\b"}
    }
    
    def run(self, context_or_entities, core=None):
        """
        Retorna hora/fecha actual usando helpers FASE 1 + FASE 2.
        
        Acepta dos firmas para compatibilidad:
        - Nueva (FASE 2): run(context: SkillContext)
        - Legacy: run(entities: dict, core: Any)
        """
        # Normalizar entrada: soportar ambas firmas
        if isinstance(context_or_entities, SkillContext):
            context = context_or_entities
            entities = context.entities
        else:
            entities = context_or_entities
            context = SkillContext.from_legacy(
                entities=entities,
                core=core,
                command="get_time"
            )
        
        tracer = Tracer(command="get_time", enabled=True)
        tracer.step("skill_started")
        
        try:
            now = datetime.now()
            time_str = now.strftime("%H:%M:%S")
            date_str = now.strftime("%d/%m/%Y")
            day_name = now.strftime("%A")
            
            tracer.step("time_computed", data={
                "time": time_str,
                "date": date_str,
                "day": day_name
            })
            
            # FASE 1: Usar Result para success
            result = Result.success(
                data={
                    "time": time_str,
                    "date": date_str,
                    "day": day_name,
                    "timestamp": now.timestamp()
                },
                metadata={"trace": tracer.summary()}
            )
            
            return result.to_dict()
            
        except Exception as e:
            tracer.error("time_computation_failed", str(e))
            
            # Esto nunca debería pasar, pero por robustez
            result = Result.failure(
                error=str(e),
                metadata={"trace": tracer.summary()}
            )
            return result.to_dict()
