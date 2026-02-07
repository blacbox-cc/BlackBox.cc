# skills/system/social_greeting.py


class SocialGreetingSkill:
    """Intent seguro para saludos y respuestas sociales básicas"""
    
    patterns = [
        r"^\s*(hola|hey|hi|hello|holis|ey|buenas)\s*$",
        r"^\s*(que tal|qué tal|como estas|cómo estás|how are you)\s*$",
        r"^\s*(gracias|thanks|thank you)\s*$",
        r"^\s*(adios|adiós|bye|chau|nos vemos)\s*$",
    ]
    
    def run(self, entities, core):
        # No ejecuta nada, solo responde
        return {
            "attempted": True,
            "success": True,
            "error": None,
            "data": {
                "message": "Hola! Estoy listo para ayudarte.",
                "type": "social_response"
            }
        }
