"""
ExecutionPolicy: Reglas para cuándo ejecutar/no ejecutar skills.

Complementa DecisionPolicy: una vez elegido un intent, ExecutionPolicy
decide si es seguro ejecutarlo.

Objetivos:
- Safety: Validar precondiciones antes de ejecutar
- Observability: Logs muestran por qué se bloqueó ejecución
- Configurabilidad: Policies ajustables sin tocar skills

Uso:
    policy = SafeModePolicy()
    result = policy.should_execute(intent, context)
    
    if result.approved:
        execute_skill(intent, context)
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum


class ExecutionDecision(Enum):
    """Resultado de ExecutionPolicy."""
    ALLOW = "allow"              # Permitir ejecución
    BLOCK = "block"              # Bloquear ejecución
    REQUIRE_CONFIRMATION = "require_confirmation"  # Pedir confirmación


@dataclass(frozen=True)
class ExecutionPolicyResult:
    """
    Resultado de aplicar ExecutionPolicy.
    
    Atributos:
        decision: ALLOW, BLOCK, REQUIRE_CONFIRMATION
        reasoning: Por qué se tomó esta decisión
        metadata: Info adicional (riesgos detectados, etc)
    """
    decision: ExecutionDecision
    reasoning: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def approved(self) -> bool:
        """¿Policy permite ejecución?"""
        return self.decision == ExecutionDecision.ALLOW
    
    @property
    def blocked(self) -> bool:
        """¿Policy bloquea ejecución?"""
        return self.decision == ExecutionDecision.BLOCK
    
    @property
    def needs_confirmation(self) -> bool:
        """¿Policy requiere confirmación?"""
        return self.decision == ExecutionDecision.REQUIRE_CONFIRMATION
    
    def to_dict(self) -> Dict[str, Any]:
        """Conversión a dict para logs."""
        return {
            "decision": self.decision.value,
            "reasoning": self.reasoning,
            "metadata": self.metadata
        }
    
    def __repr__(self) -> str:
        return f"ExecutionPolicyResult({self.decision.value})"


class ExecutionPolicy:
    """Base class para execution policies."""
    
    def should_execute(self, intent: str, context: Dict[str, Any]) -> ExecutionPolicyResult:
        """
        Decide si ejecutar un intent.
        
        Args:
            intent: Intent a ejecutar
            context: Contexto (entities, user, session, etc)
        
        Returns:
            ExecutionPolicyResult con decisión
        """
        raise NotImplementedError("Subclasses must implement should_execute()")


class SafeModePolicy(ExecutionPolicy):
    """
    Policy: Bloquear intents peligrosos en modo seguro.
    
    Útil para testing, demos, o usuarios novatos.
    """
    
    def __init__(self, dangerous_intents: List[str] = None):
        """
        Args:
            dangerous_intents: Lista de intents considerados peligrosos.
                              Default: comandos de sistema, file operations, etc.
        """
        self.dangerous_intents = set(dangerous_intents or [
            "system_shutdown",
            "delete_file",
            "format_disk",
            "run_script",
            "modify_registry"
        ])
    
    def should_execute(self, intent: str, context: Dict[str, Any]) -> ExecutionPolicyResult:
        if intent in self.dangerous_intents:
            return ExecutionPolicyResult(
                decision=ExecutionDecision.BLOCK,
                reasoning=f"Intent '{intent}' bloqueado por SafeMode",
                metadata={
                    "intent": intent,
                    "dangerous_intents": list(self.dangerous_intents)
                }
            )
        
        return ExecutionPolicyResult(
            decision=ExecutionDecision.ALLOW,
            reasoning=f"Intent '{intent}' permitido en SafeMode",
            metadata={"intent": intent}
        )


class RateLimitPolicy(ExecutionPolicy):
    """
    Policy: Limitar frecuencia de ejecución por intent.
    
    Previene spam/abuse de comandos.
    """
    
    def __init__(self, max_per_minute: int = 10):
        """
        Args:
            max_per_minute: Máximo de ejecuciones por minuto por intent
        """
        self.max_per_minute = max_per_minute
        self.execution_counts: Dict[str, List[float]] = {}  # intent -> [timestamps]
    
    def should_execute(self, intent: str, context: Dict[str, Any]) -> ExecutionPolicyResult:
        import time
        now = time.time()
        
        # Inicializar contador para este intent
        if intent not in self.execution_counts:
            self.execution_counts[intent] = []
        
        # Limpiar timestamps antiguos (> 1 minuto)
        self.execution_counts[intent] = [
            ts for ts in self.execution_counts[intent]
            if now - ts < 60
        ]
        
        # Check rate limit
        count = len(self.execution_counts[intent])
        if count >= self.max_per_minute:
            return ExecutionPolicyResult(
                decision=ExecutionDecision.BLOCK,
                reasoning=f"Rate limit excedido: {count}/{self.max_per_minute} por minuto",
                metadata={
                    "intent": intent,
                    "count": count,
                    "limit": self.max_per_minute
                }
            )
        
        # Permitir y registrar
        self.execution_counts[intent].append(now)
        
        return ExecutionPolicyResult(
            decision=ExecutionDecision.ALLOW,
            reasoning=f"Dentro de rate limit: {count + 1}/{self.max_per_minute}",
            metadata={
                "intent": intent,
                "count": count + 1,
                "limit": self.max_per_minute
            }
        )


class ConfirmationPolicy(ExecutionPolicy):
    """
    Policy: Requiere confirmación para intents destructivos.
    
    Previene ejecución accidental de comandos peligrosos.
    """
    
    def __init__(self, require_confirmation_for: List[str] = None):
        """
        Args:
            require_confirmation_for: Lista de intents que requieren confirmación
        """
        self.require_confirmation_for = set(require_confirmation_for or [
            "delete_file",
            "system_shutdown",
            "clear_history",
            "factory_reset"
        ])
    
    def should_execute(self, intent: str, context: Dict[str, Any]) -> ExecutionPolicyResult:
        # Check si ya fue confirmado (en context)
        if context.get("user_confirmed", False):
            return ExecutionPolicyResult(
                decision=ExecutionDecision.ALLOW,
                reasoning=f"Usuario confirmó ejecución de '{intent}'",
                metadata={"intent": intent, "confirmed": True}
            )
        
        # Check si requiere confirmación
        if intent in self.require_confirmation_for:
            return ExecutionPolicyResult(
                decision=ExecutionDecision.REQUIRE_CONFIRMATION,
                reasoning=f"Intent '{intent}' requiere confirmación del usuario",
                metadata={
                    "intent": intent,
                    "requires_confirmation": True
                }
            )
        
        # No requiere confirmación
        return ExecutionPolicyResult(
            decision=ExecutionDecision.ALLOW,
            reasoning=f"Intent '{intent}' no requiere confirmación",
            metadata={"intent": intent}
        )


class PermissionPolicy(ExecutionPolicy):
    """
    Policy: Verificar permisos de usuario antes de ejecutar.
    
    Útil para multi-usuario o roles.
    """
    
    def __init__(self, permissions_map: Dict[str, List[str]] = None):
        """
        Args:
            permissions_map: Dict de {intent: [roles_permitidos]}
        """
        self.permissions_map = permissions_map or {
            "system_shutdown": ["admin"],
            "modify_registry": ["admin"],
            "install_software": ["admin", "power_user"],
            "delete_file": ["admin", "power_user", "user"],
            # Intents sin restricción se permiten a todos
        }
    
    def should_execute(self, intent: str, context: Dict[str, Any]) -> ExecutionPolicyResult:
        user_role = context.get("user_role", "user")
        
        # Si intent no está en map, permitir a todos
        if intent not in self.permissions_map:
            return ExecutionPolicyResult(
                decision=ExecutionDecision.ALLOW,
                reasoning=f"Intent '{intent}' sin restricción de permisos",
                metadata={"intent": intent, "user_role": user_role}
            )
        
        # Check permisos
        allowed_roles = self.permissions_map[intent]
        if user_role in allowed_roles:
            return ExecutionPolicyResult(
                decision=ExecutionDecision.ALLOW,
                reasoning=f"Usuario con rol '{user_role}' permitido para '{intent}'",
                metadata={
                    "intent": intent,
                    "user_role": user_role,
                    "allowed_roles": allowed_roles
                }
            )
        
        # Sin permisos
        return ExecutionPolicyResult(
            decision=ExecutionDecision.BLOCK,
            reasoning=f"Usuario con rol '{user_role}' no permitido para '{intent}'",
            metadata={
                "intent": intent,
                "user_role": user_role,
                "allowed_roles": allowed_roles
            }
        )


class ExecutionPolicyChain:
    """
    Aplica múltiples ExecutionPolicies en secuencia.
    
    Si una policy bloquea, se detiene la cadena.
    Si una policy pide confirmación, se detiene (o continúa si ya confirmado).
    
    Uso:
        chain = ExecutionPolicyChain([
            SafeModePolicy(),
            RateLimitPolicy(max_per_minute=5),
            ConfirmationPolicy()
        ])
        result = chain.should_execute(intent, context)
    """
    
    def __init__(self, policies: List[ExecutionPolicy]):
        self.policies = policies
    
    def should_execute(self, intent: str, context: Dict[str, Any]) -> ExecutionPolicyResult:
        """Aplica policies en orden hasta que una no-ALLOW."""
        for policy in self.policies:
            result = policy.should_execute(intent, context)
            
            # Si policy bloquea o pide confirmación, detener
            if result.decision != ExecutionDecision.ALLOW:
                result.metadata["stopped_at_policy"] = policy.__class__.__name__
                return result
        
        # Todas las policies permitieron
        return ExecutionPolicyResult(
            decision=ExecutionDecision.ALLOW,
            reasoning=f"Aprobado por {len(self.policies)} policies",
            metadata={"policies_passed": len(self.policies)}
        )
    
    def __repr__(self) -> str:
        return f"ExecutionPolicyChain({len(self.policies)} policies)"
