import psutil
import time
import os
import psutil
import subprocess

def execute_action(action_type, params=None):
    try:
        if action_type == "SPAWN_DUMMY":
            # Crea un proceso que no hace nada pero ocupa lugar en la tabla
            subprocess.Popen(["python", "-c", "import time; time.sleep(10)"])
            return {"success": True}

        if action_type == "ADJUST_PRIORITY":
            # Baja la prioridad del proceso actual (o un dummy)
            p = psutil.Process(os.getpid())
            p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS if os.name == 'nt' else 10)
            return {"success": True}
        
        if action_type == "CHECK_CPU":
            return {"success": True, "val": psutil.cpu_percent()}
        
        if action_type == "SIMULATE_LOAD":
            # Genera carga artificial por 1 segundo
            start = time.time()
            while time.time() - start < 1:
                _ = 1000 * 1000 # Operación inútil de CPU
            return {"success": True, "msg": "Load simulated"}
            
        if action_type == "IDLE":
            return {"success": True, "val": 0}
        
        return {"success": False, "error": "Unknown"}
    except Exception as e:
        return {"success": False, "error": str(e)}
    
   