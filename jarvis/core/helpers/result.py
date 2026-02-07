# core/helpers/result.py
"""
Result/Outcome Helper - FASE 1
Contrato uniforme para operaciones con success/failure explícito.

Principios:
- Toda operación retorna Result
- Success y Failure son explícitos, no booleanos
- Backward compatible con dict {attempted, success, error, data}
"""
from typing import Optional, Any, Dict
from dataclasses import dataclass, field


@dataclass
class Result:
    """
    Resultado de una operación con outcome explícito.
    
    Uso:
        # Success
        return Result.success(data={"app": "notepad"})
        
        # Failure
        return Result.failure(error="Archivo no encontrado")
        
        # Check
        if result.is_success():
            print(result.data)
    """
    attempted: bool
    success: bool
    error: Optional[str] = None
    data: Optional[Any] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def success(cls, data: Any = None, metadata: Dict = None) -> 'Result':
        """Crea un resultado exitoso"""
        return cls(
            attempted=True,
            success=True,
            error=None,
            data=data,
            metadata=metadata or {}
        )
    
    @classmethod
    def failure(cls, error: str, data: Any = None, metadata: Dict = None) -> 'Result':
        """Crea un resultado fallido con error explícito"""
        return cls(
            attempted=True,
            success=False,
            error=error,
            data=data,
            metadata=metadata or {}
        )
    
    @classmethod
    def not_attempted(cls, reason: str) -> 'Result':
        """Operación no intentada (precondición falló)"""
        return cls(
            attempted=False,
            success=False,
            error=reason,
            data=None,
            metadata={}
        )
    
    def is_success(self) -> bool:
        """Verifica si la operación fue exitosa"""
        return self.success
    
    def is_failure(self) -> bool:
        """Verifica si la operación falló"""
        return not self.success
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte a dict para backward compatibility.
        Compatible con el formato {attempted, success, error, data}
        """
        result = {
            "attempted": self.attempted,
            "success": self.success,
            "error": self.error,
            "data": self.data
        }
        if self.metadata:
            result["metadata"] = self.metadata
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Result':
        """
        Crea Result desde dict para backward compatibility.
        Permite trabajar con código legacy que retorna dicts.
        """
        return cls(
            attempted=data.get("attempted", True),
            success=data.get("success", False),
            error=data.get("error"),
            data=data.get("data"),
            metadata=data.get("metadata", {})
        )
    
    def __bool__(self) -> bool:
        """Permite usar Result en contextos booleanos (if result:)"""
        return self.success
    
    def __str__(self) -> str:
        """Representación legible"""
        status = "SUCCESS" if self.success else "FAILURE"
        if self.error:
            return f"Result[{status}: {self.error}]"
        return f"Result[{status}]"
    
    def __repr__(self) -> str:
        return f"Result(attempted={self.attempted}, success={self.success}, error={self.error!r})"


# Aliases para claridad semántica
Outcome = Result
Success = Result.success
Failure = Result.failure
