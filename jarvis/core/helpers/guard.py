# core/helpers/guard.py
"""
Guard/Preconditions Helper - FASE 1
Validaciones explícitas antes de ejecutar operaciones.

Principios:
- Verificar condiciones ANTES de ejecutar
- Fallar rápido con mensajes claros
- Separar validación de lógica de negocio
"""
from typing import Callable, Optional, Any, List
from dataclasses import dataclass


@dataclass
class Precondition:
    """
    Una precondición que debe cumplirse antes de ejecutar.
    
    Atributos:
        name: Nombre descriptivo de la precondición
        check: Función que retorna True si se cumple
        error_message: Mensaje de error si no se cumple
    """
    name: str
    check: Callable[[], bool]
    error_message: str
    
    def validate(self) -> tuple[bool, Optional[str]]:
        """
        Valida la precondición.
        
        Returns:
            (is_valid, error_message)
        """
        try:
            if self.check():
                return (True, None)
            else:
                return (False, self.error_message)
        except Exception as e:
            return (False, f"{self.error_message} (check failed: {e})")


class Guard:
    """
    Sistema de guards para validar precondiciones antes de ejecutar.
    
    Uso:
        # En una skill
        guard = Guard()
        guard.require("app_specified", lambda: entities.get("app"), 
                     "No se especificó qué aplicación abrir")
        guard.require("valid_path", lambda: os.path.exists(path),
                     f"Ruta no existe: {path}")
        
        result = guard.check()
        if not result[0]:
            return Result.failure(result[1])
    """
    
    def __init__(self):
        self.preconditions: List[Precondition] = []
    
    def require(self, name: str, check: Callable[[], bool], error_message: str) -> 'Guard':
        """
        Agrega una precondición requerida.
        
        Args:
            name: Nombre de la precondición
            check: Función que retorna True si se cumple
            error_message: Mensaje si falla
            
        Returns:
            Self para encadenar (fluent interface)
        """
        self.preconditions.append(
            Precondition(name, check, error_message)
        )
        return self
    
    def require_not_none(self, name: str, value: Any, error_message: str) -> 'Guard':
        """Helper: Verificar que un valor no sea None"""
        return self.require(
            name,
            lambda: value is not None,
            error_message
        )
    
    def require_not_empty(self, name: str, value: Any, error_message: str) -> 'Guard':
        """Helper: Verificar que una colección no esté vacía"""
        return self.require(
            name,
            lambda: bool(value) if value is not None else False,
            error_message
        )
    
    def require_type(self, name: str, value: Any, expected_type: type, error_message: str) -> 'Guard':
        """Helper: Verificar tipo de valor"""
        return self.require(
            name,
            lambda: isinstance(value, expected_type),
            error_message
        )
    
    def check(self) -> tuple[bool, Optional[str]]:
        """
        Valida todas las precondiciones.
        
        Returns:
            (all_valid, first_error_message)
        """
        for precond in self.preconditions:
            is_valid, error = precond.validate()
            if not is_valid:
                return (False, error)
        return (True, None)
    
    def check_all(self) -> tuple[bool, List[str]]:
        """
        Valida todas las precondiciones y retorna TODOS los errores.
        
        Returns:
            (all_valid, list_of_errors)
        """
        errors = []
        for precond in self.preconditions:
            is_valid, error = precond.validate()
            if not is_valid:
                errors.append(error)
        return (len(errors) == 0, errors)
    
    def reset(self) -> 'Guard':
        """Limpia todas las precondiciones"""
        self.preconditions.clear()
        return self
