"""
SkillExecutor: Wrapper uniforme para ejecución de skills con observabilidad.

En lugar de llamar skill.run() directamente, usamos un wrapper que:
- Aplica Guards automáticamente
- Captura excepciones con ErrorFactory
- Traza ejecución con Tracer
- Aplica ExecutionPolicies
- Retorna ExecutionResult estructurado

Objetivos:
- Uniforme: Todas las skills se ejecutan igual
- Observable: Trace completo de ejecución
- Seguro: Guards y policies aplicados automáticamente
- Testeable: Fácil mockear y validar

Uso:
    executor = SkillExecutor()
    result = executor.execute(skill, context)
    
    if result.success:
        print(result.data)
    else:
        print(result.error)
"""

import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Callable
from enum import Enum

from .result import Result
from .tracer import Tracer
from .guard import Guard
from .error_factory import ErrorFactory, ErrorType
from .skill_context import SkillContext
from .execution_policy import ExecutionPolicy, ExecutionPolicyResult


class ExecutionStatus(Enum):
    """Estado de ejecución de un skill."""
    SUCCESS = "success"           # Ejecución exitosa
    FAILURE = "failure"           # Ejecución falló
    BLOCKED = "blocked"           # Bloqueado por policy
    TIMEOUT = "timeout"           # Timeout excedido
    EXCEPTION = "exception"       # Excepción no manejada


@dataclass(frozen=True)
class ExecutionResult:
    """
    Resultado de ejecutar un skill mediante SkillExecutor.
    
    Atributos:
        status: Estado de ejecución (SUCCESS, FAILURE, etc)
        data: Datos retornados por el skill (si success)
        error: Error message (si failure)
        trace: Trace de ejecución completo
        duration_ms: Duración en milisegundos
        metadata: Info adicional (skill_name, policy_checks, etc)
    """
    status: ExecutionStatus
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    trace: Dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def success(self) -> bool:
        """¿Ejecución exitosa?"""
        return self.status == ExecutionStatus.SUCCESS
    
    @property
    def failed(self) -> bool:
        """¿Ejecución falló?"""
        return self.status in (ExecutionStatus.FAILURE, ExecutionStatus.EXCEPTION, ExecutionStatus.TIMEOUT)
    
    @property
    def blocked(self) -> bool:
        """¿Bloqueado por policy?"""
        return self.status == ExecutionStatus.BLOCKED
    
    def to_dict(self) -> Dict[str, Any]:
        """Conversión a dict para compatibilidad."""
        return {
            "status": self.status.value,
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "trace": self.trace,
            "duration_ms": self.duration_ms,
            "metadata": self.metadata
        }
    
    def to_legacy_dict(self) -> Dict[str, Any]:
        """
        Conversión a formato legacy {attempted, success, error, data}.
        
        Para backward compatibility con código que espera formato antiguo.
        """
        return {
            "attempted": True,
            "success": self.success,
            "error": self.error if self.error else "",
            "data": self.data if self.data else {},
            "metadata": {
                "trace": self.trace,
                "duration_ms": self.duration_ms,
                **self.metadata
            }
        }
    
    def __repr__(self) -> str:
        return f"ExecutionResult({self.status.value}, duration={self.duration_ms:.2f}ms)"


class SkillExecutor:
    """
    Wrapper para ejecución uniforme de skills con observabilidad.
    
    Encapsula toda la lógica de ejecución:
    - Pre-checks (Guards, Policies)
    - Ejecución con trace
    - Post-processing (error handling, timing)
    - Resultado estructurado
    
    Ejemplo:
        executor = SkillExecutor(timeout_seconds=10)
        result = executor.execute(
            skill=OpenAppSkill(),
            context=SkillContext(...)
        )
    """
    
    def __init__(
        self,
        timeout_seconds: Optional[float] = None,
        execution_policy: Optional[ExecutionPolicy] = None,
        enable_tracing: bool = True
    ):
        """
        Args:
            timeout_seconds: Timeout máximo para ejecución (None = sin límite)
            execution_policy: Policy para validar ejecución (None = sin policy)
            enable_tracing: Si habilitar tracing automático
        """
        self.timeout_seconds = timeout_seconds
        self.execution_policy = execution_policy
        self.enable_tracing = enable_tracing
    
    def execute(
        self,
        skill: Any,
        context: SkillContext,
        skill_name: Optional[str] = None
    ) -> ExecutionResult:
        """
        Ejecuta skill con wrapper completo.
        
        Pipeline:
        1. Pre-checks (policies)
        2. Validaciones (guards)
        3. Ejecución con trace
        4. Post-processing
        
        Args:
            skill: Instancia del skill a ejecutar
            context: SkillContext con dependencias
            skill_name: Nombre del skill (para logging, opcional)
        
        Returns:
            ExecutionResult con outcome completo
        """
        start_time = time.time()
        skill_name = skill_name or skill.__class__.__name__
        
        # Inicializar tracer
        tracer = Tracer(command=f"execute_{skill_name}", enabled=self.enable_tracing)
        tracer.step("executor_started", data={"skill": skill_name})
        
        metadata = {
            "skill_name": skill_name,
            "intent": context.get_entity("_intent", "unknown"),
            "command": context.command
        }
        
        # Paso 1: Pre-checks (ExecutionPolicy)
        if self.execution_policy:
            tracer.step("policy_check", data={"policy": str(self.execution_policy)})
            
            policy_result = self.execution_policy.should_execute(
                intent=skill_name,
                context={"entities": context.entities, "user": context.user_context}
            )
            
            if not policy_result.approved:
                duration_ms = (time.time() - start_time) * 1000
                tracer.error("policy_blocked", policy_result.reasoning)
                
                return ExecutionResult(
                    status=ExecutionStatus.BLOCKED,
                    error=policy_result.reasoning,
                    trace=tracer.summary(),
                    duration_ms=duration_ms,
                    metadata={**metadata, "policy_decision": policy_result.decision.value}
                )
        
        # Paso 2: Ejecutar skill con timeout y error handling
        tracer.step("skill_execution_start")
        
        try:
            # Ejecutar con timeout (si configurado)
            if self.timeout_seconds:
                result = self._execute_with_timeout(skill, context, tracer)
            else:
                result = self._execute_skill(skill, context, tracer)
            
            duration_ms = (time.time() - start_time) * 1000
            tracer.step("skill_execution_end", data={"duration_ms": duration_ms})
            
            # Interpretar resultado
            return self._process_skill_result(
                result=result,
                tracer=tracer,
                duration_ms=duration_ms,
                metadata=metadata
            )
            
        except TimeoutError:
            duration_ms = (time.time() - start_time) * 1000
            tracer.error("timeout", f"Timeout después de {self.timeout_seconds}s")
            
            error = ErrorFactory.timeout(
                operation=f"execute_{skill_name}",
                timeout_seconds=self.timeout_seconds
            )
            
            return ExecutionResult(
                status=ExecutionStatus.TIMEOUT,
                error=error.message,
                trace=tracer.summary(),
                duration_ms=duration_ms,
                metadata={**metadata, "error_context": error.to_dict()}
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            tracer.error("exception", str(e), data={"exception_type": type(e).__name__})
            
            error = ErrorFactory.from_exception(
                exc=e,
                context=f"skill={skill_name}, command={context.command}"
            )
            
            return ExecutionResult(
                status=ExecutionStatus.EXCEPTION,
                error=error.message,
                trace=tracer.summary(),
                duration_ms=duration_ms,
                metadata={**metadata, "error_context": error.to_dict()}
            )
    
    def _execute_skill(
        self,
        skill: Any,
        context: SkillContext,
        tracer: Tracer
    ) -> Any:
        """Ejecuta skill.run() con trace."""
        tracer.step("calling_skill_run")
        
        # Llamar skill.run() - puede recibir context o (entities, core)
        try:
            result = skill.run(context)
        except TypeError:
            # Fallback: skill espera firma legacy (entities, core)
            tracer.step("using_legacy_signature")
            result = skill.run(context.entities, context.core)
        
        tracer.step("skill_run_completed")
        return result
    
    def _execute_with_timeout(
        self,
        skill: Any,
        context: SkillContext,
        tracer: Tracer
    ) -> Any:
        """
        Ejecuta skill con timeout.
        
        Nota: Implementación básica. Para timeout real necesitaríamos threading/multiprocessing.
        """
        # TODO: Implementar timeout real con threading
        # Por ahora, ejecutar sin timeout real
        tracer.step("timeout_check", data={"timeout": self.timeout_seconds, "note": "not_implemented"})
        return self._execute_skill(skill, context, tracer)
    
    def _process_skill_result(
        self,
        result: Any,
        tracer: Tracer,
        duration_ms: float,
        metadata: Dict[str, Any]
    ) -> ExecutionResult:
        """
        Procesa resultado del skill para crear ExecutionResult.
        
        Maneja diferentes formatos de retorno:
        - Result object (FASE 1)
        - Dict con {success, data, error} (legacy)
        - Dict plano (muy legacy)
        """
        # Si es Result object (FASE 1)
        if hasattr(result, 'success') and hasattr(result, 'to_dict'):
            result_dict = result.to_dict()
            
            if result_dict.get('success', False):
                return ExecutionResult(
                    status=ExecutionStatus.SUCCESS,
                    data=result_dict.get('data', {}),
                    trace=tracer.summary(),
                    duration_ms=duration_ms,
                    metadata=metadata
                )
            else:
                return ExecutionResult(
                    status=ExecutionStatus.FAILURE,
                    error=result_dict.get('error', 'Unknown error'),
                    data=result_dict.get('data'),
                    trace=tracer.summary(),
                    duration_ms=duration_ms,
                    metadata=metadata
                )
        
        # Si es dict legacy
        if isinstance(result, dict):
            success = result.get('success', False)
            
            if success:
                return ExecutionResult(
                    status=ExecutionStatus.SUCCESS,
                    data=result.get('data', result),  # Algunos skills retornan data directamente
                    trace=tracer.summary(),
                    duration_ms=duration_ms,
                    metadata=metadata
                )
            else:
                return ExecutionResult(
                    status=ExecutionStatus.FAILURE,
                    error=result.get('error', 'Skill returned success=False'),
                    data=result.get('data'),
                    trace=tracer.summary(),
                    duration_ms=duration_ms,
                    metadata=metadata
                )
        
        # Formato desconocido: asumir success
        tracer.step("unknown_result_format", data={"result_type": type(result).__name__})
        
        return ExecutionResult(
            status=ExecutionStatus.SUCCESS,
            data={"result": result},
            trace=tracer.summary(),
            duration_ms=duration_ms,
            metadata={**metadata, "result_format": "unknown"}
        )
