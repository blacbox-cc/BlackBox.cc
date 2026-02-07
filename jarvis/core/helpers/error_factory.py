# core/helpers/error_factory.py
"""
ErrorFactory - FASE 1
Errores semánticos estructurados en lugar de strings planos.

Principios:
- Errores con código + mensaje + contexto
- Clasificación por tipo (precondition, execution, validation)
- Serializables para logs
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class ErrorType(Enum):
    """Tipos de errores en el sistema"""
    PRECONDITION = "precondition"      # Fallo en validación previa
    EXECUTION = "execution"            # Fallo durante ejecución
    VALIDATION = "validation"          # Input inválido
    NOT_FOUND = "not_found"           # Recurso no encontrado
    PERMISSION = "permission"          # No autorizado
    TIMEOUT = "timeout"                # Timeout
    DEPENDENCY = "dependency"          # Dependencia externa falló
    INTERNAL = "internal"              # Error interno inesperado


@dataclass
class ErrorContext:
    """
    Contexto estructurado de un error.
    
    Atributos:
        error_type: Tipo de error (enum)
        code: Código único del error (ej: "APP_NOT_FOUND")
        message: Mensaje legible para usuario
        details: Detalles técnicos adicionales
        suggestion: Sugerencia de cómo resolver (opcional)
    """
    error_type: ErrorType
    code: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    suggestion: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa a dict para logs/eventos"""
        return {
            "error_type": self.error_type.value,
            "code": self.code,
            "message": self.message,
            "details": self.details,
            "suggestion": self.suggestion
        }
    
    def to_user_message(self) -> str:
        """Formatea mensaje para mostrar al usuario"""
        msg = self.message
        if self.suggestion:
            msg += f"\n💡 Sugerencia: {self.suggestion}"
        return msg
    
    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"


class ErrorFactory:
    """
    Factory para crear errores semánticos estructurados.
    
    Uso:
        # En lugar de:
        return {"error": "Aplicación no encontrada"}
        
        # Usar:
        error = ErrorFactory.app_not_found("spotify")
        return Result.failure(error.message, metadata={"error": error.to_dict()})
    """
    
    @staticmethod
    def precondition_failed(condition: str, details: Dict = None) -> ErrorContext:
        """Precondición no cumplida"""
        return ErrorContext(
            error_type=ErrorType.PRECONDITION,
            code="PRECONDITION_FAILED",
            message=f"Precondición no cumplida: {condition}",
            details=details or {},
            suggestion="Verificar que todos los parámetros requeridos estén presentes"
        )
    
    @staticmethod
    def app_not_found(app_name: str, searched_as: str = None) -> ErrorContext:
        """Aplicación no encontrada"""
        details = {"app_name": app_name}
        if searched_as:
            details["searched_as"] = searched_as
        
        return ErrorContext(
            error_type=ErrorType.NOT_FOUND,
            code="APP_NOT_FOUND",
            message=f"Ejecutable '{searched_as or app_name}' no encontrado en PATH",
            details=details,
            suggestion="Verificar que la aplicación esté instalada y en el PATH del sistema"
        )
    
    @staticmethod
    def file_not_found(file_path: str) -> ErrorContext:
        """Archivo no encontrado"""
        return ErrorContext(
            error_type=ErrorType.NOT_FOUND,
            code="FILE_NOT_FOUND",
            message=f"Archivo no encontrado: {file_path}",
            details={"file_path": file_path},
            suggestion="Verificar que la ruta sea correcta"
        )
    
    @staticmethod
    def invalid_input(field: str, reason: str) -> ErrorContext:
        """Input inválido"""
        return ErrorContext(
            error_type=ErrorType.VALIDATION,
            code="INVALID_INPUT",
            message=f"Input inválido en '{field}': {reason}",
            details={"field": field, "reason": reason}
        )
    
    @staticmethod
    def execution_failed(operation: str, cause: str) -> ErrorContext:
        """Fallo durante ejecución"""
        return ErrorContext(
            error_type=ErrorType.EXECUTION,
            code="EXECUTION_FAILED",
            message=f"Error al ejecutar '{operation}': {cause}",
            details={"operation": operation, "cause": cause}
        )
    
    @staticmethod
    def timeout(operation: str, timeout_seconds: float) -> ErrorContext:
        """Timeout en operación"""
        return ErrorContext(
            error_type=ErrorType.TIMEOUT,
            code="OPERATION_TIMEOUT",
            message=f"Timeout al ejecutar '{operation}' ({timeout_seconds}s)",
            details={"operation": operation, "timeout": timeout_seconds},
            suggestion="Intentar nuevamente o aumentar timeout"
        )
    
    @staticmethod
    def permission_denied(resource: str) -> ErrorContext:
        """Permiso denegado"""
        return ErrorContext(
            error_type=ErrorType.PERMISSION,
            code="PERMISSION_DENIED",
            message=f"No tienes permisos para acceder a: {resource}",
            details={"resource": resource},
            suggestion="Verificar permisos o ejecutar con privilegios elevados"
        )
    
    @staticmethod
    def dependency_unavailable(dependency: str, reason: str) -> ErrorContext:
        """Dependencia externa no disponible"""
        return ErrorContext(
            error_type=ErrorType.DEPENDENCY,
            code="DEPENDENCY_UNAVAILABLE",
            message=f"Dependencia no disponible: {dependency}",
            details={"dependency": dependency, "reason": reason},
            suggestion="Verificar que la dependencia esté instalada y funcionando"
        )
    
    @staticmethod
    def internal_error(details: str) -> ErrorContext:
        """Error interno inesperado"""
        return ErrorContext(
            error_type=ErrorType.INTERNAL,
            code="INTERNAL_ERROR",
            message="Error interno del sistema",
            details={"details": details},
            suggestion="Reportar este error al desarrollador"
        )
    
    @staticmethod
    def from_exception(exc: Exception, context: str = "") -> ErrorContext:
        """Crea ErrorContext desde una Exception"""
        return ErrorContext(
            error_type=ErrorType.INTERNAL,
            code="EXCEPTION",
            message=f"{context}: {str(exc)}" if context else str(exc),
            details={"exception_type": type(exc).__name__}
        )
