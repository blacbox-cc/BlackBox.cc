# skills/system/open_app.py
import subprocess
import shutil
import os


class OpenAppSkill:
    """Abre aplicaciones del sistema con verificación honesta"""
    
    patterns = [
        r"\b(abr[ie]|abre|open|launch|lanza|ejecuta|inicia)\b.*\b(app|aplicaci[oó]n|programa)\b",
        r"\b(abr[ie]|abre|open|launch)\s+\w+",
    ]
    
    entity_hints = {
        "app_name": {"pattern": r"(?:abr[ie]|abre|open|launch|lanza|ejecuta|inicia)\s+(.+)"}
    }
    
    def run(self, entities, core):
        app_name = entities.get("app_name", entities.get("app"))
        
        if not app_name:
            return {
                "attempted": False,
                "success": False,
                "error": "No se especificó aplicación",
                "data": None
            }
        
        # Limpiar nombre
        app_name = str(app_name).strip().lower()
        
        # Mapeo común
        app_map = {
            "calculadora": "calc.exe",
            "calculator": "calc.exe",
            "notepad": "notepad.exe",
            "bloc": "notepad.exe",
            "chrome": "chrome.exe",
            "firefox": "firefox.exe",
            "edge": "msedge.exe",
            "explorer": "explorer.exe",
            "cmd": "cmd.exe",
            "powershell": "powershell.exe",
            "spotify": "spotify.exe",
            "vscode": "code.exe",
            "code": "code.exe"
        }
        
        exe_name = app_map.get(app_name, f"{app_name}.exe")
        
        # Verificar si existe ANTES de intentar
        exists = shutil.which(exe_name) is not None
        
        if not exists:
            return {
                "attempted": True,
                "success": False,
                "error": f"Ejecutable '{exe_name}' no encontrado en PATH",
                "data": {"app_requested": app_name, "exe_searched": exe_name}
            }
        
        # Intentar abrir
        try:
            subprocess.Popen([exe_name], 
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL,
                           start_new_session=True)
            
            return {
                "attempted": True,
                "success": True,
                "error": None,
                "data": {
                    "app_name": app_name,
                    "exe_name": exe_name,
                    "message": f"Abriendo {app_name}"
                }
            }
        except Exception as e:
            return {
                "attempted": True,
                "success": False,
                "error": f"Error al ejecutar '{exe_name}': {str(e)}",
                "data": {"app_name": app_name, "exe_name": exe_name}
            }
