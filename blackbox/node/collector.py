# system/data/collector.py
import psutil
import platform
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List


class DataCollector:
    """
    Recolector de datos del sistema con TRANSPARENCIA TOTAL.
    TODO en Desktop/JarvisData con README explicativo.
    """
    
    def __init__(self, consent: bool = True):
        self.consent = consent
        
        # Carpeta en Desktop
        self.data_dir = Path.home() / "Desktop" / "JarvisData"
        self.data_dir.mkdir(exist_ok=True)
        
        # Crear README de transparencia
        self._create_transparency_readme()
        
        # Archivos de datos
        self.app_usage_file = self.data_dir / "app_usage.json"
        self.system_metrics_file = self.data_dir / "system_metrics.json"
        self.patterns_file = self.data_dir / "usage_patterns.json"
        
        # Inicializar estructuras
        self._init_data_structures()
    
    def _create_transparency_readme(self):
        """Crea README explicando qué datos se recolectan"""
        readme_path = self.data_dir / "README.txt"
        
        readme_content = """
═══════════════════════════════════════════════════════════════
                    JARVIS - TRANSPARENCIA DE DATOS
═══════════════════════════════════════════════════════════════

🔒 PRIVACIDAD PRIMERO:
Todos los datos son LOCAL-ONLY. Nada se envía a servidores externos.
Puedes borrar esta carpeta en cualquier momento sin afectar a Jarvis.

📊 DATOS RECOLECTADOS:

1. app_usage.json
   - Apps que abriste via Jarvis
   - Frecuencia de uso
   - Última vez usada
   → Para: Sugerencias inteligentes ("¿quieres abrir Chrome otra vez?")

2. system_metrics.json
   - CPU, RAM, Disco (snapshots cada X minutos)
   - Apps corriendo en background
   → Para: Optimizar rendimiento, avisar cuando algo consume mucho

3. usage_patterns.json
   - Comandos que más usas
   - Horarios de uso
   - Workflows detectados
   → Para: Automatizaciones ("Siempre abres X después de Y")

4. commands_history.jsonl
   - Todos los comandos que le diste a Jarvis
   - Intents detectados
   - Éxito/fallo
   → Para: Mejorar NLU, entender qué funciona y qué no

5. skills_execution.jsonl
   - Skills ejecutadas
   - Tiempo de respuesta
   → Para: Optimización de performance

═══════════════════════════════════════════════════════════════

✅ TUS DERECHOS:

- Puedes BORRAR esta carpeta en cualquier momento
- Puedes EXPORTAR tus datos (comando: "jarvis exportar datos")
- Puedes DESACTIVAR recolección (config.json → data_collection: false)
- Jarvis sigue funcionando SIN estos datos (solo pierde features de IA)

═══════════════════════════════════════════════════════════════

🤝 MEJORAS FUTURAS (opcional, con tu permiso):

Si quieres ayudar a mejorar Jarvis para todos:
- Feedback anónimo de skills (rating ⭐)
- Reportes de bugs automáticos (anónimos)
- Sugerencias de nuevas features basadas en uso

→ Activar en config.json → anonymous_telemetry: true

═══════════════════════════════════════════════════════════════

Fecha de creación: {}
Versión de Jarvis: 1.0
        """.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        with open(readme_path, "w", encoding='utf-8') as f:
            f.write(readme_content)
    
    def _init_data_structures(self):
        """Inicializa archivos de datos si no existen"""
        if not self.app_usage_file.exists():
            with open(self.app_usage_file, "w") as f:
                json.dump({}, f)
        
        if not self.system_metrics_file.exists():
            with open(self.system_metrics_file, "w") as f:
                json.dump({"snapshots": []}, f)
        
        if not self.patterns_file.exists():
            with open(self.patterns_file, "w") as f:
                json.dump({"patterns": [], "automations": []}, f)
    
    def track_app_usage(self, app_name: str):
        """Registra uso de app"""
        if not self.consent:
            return
        
        with open(self.app_usage_file, "r+") as f:
            data = json.load(f)
            
            if app_name not in data:
                data[app_name] = {
                    "count": 0,
                    "first_used": datetime.now().isoformat(),
                    "last_used": None
                }
            
            data[app_name]["count"] += 1
            data[app_name]["last_used"] = datetime.now().isoformat()
            
            f.seek(0)
            json.dump(data, f, indent=2)
            f.truncate()
    
    def collect_system_snapshot(self):
        # SOLO devuelve el diccionario, NO escribe archivos.
        return {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent
        }
    
    def detect_pattern(self, commands: List[str]) -> Dict:
        """Detecta patrones de uso"""
        if not self.consent or len(commands) < 2:
            return {}
        
        # Análisis simple de secuencias
        patterns = {}
        for i in range(len(commands) - 1):
            pair = (commands[i], commands[i+1])
            patterns[pair] = patterns.get(pair, 0) + 1
        
        # Guardar si hay patrón significativo
        significant = {k: v for k, v in patterns.items() if v >= 3}
        
        if significant:
            with open(self.patterns_file, "r+") as f:
                data = json.load(f)
                data["patterns"].append({
                    "detected_at": datetime.now().isoformat(),
                    "sequences": {f"{k[0]} → {k[1]}": v for k, v in significant.items()}
                })
                
                f.seek(0)
                json.dump(data, f, indent=2)
                f.truncate()
        
        return significant
    
    def get_suggestions(self) -> List[str]:
        """Genera sugerencias basadas en patrones"""
        if not self.consent:
            return []
        
        suggestions = []
        
        # Top apps usadas
        try:
            with open(self.app_usage_file, "r") as f:
                apps = json.load(f)
                top_apps = sorted(apps.items(), key=lambda x: x[1]["count"], reverse=True)[:3]
                
                for app, data in top_apps:
                    suggestions.append(f"App frecuente: {app} (usado {data['count']} veces)")
        except:
            pass
        
        return suggestions