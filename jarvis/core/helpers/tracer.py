# core/helpers/tracer.py
"""
Tracer - FASE 1
Traza estructurada por comando para debugging y observabilidad.

Principios:
- Una traza por comando/operación
- Eventos con timestamp y metadata
- Formato estructurado para logs
- No afecta performance en producción
"""
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class TraceEntry:
    """
    Una entrada individual en la traza.
    
    Atributos:
        step: Nombre del paso (ej: "nlu_normalization", "skill_dispatch")
        timestamp: Timestamp del evento
        duration_ms: Duración en milisegundos (opcional)
        data: Datos adicionales del paso
        level: Nivel de detalle (debug, info, warning, error)
    """
    step: str
    timestamp: float
    duration_ms: Optional[float] = None
    data: Dict[str, Any] = field(default_factory=dict)
    level: str = "info"
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa a dict para logs"""
        return {
            "step": self.step,
            "timestamp": self.timestamp,
            "duration_ms": self.duration_ms,
            "data": self.data,
            "level": self.level
        }
    
    def __str__(self) -> str:
        duration = f" ({self.duration_ms:.1f}ms)" if self.duration_ms else ""
        return f"[{self.step}]{duration} {self.data if self.data else ''}"


class Tracer:
    """
    Tracer para seguir ejecución de comandos con timing y metadata.
    
    Uso:
        tracer = Tracer(command="abre notepad")
        
        tracer.step("nlu_started")
        # ... hacer NLU ...
        tracer.step("nlu_completed", data={"intent": "open_app"})
        
        tracer.step("skill_dispatch", data={"skill": "open_app"})
        # ... ejecutar skill ...
        tracer.step("skill_completed", data={"success": True})
        
        # Al final
        summary = tracer.summary()
        logger.info(summary)
    """
    
    def __init__(self, command: str = "", enabled: bool = True):
        self.command = command
        self.enabled = enabled
        self.entries: List[TraceEntry] = []
        self.start_time = time.time()
        self._last_step_time = self.start_time
    
    def step(self, step_name: str, data: Dict[str, Any] = None, level: str = "info") -> 'Tracer':
        """
        Registra un paso en la traza.
        
        Args:
            step_name: Nombre del paso
            data: Metadata adicional
            level: Nivel de log (debug, info, warning, error)
            
        Returns:
            Self para encadenar
        """
        if not self.enabled:
            return self
        
        now = time.time()
        duration_ms = (now - self._last_step_time) * 1000
        
        entry = TraceEntry(
            step=step_name,
            timestamp=now,
            duration_ms=duration_ms if len(self.entries) > 0 else 0,
            data=data or {},
            level=level
        )
        
        self.entries.append(entry)
        self._last_step_time = now
        
        return self
    
    def error(self, step_name: str, error: str, data: Dict[str, Any] = None) -> 'Tracer':
        """Registra un paso con error"""
        error_data = {"error": error}
        if data:
            error_data.update(data)
        return self.step(step_name, data=error_data, level="error")
    
    def get_total_duration_ms(self) -> float:
        """Retorna duración total desde el inicio"""
        return (time.time() - self.start_time) * 1000
    
    def get_entries(self) -> List[TraceEntry]:
        """Retorna todas las entradas de la traza"""
        return self.entries.copy()
    
    def summary(self) -> Dict[str, Any]:
        """
        Genera resumen estructurado de la traza.
        
        Returns:
            Dict con comando, duración total, pasos, errores
        """
        total_duration = self.get_total_duration_ms()
        error_steps = [e for e in self.entries if e.level == "error"]
        
        return {
            "command": self.command,
            "total_duration_ms": round(total_duration, 2),
            "steps_count": len(self.entries),
            "steps": [e.to_dict() for e in self.entries],
            "has_errors": len(error_steps) > 0,
            "error_steps": [e.to_dict() for e in error_steps]
        }
    
    def to_log_string(self) -> str:
        """
        Formatea la traza para logs legibles.
        
        Returns:
            String multi-línea con la traza formateada
        """
        lines = [f"TRACE: {self.command}"]
        
        for i, entry in enumerate(self.entries, 1):
            duration = f" [{entry.duration_ms:.1f}ms]" if entry.duration_ms else ""
            level_prefix = "❌" if entry.level == "error" else "  "
            lines.append(f"{level_prefix} {i}. {entry.step}{duration}")
            
            if entry.data:
                for key, value in entry.data.items():
                    lines.append(f"      {key}: {value}")
        
        total = self.get_total_duration_ms()
        lines.append(f"  Total: {total:.1f}ms")
        
        return "\n".join(lines)
    
    def clear(self) -> 'Tracer':
        """Limpia la traza y reinicia timer"""
        self.entries.clear()
        self.start_time = time.time()
        self._last_step_time = self.start_time
        return self
