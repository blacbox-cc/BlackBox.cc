# system/core/responses.py
from typing import Any


class ResponseFormatter:
    """Formateador de respuestas de las skills, separado para escalabilidad"""
    def format(self, intent: str, dispatch_result: dict) -> str:
        if not intent:
            return "No recibí ninguna intención."

        if intent == "unknown":
            # TODO: obtener lista de skills desde dispatcher
            available = "open_app, get_time, system_status, create_note, search_file, social_greeting"
            return "No entendí el comando. Probá con: " + available

        # Check dispatcher-level failure first
        if not dispatch_result.get("success", True):
            err = dispatch_result.get("error") or "error desconocido"
            return f"❌ No pude ejecutar '{intent}': {err}"

        # Check skill outcome format
        payload = dispatch_result.get("result")
        
        # NEW: Handle outcome contract {attempted, success, error, data}
        if isinstance(payload, dict) and "attempted" in payload:
            if not payload.get("success", False):
                error_msg = payload.get("error", "sin detalles")
                return f"❌ No pude ejecutar '{intent}': {error_msg}"
            # Success - use data
            data = payload.get("data", {})
            
            # Format specific intents with data
            if intent == "open_app":
                app_name = data.get("app", "la aplicación")
                return f"✓ Abriendo {app_name}."
            elif intent == "get_time":
                return f"✓ Son las {data.get('time')} del {data.get('date')}."
            elif intent == "system_status":
                cpu = (data.get("cpu") or {}).get("percent")
                mem = (data.get("memory") or {}).get("percent")
                if cpu is not None and mem is not None:
                    return f"✓ Estado del sistema: CPU {cpu}% | RAM {mem}%."
                return "✓ Estado del sistema obtenido."
            elif intent == "create_note":
                return f"✓ Nota creada: {data.get('filename', 'ok')}."
            elif intent == "search_file":
                return f"✓ Búsqueda completada. Encontré {data.get('count', 0)} resultados."
            elif intent == "social_greeting":
                return data.get("message", "¡Hola!")
            else:
                return f"✓ Listo: {intent}."
        
        # Legacy format (backward compat)
        if isinstance(payload, dict) and payload.get("success") is False:
            err = payload.get("error") or "error desconocido"
            return f"❌ No pude ejecutar '{intent}': {err}"

        # Legacy success responses
        if intent == "open_app" and isinstance(payload, dict):
            return f"✓ Abriendo {payload.get('app', 'la aplicación')}."
        if intent == "get_time" and isinstance(payload, dict):
            return f"✓ Son las {payload.get('time')} del {payload.get('date')}."
        if intent == "system_status" and isinstance(payload, dict):
            cpu = (payload.get("cpu") or {}).get("percent")
            mem = (payload.get("memory") or {}).get("percent")
            if cpu is not None and mem is not None:
                return f"✓ Estado del sistema: CPU {cpu}% | RAM {mem}%."
            return "✓ Estado del sistema obtenido."
        if intent == "create_note" and isinstance(payload, dict):
            return f"✓ Nota creada: {payload.get('filename', 'ok')}."
        if intent == "search_file" and isinstance(payload, dict):
            return f"✓ Búsqueda completada. Encontré {payload.get('count', 0)} resultados."

        return f"✓ Listo: {intent}."
