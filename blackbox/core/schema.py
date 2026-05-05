from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from datetime import datetime

@dataclass
class SystemState:
    """Lo que el sistema percibe en un instante T."""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    telemetry: Dict[str, Any] = field(default_factory=dict)
    context: str = ""  # Input del usuario o evento externo

@dataclass
class Action:
    """La orden que el Agente envía al Nodo."""
    type: str  # ej: "SYSTEM_OPTIMIZE", "APP_OPEN"
    params: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Result:
    """El reporte de ejecución del Nodo."""
    success: bool
    data: Optional[Dict] = None
    error: Optional[str] = None