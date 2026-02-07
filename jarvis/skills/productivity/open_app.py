# skills/productivity/open_app.py
"""
OpenApp Skill - Refactored FASE 1 + FASE 2
Usa helpers: Guard, Result, ErrorFactory, Tracer, SkillContext
"""
import subprocess
import platform
import shutil
from core.helpers import Guard, Result, ErrorFactory, Tracer, SkillContext


class OpenAppSkill:
    """Abre aplicaciones del sistema (v0.0.3.1 - outcome honesto + helpers)"""
    
    patterns = [
        r"\b(abr[ie]|open|ejecuta|launch|inicia|lanza)\b",
        r"\b(abr[ie]|open)\s+\w+",
    ]
    
    entity_hints = {
        "app": [
            "notepad", "calc", "chrome", "explorer", "cmd", "firefox", "edge",
            "brave", "vscode", "visual studio code", "code", "notas", "spotify",
            "teams", "telegram", "discord"
        ]
    }
    
    APP_ALIASES = {
        # Windows
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
        "calc": "calc.exe",
        "chrome": "chrome.exe",
        "edge": "msedge.exe",
        "explorer": "explorer.exe",
        "cmd": "cmd.exe",
        "terminal": "cmd.exe",
        "brave": "brave.exe",
        "vscode": "Code.exe",
        "visual studio code": "Code.exe",
        "code": "Code.exe",
        "notas": "notepad.exe",
        "spotify": "Spotify.exe",
        "teams": "Teams.exe",
        "telegram": "Telegram.exe",
        "discord": "Discord.exe",
        
        # Cross-platform
        "browser": "chrome.exe" if platform.system() == "Windows" else "firefox",
        "editor": "notepad.exe" if platform.system() == "Windows" else "gedit"
    }
    
    def run(self, context_or_entities, core=None):
        """
        Ejecuta skill con helpers FASE 1 + FASE 2.
        
        Acepta dos firmas para compatibilidad:
        - Nueva (FASE 2): run(context: SkillContext)
        - Legacy: run(entities: dict, core: Any)
        
        Retorna dict para backward compatibility.
        """
        # Normalizar entrada: soportar ambas firmas
        if isinstance(context_or_entities, SkillContext):
            # FASE 2: Nueva firma
            context = context_or_entities
            entities = context.entities
            core_ref = context.core
        else:
            # Legacy: entities dict + core separado
            entities = context_or_entities
            core_ref = core
            # Construir SkillContext internamente
            context = SkillContext.from_legacy(
                entities=entities,
                core=core_ref,
                command=f"open_app with {entities}"
            )
        
        # Inicializar tracer para observabilidad
        tracer = Tracer(command="open_app", enabled=True)
        tracer.step("skill_started", data={"entities": list(entities.keys())})
        
        # Extraer app name de entities
        app_name = None
        if entities.get("app"):
            app_name = entities["app"][0] if isinstance(entities["app"], list) else entities["app"]
        
        tracer.step("app_extracted", data={"app_name": app_name})
        
        # FASE 1: Usar Guard para precondiciones
        guard = Guard()
        guard.require_not_none("app_name", app_name, "No se especificó qué aplicación abrir")
        
        is_valid, error_msg = guard.check()
        if not is_valid:
            tracer.error("precondition_failed", error_msg)
            # FASE 1: Usar ErrorFactory
            error = ErrorFactory.precondition_failed("app_name", details={"entities": entities})
            result = Result.failure(error=error.message, metadata={"error_context": error.to_dict()})
            return result.to_dict()  # Backward compatible
        
        # Buscar alias
        executable = self.APP_ALIASES.get(app_name.lower(), app_name)
        tracer.step("alias_resolved", data={"executable": executable})
        
        # FASE 1: Usar Guard para verificar ejecutable existe
        exe_path = shutil.which(executable)
        if not exe_path and not executable.endswith(".exe"):
            exe_path = shutil.which(f"{executable}.exe")
        
        guard2 = Guard()
        guard2.require("exe_exists", lambda: exe_path is not None, 
                      f"Ejecutable '{executable}' no encontrado en PATH")
        
        is_valid2, error_msg2 = guard2.check()
        if not is_valid2:
            tracer.error("exe_not_found", error_msg2, data={"executable": executable})
            # FASE 1: Usar ErrorFactory para error semántico
            error = ErrorFactory.app_not_found(app_name, searched_as=executable)
            result = Result.failure(
                error=error.message,
                data={"app_name": app_name, "executable": executable},
                metadata={"error_context": error.to_dict()}
            )
            return result.to_dict()
        
        tracer.step("exe_found", data={"path": exe_path})
        
        # Ejecutar
        try:
            if platform.system() == "Windows":
                subprocess.Popen(exe_path, shell=False)
            elif platform.system() == "Darwin":  # macOS
                subprocess.Popen(["open", "-a", exe_path])
            else:  # Linux
                subprocess.Popen([exe_path])
            
            tracer.step("app_launched", data={"success": True})
            
            # FASE 1: Usar Result para success
            result = Result.success(
                data={
                    "app": app_name,
                    "executable": executable,
                    "path": exe_path
                },
                metadata={"trace": tracer.summary()}
            )
            return result.to_dict()
            
        except Exception as e:
            tracer.error("launch_failed", str(e), data={"exception_type": type(e).__name__})
            
            # FASE 1: Usar ErrorFactory para error de ejecución
            error = ErrorFactory.execution_failed("open_app", str(e))
            result = Result.failure(
                error=f"Error al abrir {app_name}: {str(e)}",
                data={"app_name": app_name, "executable": executable},
                metadata={
                    "error_context": error.to_dict(),
                    "trace": tracer.summary()
                }
            )
            return result.to_dict()
