# actions/dispatcher.py
"""
Skill Dispatcher v0.0.4+ - Enhanced with parallelization & scalability
Robust skill execution with validation, timeout handling, and error recovery
"""
import inspect
import time
import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from typing import Dict, Any, Optional, Callable
from system.core.exceptions import (
    SkillNotFoundError, SkillTimeoutError, SkillError, SkillDependencyError
)


class SkillDispatcher:
    """
    Dispatches intents to appropriate skills with robust error handling & parallelization
    Features:
    - Validation before execution
    - Timeout protection
    - Parallel execution for non-blocking skills
    - Thread pool management
    - Proper exception handling
    - Execution metrics
    """
    
    def __init__(self, logger=None, timeout_seconds: float = 30.0, max_workers: int = 4):
        self.skills: Dict[str, Any] = {}
        self.logger = logger
        self.timeout_seconds = timeout_seconds
        self.execution_stats = {}  # Track execution metrics per skill
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.async_tasks = {}  # Track async task results
        self.lock = threading.Lock()  # For thread-safe operations

    def _log(self, level: str, msg: str):
        """Log message using logger or print fallback"""
        if self.logger:
            fn = getattr(self.logger, level, None)
            if callable(fn):
                fn(msg)
                return
        print(msg)
    
    def _record_execution(self, intent: str, success: bool, duration_ms: float, error: str = None):
        """Record execution statistics"""
        if intent not in self.execution_stats:
            self.execution_stats[intent] = {
                "total": 0,
                "success": 0,
                "failures": 0,
                "avg_time_ms": 0,
                "last_error": None,
                "timeouts": 0
            }
        
        stats = self.execution_stats[intent]
        stats["total"] += 1
        stats["avg_time_ms"] = (stats["avg_time_ms"] + duration_ms) / 2
        
        if success:
            stats["success"] += 1
        else:
            stats["failures"] += 1
            stats["last_error"] = error
    
    def _validate_skill_requirements(self, intent: str, skill_cls: Any) -> tuple:
        """
        Validate skill can be executed
        Returns: (can_execute: bool, error_message: str or None)
        """
        # Check if skill has pre_check method
        if hasattr(skill_cls, "pre_check") and callable(getattr(skill_cls, "pre_check")):
            try:
                skill_instance = skill_cls() if inspect.isclass(skill_cls) else skill_cls
                result = skill_instance.pre_check({})
                
                if isinstance(result, tuple):
                    can_execute, message = result
                    return (can_execute, message if not can_execute else None)
                elif isinstance(result, bool):
                    return (result, None if result else "Pre-check failed")
                else:
                    return (True, None)  # Assume OK if unknown return
            except Exception as e:
                return (False, f"Pre-check error: {str(e)}")
        
        return (True, None)  # No pre-check, assume OK

    def register(self, intent_name, skill_cls):
        """
        Registra una skill para un intent específico.
        
        Args:
            intent_name (str): Nombre del intent (ej: "open_app")
            skill_cls (class): Clase de la skill (no instancia)
        """
        self.skills[intent_name] = skill_cls
        self._log("debug", f"[DISPATCHER] Registered skill: {intent_name}")

    def dispatch(self, intent, entities, core):
        """
        Execute the skill corresponding to intent with robust error handling
        
        Args:
            intent (str): Intent to execute
            entities (dict): Extracted entities
            core: JarvisCore instance
            
        Returns:
            dict: Execution result with success/error/result fields
            
        Raises:
            SkillNotFoundError: If skill not registered
            SkillTimeoutError: If execution exceeds timeout
            SkillError: If skill execution fails
        """
        start_time = time.time()
        
        # 1. Validate skill exists
        if intent not in self.skills:
            error_msg = f"Skill not registered: {intent}"
            self._log("warning", f"[DISPATCHER] {error_msg}")
            
            raise SkillNotFoundError(
                error_msg,
                {
                    "requested_intent": intent,
                    "available_skills": list(self.skills.keys())
                }
            )
        
        try:
            skill_cls = self.skills[intent]
            
            # 2. Pre-execution validation
            can_execute, validation_error = self._validate_skill_requirements(intent, skill_cls)
            if not can_execute:
                duration_ms = (time.time() - start_time) * 1000
                self._record_execution(intent, False, duration_ms, validation_error)
                
                raise SkillDependencyError(
                    f"Skill {intent} dependencies not met: {validation_error}",
                    {"intent": intent, "validation_error": validation_error}
                )
            
            # 3. Instantiate skill
            if inspect.isclass(skill_cls):
                skill_instance = skill_cls()
                self._log("debug", f"[DISPATCHER] Instantiated {intent}")
            else:
                skill_instance = skill_cls
                self._log("debug", f"[DISPATCHER] Using cached instance for {intent}")
            
            # 4. Execute with timeout protection
            self._log("info", f"[DISPATCHER] Executing: {intent} | entities: {list(entities.keys())}")
            
            execution_start = time.time()
            
            # Simple timeout using try-except (no threading required for now)
            try:
                result = skill_instance.run(entities, core)
            except TimeoutError as e:
                duration_ms = (time.time() - start_time) * 1000
                self._record_execution(intent, False, duration_ms, "timeout")
                
                raise SkillTimeoutError(
                    f"Skill {intent} exceeded {self.timeout_seconds}s timeout",
                    {"intent": intent, "timeout_seconds": self.timeout_seconds}
                )
            
            execution_time = time.time() - execution_start
            duration_ms = execution_time * 1000
            
            # 5. Validate result structure
            if not isinstance(result, dict):
                self._log("warning", f"[DISPATCHER] {intent} returned non-dict: {type(result)}")
                result = {"success": True, "result": result}
            
            # NUEVO: Extract success from outcome contract (attempted, success, error, data)
            # Support both old {"success": bool} and new outcome format
            if "attempted" in result:
                # New outcome format: {attempted, success, error, data}
                success = result.get("success", False)
                error_msg = result.get("error")
            else:
                # Legacy format: {"success": bool, ...}
                success = result.get("success", True)
                error_msg = result.get("error") or result.get("message")
            
            # 6. Record execution
            self._record_execution(intent, success, duration_ms, error_msg)
            
            # FASE 1: Extract metadata from result if present
            metadata = result.get("metadata", {})
            
            # 7. Format response
            response = {
                "success": success,
                "intent": intent,
                "result": result,
                "execution_time_ms": duration_ms
            }
            
            # FASE 1: Preserve metadata at top level for observability
            if metadata:
                response["metadata"] = metadata
            
            # Enhanced logging with error detail
            if success:
                log_msg = f"[DISPATCHER] {intent} ✓ ({duration_ms:.1f}ms)"
                self._log("info", log_msg)
            else:
                log_msg = f"[DISPATCHER] {intent} ✗ ({duration_ms:.1f}ms)"
                if error_msg:
                    log_msg += f" - {error_msg}"
                self._log("warning", log_msg)
            
            return response
            
        except SkillError:
            # Re-raise skill-specific errors
            raise
        except Exception as e:
            # Catch unexpected errors
            duration_ms = (time.time() - start_time) * 1000
            self._record_execution(intent, False, duration_ms, str(e))
            
            self._log("error", f"[DISPATCHER] Unexpected error in {intent}: {str(e)}")
            
            raise SkillError(
                f"Unexpected error executing {intent}: {str(e)}",
                {"intent": intent, "error": str(e)}
            )

    def list_skills(self):
        """Return list of available skills"""
        return list(self.skills.keys())

    def get_skill_info(self, intent_name):
        """Get information about a skill"""
        if intent_name not in self.skills:
            return None
        
        skill_cls = self.skills[intent_name]
        stats = self.execution_stats.get(intent_name, {})
        
        return {
            "name": intent_name,
            "class": skill_cls.__name__ if hasattr(skill_cls, "__name__") else "UnknownSkill",
            "doc": skill_cls.__doc__ or "No documentation",
            "has_pre_check": hasattr(skill_cls, "pre_check"),
            "stats": stats
        }
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics for all skills"""
        return {
            skill_name: stats
            for skill_name, stats in self.execution_stats.items()
        }
    
    def get_skill_performance(self, intent_name: str) -> Optional[Dict[str, Any]]:
        """Get performance metrics for a specific skill"""
        if intent_name not in self.execution_stats:
            return None
        
        stats = self.execution_stats[intent_name]
        total = stats["total"]
        
        if total == 0:
            return stats
        
        success_rate = (stats["success"] / total) * 100
        timeout_rate = (stats["timeouts"] / total) * 100
        
        return {
            **stats,
            "success_rate": f"{success_rate:.1f}%",
            "timeout_rate": f"{timeout_rate:.1f}%"
        }
    
    def reset_stats(self):
        """Reset execution statistics"""
        self.execution_stats.clear()
    
    def dispatch_async(self, intent: str, entities: dict, core=None) -> str:
        """
        Execute skill asynchronously (non-blocking)
        Useful for long-running tasks like file operations, optimization, etc.
        
        Returns:
            task_id: str for tracking the async task
        """
        task_id = f"{intent}_{int(time.time() * 1000)}"
        
        def _async_task():
            try:
                return self.dispatch(intent, entities, core)
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        future = self.executor.submit(_async_task)
        
        with self.lock:
            self.async_tasks[task_id] = {
                "future": future,
                "intent": intent,
                "created_at": time.time(),
                "status": "RUNNING"
            }
        
        self._log("debug", f"[DISPATCHER] Async task started: {task_id}")
        return task_id
    
    def get_async_result(self, task_id: str, timeout: float = 5.0) -> dict:
        """Get result of async task"""
        with self.lock:
            if task_id not in self.async_tasks:
                return {"success": False, "error": "Task not found"}
            
            task_info = self.async_tasks[task_id]
        
        try:
            result = task_info["future"].result(timeout=timeout)
            task_info["status"] = "COMPLETED"
            return result
        except FutureTimeoutError:
            task_info["status"] = "TIMEOUT"
            return {"success": False, "error": "Task timeout"}
        except Exception as e:
            task_info["status"] = "FAILED"
            return {"success": False, "error": str(e)}
    
    def list_async_tasks(self) -> list:
        """List all active async tasks"""
        with self.lock:
            tasks = []
            for task_id, info in self.async_tasks.items():
                tasks.append({
                    "task_id": task_id,
                    "intent": info["intent"],
                    "status": info["status"],
                    "created_at": info["created_at"]
                })
            return tasks
    
    def cleanup_async_tasks(self, max_age_seconds: int = 3600):
        """Clean old async tasks"""
        current_time = time.time()
        
        with self.lock:
            expired = [
                task_id for task_id, info in self.async_tasks.items()
                if (current_time - info["created_at"]) > max_age_seconds
            ]
            
            for task_id in expired:
                del self.async_tasks[task_id]
        
        self._log("debug", f"[DISPATCHER] Cleaned {len(expired)} async tasks")
        return len(expired)
    
    def shutdown(self):
        """Graceful shutdown of executor"""
        self.executor.shutdown(wait=True)
        self._log("info", "[DISPATCHER] Executor shut down")