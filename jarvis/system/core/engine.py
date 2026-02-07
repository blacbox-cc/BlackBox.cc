# system/core/engine.py
import time
from typing import Optional

from core.lifecycle.runtime import RuntimeState, EventBus, Scheduler
from core.lifecycle.boot import Initializer, Diagnostics, ModuleLoader

from jarvis_io.text.input_adapter import CLIInput
from jarvis_io.text.output_adapter import TextOutput
from jarvis_io.cli.interface import AdvancedCLI
from jarvis_io.voice.tts import TTS
from jarvis_io.voice.stt import VoskSTT
from jarvis_io.voice_pipeline import VoiceIOPipeline
from brain.nlu.pipeline import NLUPipeline

from skills.system.logging.manager import JarvisLogger
from data.collector import DataCollector
from skills.actions.dispatcher import SkillDispatcher

# New: Error handling and validation
from .exceptions import BootError, JarvisException, ConfigError
from .decorators import handle_errors, validate_input, log_execution
from .validators import ConfigValidator, StateValidator
from skills.system.get_time import GetTimeSkill
from skills.system.system_status import SystemStatusSkill
from skills.productivity.create_note import CreateNoteSkill
from skills.research.search_file import SearchFileSkill
from skills.research.summarize_recent_activity import SummarizeRecentActivitySkill
from skills.analysis.analyze_session_value import AnalyzeSessionValueSkill
from skills.analysis.research_and_contextualize import ResearchAndContextualizeSkill
from skills.system.analyze_system_health import AnalyzeSystemHealthSkill
from skills.system.what_do_you_know_about_me import WhatDoYouKnowAboutMeSkill
from skills.analysis.evaluate_user_session import EvaluateUserSessionSkill
from skills.system.system_auto_optimization import SystemAutoOptimizationSkill
from skills.automation.auto_programming import AutoProgrammingSkill

# Web Dashboard (opcional)
try:
    from webapp.dashboard import JarvisDashboard
    DASHBOARD_AVAILABLE = True
except ImportError:
    DASHBOARD_AVAILABLE = False
    JarvisDashboard = None

from .handlers import EventHandlers
from .responses import ResponseFormatter
from .runtime_manager import RuntimeManager

from core.constants import (
    EVENT_NLU_INTENT, EVENT_INPUT_TEXT, EVENT_INPUT_VOICE, EVENT_JARVIS_RESPONSE
)

# New: Memory and LLM components
from brain.memory.storage import JarvisStorage
from brain.memory.context import ContextManager
from brain.memory.adaptive_learning import AdaptiveMemory
from brain.llm.manager import LLMManager
from brain.reflection_engine import ActiveLearningEngine

# New: Multi-session and operational modes
from system.session_manager import SessionManager
from core.modes import ModeController


class JarvisCore:
    """
    Jarvis Core v2 - Refinado para escalabilidad
    """
    @handle_errors(reraise=True)
    def __init__(self, config: dict):
        """
        Initialize JarvisCore with error handling
        
        Args:
            config: Configuration dictionary (will be validated)
            
        Raises:
            ConfigError: If configuration is invalid
            BootError: If critical components fail to initialize
        """
        # Validate configuration first
        try:
            self.config = ConfigValidator.validate(config)
        except Exception as e:
            raise ConfigError(f"Configuration validation failed: {e}", {"original_config": config})
        
        self.start_time = time.time()
        self.state = RuntimeState()
        
        # Component initialization tracking
        self._components_initialized = []
        self._components_failed = []
        
        # Sistema de logging profesional
        try:
            self.logger = JarvisLogger(self.config)
            self._components_initialized.append("logger")
        except Exception as e:
            raise BootError(f"Failed to initialize logger: {e}", {"component": "logger"})
        
        # Data collector (con consent del config)
        try:
            self.data_collector = DataCollector(
                consent=self.config.get("data_collection", False)
            )
            self._components_initialized.append("data_collector")
        except Exception as e:
            self.logger.logger.warning(f"Data collector initialization failed: {e}")
            self._components_failed.append(("data_collector", str(e)))
        
        # Runtime components
        try:
            self.events = EventBus(workers=self.config.get("workers", 4))
            self.scheduler = Scheduler()
            self.modules_loader = ModuleLoader(self)
            self._components_initialized.append("runtime")
        except Exception as e:
            raise BootError(f"Failed to initialize runtime: {e}", {"component": "runtime"})

        # New: Multi-session support
        try:
            self.session_manager = SessionManager()
            self.mode_controller = ModeController()
            self._components_initialized.append("session_management")
        except Exception as e:
            self.logger.logger.warning(f"Session management initialization failed: {e}")
            self._components_failed.append(("session_management", str(e)))

        # Output adapters
        try:
            self.output = TextOutput()
            self.cli = AdvancedCLI(use_colors=self.config.get("use_colors", True))
            self._components_initialized.append("output_adapters")
        except Exception as e:
            raise BootError(f"Failed to initialize output adapters: {e}", {"component": "output"})
        
        # Voice IO Pipeline (optional - non-blocking failure)
        try:
            self.voice_pipeline = VoiceIOPipeline(self.config)
            self._components_initialized.append("voice_pipeline")
        except Exception as e:
            self.logger.logger.warning(f"Voice pipeline initialization failed: {e}")
            self._components_failed.append(("voice_pipeline", str(e)))
        
        # Legacy TTS/STT (will be deprecated)
        try:
            self.tts = TTS(enabled=bool(self.config.get("tts", False)))
            self.stt = VoskSTT()
            self._components_initialized.append("legacy_voice")
        except Exception as e:
            self.logger.logger.warning(f"Legacy voice components failed: {e}")
            self._components_failed.append(("legacy_voice", str(e)))
        
        # New: Memory and LLM components
        try:
            self.storage = JarvisStorage()
            self.context_manager = ContextManager(self.storage)
            self.adaptive_memory = AdaptiveMemory(self.storage)
            self.llm_manager = LLMManager()
            self._components_initialized.append("memory_llm")
        except Exception as e:
            self.logger.logger.warning(f"Memory/LLM components failed: {e}")
            self._components_failed.append(("memory_llm", str(e)))

        # NLU Pipeline (temporal - será inicializado después)
        self.nlu = None

        # Active Learning Engine - Observes and learns from user patterns
        try:
            self.active_learning = ActiveLearningEngine(
                storage=self.storage,
                nlu_parser=self.nlu,
                logger=self.logger.logger
            )
            self._components_initialized.append("active_learning")
        except Exception as e:
            self.logger.logger.warning(f"Active learning engine failed: {e}")
            self._components_failed.append(("active_learning", str(e)))

        # Dispatcher de skills
        try:
            self.skill_dispatcher = SkillDispatcher(logger=self.logger.logger)
            self._register_skills()
            self._components_initialized.append("skill_dispatcher")
        except Exception as e:
            raise BootError(f"Failed to initialize skill dispatcher: {e}", {"component": "skill_dispatcher"})

        # NLU Pipeline - inicializar después de registrar skills
        try:
            self.nlu = NLUPipeline(
                self.skill_dispatcher.skills, 
                debug=self.config.get("debug_nlu", False),
                context_manager=self.context_manager,  # Pass context manager for awareness
                runtime_state=self.state  # NEW v0.0.3.1: Pass state for decision storage
            )
            self._components_initialized.append("nlu_pipeline")
        except Exception as e:
            self.logger.logger.warning(f"NLU pipeline initialization failed: {e}")
            self._components_failed.append(("nlu_pipeline", str(e)))
        
        # Log initialization status
        self.logger.logger.info(
            f"JarvisCore initialized: {len(self._components_initialized)} components OK, "
            f"{len(self._components_failed)} components failed"
        )
        
        if self._components_failed and self.config.get("debug", False):
            self.logger.logger.debug(f"Failed components: {self._components_failed}")

        # Actualizar active_learning con NLU
        self.active_learning.nlu_parser = self.nlu
        
        # Formateador de respuestas
        self.response_formatter = ResponseFormatter()
        
        # NEW v0.0.4: Reflection + Intent Validation + Background Tasks + Parallel Execution
        from brain.reflection_observer import SkillReflectionObserver
        from system.core.intent_validator import IntentValidator
        from system.core.background_tasks import BackgroundTaskManager
        from system.core.parallel_executor import ParallelExecutor
        
        self.reflection_observer = SkillReflectionObserver(self.storage, self.logger.logger)
        self.intent_validator = IntentValidator(self.cli, self.reflection_observer)
        self.background_tasks = BackgroundTaskManager(max_workers=4, logger=self.logger.logger)
        self.parallel_executor = ParallelExecutor(self.skill_dispatcher, self.logger.logger, timeout_seconds=3.0)
        
        # Handlers
        self.handlers = EventHandlers(self)
        
        # Runtime Manager - para debug y control
        self.runtime_manager = RuntimeManager(self)
        
        # Suscripciones a eventos (V0.0.3.1: Added cognitive events)
        self.events.subscribe(EVENT_NLU_INTENT, self.handlers.handle_skill_intent)
        self.events.subscribe(EVENT_INPUT_TEXT, self.handlers.handle_input_text)
        self.events.subscribe(EVENT_INPUT_VOICE, self.handlers.handle_input_voice)
        self.events.subscribe(EVENT_JARVIS_RESPONSE, self.handlers.handle_response)
        self.events.subscribe("nlu.intent", self.handlers.handle_nlu_trace)  # NLU trace for debug mode
        
        # V0.0.3.1: Subscribe to cognitive events
        self.events.subscribe("cognitive.decision_made", self._handle_decision_made)
        
        # Boot components
        self._initializer = Initializer(self)
        self._diagnostics = Diagnostics(self)
        
        # Historial de comandos (para patrones)
        self.command_history = []

        # Short-term memory (fase 1): últimas interacciones para contexto simple
        self.short_term_memory = []
        self.short_term_memory_max = int(config.get("short_term_memory_max", 20))
        
        self.logger.logger.info("JarvisCore v2 initialized")

    def _log(self, tag: str, msg: str):
        """Logging interno usado por módulos de boot (initializer/loader/diagnostics)."""
        try:
            self.logger.logger.info(f"[{tag}] {msg}")
        except Exception:
            print(f"[{tag}] {msg}")

    def _register_skills(self):
        """Registra todas las skills disponibles"""
        from skills.productivity.open_app import OpenAppSkill
        from skills.system.get_time import GetTimeSkill
        from skills.system.system_status import SystemStatusSkill
        from skills.productivity.create_note import CreateNoteSkill
        from skills.research.search_file import SearchFileSkill
        from skills.research.summarize_recent_activity import SummarizeRecentActivitySkill
        from skills.research.summarize_last_session import SummarizeLastSessionSkill
        from skills.analysis.analyze_session_value import AnalyzeSessionValueSkill
        from skills.analysis.research_and_contextualize import ResearchAndContextualizeSkill
        from skills.system.analyze_system_health import AnalyzeSystemHealthSkill
        from skills.system.what_do_you_know_about_me import WhatDoYouKnowAboutMeSkill
        from skills.analysis.evaluate_user_session import EvaluateUserSessionSkill
        from skills.learning.learning_engine import LearningEngineSkill
        from skills.research.research_skill import ResearchSkill
        from skills.learning.context_awareness import ContextAwarenessSkill
        from skills.system.manage_resources import ManageResourcesSkill
        # NEW v0.0.3.1: Safe greetings
        from skills.system.social_greeting import SocialGreetingSkill
        # NEW v0.0.6: Advanced features
        from skills.productivity.open_app_advanced import OpenAppAdvancedSkill
        from skills.research.internet_search import InternetSearchSkill, StackOverflowSearchSkill, GitHubSearchSkill
        from skills.system.skill_testing import SkillTestingSkill
        
        skills = {
            "open_app": OpenAppSkill,
            "get_time": GetTimeSkill,
            "system_status": SystemStatusSkill,
            "create_note": CreateNoteSkill,
            "search_file": SearchFileSkill,
            "summarize_recent_activity": SummarizeRecentActivitySkill,
            "summarize_last_session": SummarizeLastSessionSkill,
            "analyze_session_value": AnalyzeSessionValueSkill,
            "research_and_contextualize": ResearchAndContextualizeSkill(self.storage, self.llm_manager),
            "analyze_system_health": AnalyzeSystemHealthSkill(self.logger.logger),
            "what_do_you_know_about_me": WhatDoYouKnowAboutMeSkill(self.storage, self.active_learning),
            "evaluate_user_session": EvaluateUserSessionSkill(self.storage, self.active_learning),
            "auto_programming": AutoProgrammingSkill(self.storage, self.active_learning, self.logger.logger),
            "system_auto_optimization": SystemAutoOptimizationSkill(self.logger.logger),
            "learning_engine": LearningEngineSkill(),
            "research_skill": ResearchSkill(),
            "context_awareness": ContextAwarenessSkill(),
            "manage_resources": ManageResourcesSkill(),
            # NEW v0.0.3.1: Safe greetings
            "social_greeting": SocialGreetingSkill(),
            # NEW v0.0.6: Advanced skills
            "open_app_advanced": OpenAppAdvancedSkill(),
            "internet_search": InternetSearchSkill(),
            "stackoverflow_search": StackOverflowSearchSkill(),
            "github_search": GitHubSearchSkill(),
            "skill_testing": SkillTestingSkill()
        }
        
        for name, skill_cls in skills.items():
            # Check if it's a class (type) or already an instance
            if isinstance(skill_cls, type):
                # It's a class, needs instantiation
                try:
                    skill_instance = skill_cls()
                    self.skill_dispatcher.register(name, skill_instance)
                except Exception as e:
                    self.logger.logger.error(f"Failed to instantiate {name}: {e}")
            else:
                # Already an instance
                self.skill_dispatcher.register(name, skill_cls)
        
        self.logger.logger.info(f"Registered {len(skills)} skills")

    def boot(self):
        """Secuencia de arranque del sistema"""
        try:
            self.state.set("BOOTING")
            self.logger.logger.info("[BOOT] Starting boot sequence")
            
            # Iniciar componentes
            self.logger.logger.info("Starting EventBus...")
            self.events.start()
            
            self.logger.logger.info("Starting Scheduler...")
            self.scheduler.start()
            
            # NEW: Start Background Task Manager
            self.logger.logger.info("Starting Background Task Manager...")
            self.background_tasks.start()
            
            # Scheduler: Recolectar métricas cada 5 minutos
            if self.config.get("data_collection", False):
                self.scheduler.schedule_every(300, self.data_collector.collect_system_snapshot)
            
            self.logger.logger.info("Running initializers...")
            self._initializer.run()
            
            self.logger.logger.info("Loading modules...")
            self.modules_loader.load_all()

            # New: Initialize Voice IO Pipeline
            self.logger.logger.info("Initializing Voice IO Pipeline...")
            self.voice_pipeline.set_eventbus(self.events)
            if self.voice_pipeline.start():
                self.logger.logger.info("[VOICE] Voice IO Pipeline started")
            else:
                self.logger.logger.warning("[VOICE] Voice IO Pipeline not available, using CLI fallback")

            # Inicializar Input adapter
            self.logger.logger.info("Initializing Input adapter...")
            self.input = CLIInput(self.events, nlu_pipeline=self.nlu, logger=self.logger.logger, core=self)

            self.logger.logger.info("Running diagnostics...")
            self._diagnostics.run()
            
            # New: Create initial session
            self.logger.logger.info("Creating initial session...")
            self.current_session_id = self.session_manager.create_session()
            self.cli.set_session(self.current_session_id)
            self.logger.logger.info(f"[SESSION] Created session: {self.current_session_id}")
            
            self.state.set("READY")
            self.logger.logger.info("[BOOT] Boot completed - READY")
            
            # Legacy STT (deprecated - will be removed)
            if self.stt.is_available():
                self.stt.start()
                self.logger.logger.info("[STT] Legacy STT started (wake word: jarvis)")
            else:
                self.logger.logger.warning("[STT] Legacy STT not available")

            # Iniciar Dashboard Web si está habilitado
            if DASHBOARD_AVAILABLE and self.config.get("web_dashboard", False):
                self.logger.logger.info("Starting Web Dashboard...")
                self.dashboard = JarvisDashboard(self)
                dashboard_port = self.config.get("dashboard_port", 5000)
                if self.dashboard.start(port=dashboard_port):
                    self.logger.logger.info(f"[WEB] Dashboard started on port {dashboard_port}")
                else:
                    self.logger.logger.warning("[WEB] Failed to start dashboard")
            else:
                self.dashboard = None
                if self.config.get("web_dashboard", False):
                    self.logger.logger.warning("[WEB] Dashboard requested but not available (missing flask)")

            # Mostrar sugerencias si hay
            suggestions = self.data_collector.get_suggestions()
            
            return True
        except Exception as e:
            self.logger.log_error("BOOT_ERROR", str(e))
            self.state.set("DEAD")
            raise BootError(f"Boot sequence failed: {e}", {"component": "boot"})
    
    def _handle_decision_made(self, event):
        """
        V0.0.3.1: Handle decision_made event to store Decision in state.
        Called when NLU emits cognitive.decision_made event.
        """
        try:
            decision_data = event.get("data", {})
            # Recreate Decision from dict if needed
            # For now, NLU already stores it, this is just for redundancy
            if hasattr(self.nlu, '_last_decision'):
                decision = self.nlu._last_decision
                self.state.add_decision(decision)
        except Exception as e:
            self.logger.logger.debug(f"Failed to store decision: {e}")
            if suggestions:
                print("\n[INFO] Suggestions based on your usage:")
                for s in suggestions:
                    print(f"   {s}")
                print()
            
        except Exception as e:
            self.logger.log_error("BOOT_FAILED", str(e))
            self.logger.logger.critical(f"Boot failed: {e}")
            self.state.set("DEAD")
            raise
    
    def run(self):
        """Loop principal del sistema"""
        if not self.state.wait_ready(timeout=5.0):
            raise RuntimeError("Core not ready to run")
        
        self.state.set("RUNNING")
        self.logger.logger.info("[START] Main loop started")
        print("\n" + "="*60)
        print("JARVIS está listo. Escribe comandos (Ctrl+C para salir)")
        print("Datos guardados en: Desktop/JarvisData/")
        print("="*60 + "\n")
        
        try:
            while self.state.is_running():
                try:
                    self.input.poll()
                    time.sleep(0.01)
                except KeyboardInterrupt:
                    print("\n[SYSTEM] Interrupción detectada")
                    break
                except Exception as e:
                    self.logger.log_error("CORE_LOOP_ERROR", str(e))
                    if self.config.get("crash_on_error", False):
                        break
        finally:
            self.stop()
    
    def stop(self):
        """Apagado limpio del sistema"""
        cur = self.state.get()
        if cur in ("STOPPING", "DEAD"):
            return
        
        self.logger.logger.info("[SYSTEM] Shutting down...")
        self.state.set("STOPPING")
        
        try:
            # Guardar métricas finales
            self.logger.save_metrics()
            
            # Detener STT si está corriendo
            try:
                self.stt.stop()
            except Exception as e:
                self.logger.log_error("STT_STOP_ERR", str(e))
            
            # Stop background tasks
            try:
                self.background_tasks.stop()
            except Exception as e:
                self.logger.log_error("BACKGROUND_STOP_ERR", str(e))
            
            # Detener componentes
            try: 
                self.input.stop()
            except Exception as e: 
                self.logger.log_error("INPUT_STOP_ERR", str(e))
            
            try: 
                self.modules_loader.stop_all()
            except Exception as e: 
                self.logger.log_error("MODULES_STOP_ERR", str(e))
            
            try: 
                self.scheduler.stop()
            except Exception as e: 
                self.logger.log_error("SCHED_STOP_ERR", str(e))
            
            try: 
                self.events.stop()
            except Exception as e: 
                self.logger.log_error("EVENTS_STOP_ERR", str(e))
        
        finally:
            self.state.set("DEAD")
            self.logger.logger.info("[SYSTEM] Shutdown complete")
            print("\n[GOODBYE] Hasta luego!")
    
    def get_session_insights(self) -> dict:
        """Obtener insights de aprendizaje de la sesión actual usando active learning"""
        return self.active_learning.learn_from_session(self.start_time)
    
    def get_usage_stats(self) -> dict:
        """Obtener estadísticas generales de uso"""
        return self.active_learning.get_usage_stats()
    
    def reload_config(self, new_config: dict):
        """Hot-reload de configuración"""
        self.logger.logger.info("Reloading configuration...")
        self.config.update(new_config)
        
        # Recargar componentes que dependen de config
        if "debug_nlu" in new_config:
            self.nlu.debug = new_config["debug_nlu"]
        
        if "data_collection" in new_config:
            self.data_collector.consent = new_config["data_collection"]
        
        self.logger.logger.info("Configuration reloaded")
    
    # ========== v0.0.4 NEW METHODS ==========
    # These methods enable soft phrases, debug mode, PC monitoring, and background tasks
    
    def get_available_skills(self) -> list:
        """Get list of all available skills
        
        Returns:
            List of dicts with 'name', 'class', 'description'
        """
        try:
            skills_list = []
            
            # Get skills from dispatcher registry
            if hasattr(self, 'skill_dispatcher') and hasattr(self.skill_dispatcher, 'skills'):
                for skill_name, skill_instance in self.skill_dispatcher.skills.items():
                    skill_doc = skill_instance.__doc__ if hasattr(skill_instance, '__doc__') else f"Skill: {skill_name}"
                    skills_list.append({
                        'name': skill_name,
                        'class': skill_instance.__class__.__name__,
                        'description': skill_doc
                    })
            
            return sorted(skills_list, key=lambda x: x['name'])
            
        except Exception as e:
            self.logger.logger.error(f"Error getting available skills: {e}")
            return []
    
    def get_skill_info(self, skill_name: str) -> dict:
        """Get detailed info about a specific skill
        
        Args:
            skill_name: Name of the skill to look up
            
        Returns:
            Dict with skill info or None if not found
        """
        try:
            all_skills = self.get_available_skills()
            for skill in all_skills:
                if skill['name'].lower() == skill_name.lower():
                    return skill
            return None
        except Exception as e:
            self.logger.logger.error(f"Error getting skill info for {skill_name}: {e}")
            return None
    
    def get_system_status(self) -> dict:
        """Get current system status with comprehensive info
        
        Returns:
            Dict with CPU, memory, disk, processes, and Jarvis state
        """
        try:
            try:
                import psutil
                cpu_percent = psutil.cpu_percent(interval=0.1)
                memory_percent = psutil.virtual_memory().percent
                disk_percent = psutil.disk_usage('/').percent
                processes = len(psutil.pids())
            except:
                cpu_percent = 0
                memory_percent = 0
                disk_percent = 0
                processes = 0
            
            status = {
                'timestamp': __import__('datetime').datetime.now().isoformat(),
                'uptime_seconds': __import__('time').time() - self.start_time,
                'state': self.state.get() if hasattr(self, 'state') else 'UNKNOWN',
                'components_ok': len(self._components_initialized) if hasattr(self, '_components_initialized') else 0,
                'components_failed': len(self._components_failed) if hasattr(self, '_components_failed') else 0,
                'session_id': self.session_manager.current_session.id if hasattr(self, 'session_manager') and hasattr(self.session_manager, 'current_session') else None,
                'mode': str(self.mode_controller.current_mode) if hasattr(self, 'mode_controller') else 'UNKNOWN',
                'system': {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory_percent,
                    'disk_percent': disk_percent,
                    'processes': processes
                },
                'debug_mode': getattr(self, '_debug_mode', False)
            }
            return status
        except Exception as e:
            self.logger.logger.error(f"Error getting system status: {e}")
            return {'error': str(e)}
    
    def toggle_debug_mode(self) -> bool:
        """Toggle debug mode ON/OFF and return new state
        
        Returns:
            New debug mode state (True=ON, False=OFF)
        """
        try:
            current_debug = getattr(self, '_debug_mode', False)
            new_debug = not current_debug
            self._debug_mode = new_debug
            
            # Also update NLU if it supports debug
            if hasattr(self, 'nlu') and hasattr(self.nlu, 'debug'):
                self.nlu.debug = new_debug
            
            self.logger.logger.info(f"Debug mode: {'ON' if new_debug else 'OFF'}")
            return new_debug
            
        except Exception as e:
            self.logger.logger.error(f"Error toggling debug mode: {e}")
            return False
    
    def get_debug_status(self) -> bool:
        """Get current debug mode status
        
        Returns:
            True if debug mode is ON, False if OFF
        """
        return getattr(self, '_debug_mode', False)
    
    def init_v004_integration(self):
        """Initialize v0.0.4 integration after boot
        
        This method wires up all v0.0.4 components (soft phrases, PC monitoring, etc.)
        Should be called after boot() completes
        """
        try:
            from .v004_integration import integrate_v004_into_engine
            self.integration_layer = integrate_v004_into_engine(self)
            self.logger.logger.info("✓ v0.0.4 integration layer initialized")
        except Exception as e:
            self.logger.logger.warning(f"Could not initialize v0.0.4 integration: {e}")
            self.integration_layer = None
    
    def submit_background_task(self, task_id: str, task_name: str, function, args=None, kwargs=None, priority=0):
        """Submit a task to background task manager
        
        Args:
            task_id: Unique task identifier
            task_name: Human-readable task name
            function: Callable to execute
            args: Function positional arguments
            kwargs: Function keyword arguments
            priority: Task priority (0-9, higher=more important)
            
        Returns:
            Task ID if submitted to background, or result if executed synchronously
        """
        try:
            if hasattr(self, 'task_manager') and self.task_manager:
                return self.task_manager.submit_task(
                    task_id=task_id,
                    name=task_name,
                    function=function,
                    args=args or (),
                    kwargs=kwargs or {},
                    priority=priority
                )
            else:
                self.logger.logger.warning("BackgroundTaskManager not available, executing synchronously")
                return function(*(args or ()), **(kwargs or {}))
        except Exception as e:
            self.logger.logger.error(f"Error submitting background task: {e}")
            return None
    
    def get_background_tasks(self) -> list:
        """Get list of active background tasks
        
        Returns:
            List of active task information dicts
        """
        try:
            if hasattr(self, 'task_manager') and self.task_manager:
                return self.task_manager.get_all_tasks()
            return []
        except Exception as e:
            self.logger.logger.error(f"Error getting background tasks: {e}")
            return []
