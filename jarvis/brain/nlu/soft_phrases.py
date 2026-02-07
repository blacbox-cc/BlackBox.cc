# brain/nlu/soft_phrases.py
"""
Soft Phrases Database for NLU Pipeline v0.0.4
Complete mapping of conversational phrases to intents for all 23 skills
"""

SOFT_PHRASES = {
    # ============================================================
    # SYSTEM SKILLS (Base)
    # ============================================================
    
    "social_greeting": [
        "hola",
        "hey",
        "hi",
        "buenas",
        "buenos dias",
        "buenas tardes",
        "buenas noches",
        "que tal",
        "como estas",
        "como va",
        "saludos",
        "gracias",
        "muchas gracias",
        "ok",
        "vale",
        "perfecto",
        "genial",
        "adios",
        "chau",
        "nos vemos",
        "hasta luego",
        "bye"
    ],
    
    "get_time": [
        "que hora es",
        "dime la hora",
        "hora actual",
        "me dices la hora",
        "cual es la hora",
        "la hora",
        "horario",
        "que hora tenemos",
        "me muestras la hora"
    ],
    
    "system_status": [
        "como esta el sistema",
        "estado del pc",
        "info del sistema",
        "usar el sistema",
        "dame el estado",
        "status del sistema",
        "como va el pc",
        "que tal va el rendimiento",
        "cpu memoria"
    ],
    
    "create_note": [
        "crea una nota",
        "anota esto",
        "escribir una nota",
        "guarda una nota",
        "nueva nota",
        "apunta",
        "crea un recordatorio",
        "nota rapida",
        "memo",
        "toma nota de esto"
    ],
    
    "get_weather": [
        "que tiempo hace",
        "clima",
        "temperatura",
        "meteoro",
        "pronostico",
        "lluvia",
        "soleado",
        "como esta el clima",
        "hay lluvia",
        "temperatura actual"
    ],
    
    # ============================================================
    # PRODUCTIVITY SKILLS
    # ============================================================
    
    "open_app": [
        "abre",
        "abrme",
        "ejecuta",
        "inicia",
        "lanza",
        "open",
        "launch",
        "run",
        "empieza",
        "para que se abra",
        "quiero que abras",
        "abre la aplicacion",
        "levanta",
        "enciende"
    ],
    
    "open_app_advanced": [
        "abre con parametros",
        "ejecuta en modo",
        "lanza la app con",
        "abre en fullscreen",
        "abre en ventana",
        "abre minimizada",
        "advanced open",
        "abre la app con configuracion"
    ],
    
    # ============================================================
    # RESEARCH SKILLS (Internet Search)
    # ============================================================
    
    "internet_search": [
        "busca en internet",
        "busca online",
        "que hay sobre",
        "buscame",
        "necesito saber sobre",
        "google",
        "buscalo en google",
        "buscame en internet",
        "que es",
        "como se hace",
        "donde puedo encontrar",
        "averigua",
        "investiga",
        "busca informacion sobre",
        "dame informacion de",
        "que sabes sobre"
    ],
    
    "github_search": [
        "busca en github",
        "github",
        "repositorio",
        "busca el repo",
        "encuentra el codigo",
        "encontra en github",
        "repositorio github",
        "codigo de github",
        "busca el proyecto",
        "github repo"
    ],
    
    "stackoverflow_search": [
        "busca en stackoverflow",
        "stackoverflow",
        "stack overflow",
        "que dicen en stackoverflow",
        "pregunta en stackoverflow",
        "error en stackoverflow",
        "busca la pregunta",
        "solucion en stack",
        "stack overflow solution"
    ],
    
    "search_file": [
        "busca archivo",
        "encuentra archivo",
        "donde esta el archivo",
        "localiza el archivo",
        "busca el fichero",
        "find file",
        "search for file",
        "donde estan mis archivos",
        "busca archivos"
    ],
    
    "summarize_recent_activity": [
        "que estuve haciendo",
        "que hice ultimamente",
        "resumir la actividad",
        "resumen de lo que hice",
        "actividad reciente",
        "que ha pasado",
        "que hicimos",
        "recuerda lo que hice",
        "resumen de sesion",
        "que he estado haciendo",
        "historial de actividad"
    ],
    
    # ============================================================
    # ANALYSIS SKILLS
    # ============================================================
    
    "analyze_session_value": [
        "que valor tiene esta sesion",
        "analiza la sesion",
        "cuanto tiempo pase aqui",
        "que he logrado",
        "productividad de la sesion",
        "valor de sesion",
        "analisis de sesion",
        "fue productiva",
        "evalua la sesion"
    ],
    
    "research_and_contextualize": [
        "dame contexto",
        "contextualiza esto",
        "que significa",
        "dame el contexto",
        "como se relaciona",
        "analiza el contexto",
        "busca contexto",
        "necesito contexto"
    ],
    
    "analyze_system_health": [
        "analiza la salud del sistema",
        "como esta el pc",
        "diagnostico del sistema",
        "salud del sistema",
        "problemas del sistema",
        "checkea el sistema",
        "health check",
        "diagnostico"
    ],
    
    "evaluate_user_session": [
        "evalua mi sesion",
        "como me va",
        "evaluacion de sesion",
        "como estuvo mi sesion",
        "resumen de sesion",
        "evaluacion",
        "que tal me fue"
    ],
    
    # ============================================================
    # AUTOMATION & LEARNING SKILLS
    # ============================================================
    
    "system_auto_optimization": [
        "optimiza el sistema",
        "limpia el pc",
        "ajusta los recursos",
        "optimizar automaticamente",
        "limpieza automatica",
        "tune up del sistema",
        "mejorar rendimiento",
        "optimizar pc",
        "limpiar archivos temporales",
        "defragmentar disco",
        "optimize system",
        "cleanup",
        "auto optimization",
        "limpia todo"
    ],
    
    "auto_programming": [
        "programa esto",
        "genera codigo",
        "auto codigo",
        "autoprogramacion",
        "escribe el codigo",
        "hazme el codigo",
        "ayudame a programar",
        "asistente de programacion",
        "ai programming"
    ],
    
    # ============================================================
    # INFO & REFLECTION SKILLS
    # ============================================================
    
    "what_do_you_know_about_me": [
        "que sabes de mi",
        "que me conoces",
        "dime que sabes",
        "cuanta informacion tienes de mi",
        "que informacion tienes",
        "dame un perfil",
        "quien soy segun tu",
        "que sabes sobre mi",
        "reflejo",
        "profile"
    ],
    
    "summarize_last_session": [
        "resumir la ultima sesion",
        "ultima sesion",
        "que paso la ultima sesion",
        "resumen anterior",
        "sesion pasada",
        "que hice la otra vez",
        "ultima vez que estuve aqui"
    ],
    
    # ============================================================
    # NEW SKILLS (v0.0.6)
    # ============================================================
    
    "skill_testing": [
        "prueba el skill",
        "test skill",
        "testea",
        "skill test",
        "que skills tengo",
        "lista de skills",
        "cuales son mis skills",
        "que puedo hacer",
        "ayuda",
        "manual",
        "help"
    ],
    
    "web_browser": [
        "abre el navegador",
        "ve a",
        "navega a",
        "visita",
        "web browser",
        "abre la pagina",
        "ve a google",
        "entra a",
        "abre chrome"
    ],
    
    "ai_chat": [
        "habla conmigo",
        "conversa",
        "charlemos",
        "chat",
        "conversa sobre",
        "hablame de",
        "que opinas",
        "dime tu opinion"
    ],
}

# Confidence boost for exact matches
SOFT_PHRASE_CONFIDENCE_BOOST = 0.15  # Add 15% confidence if exact match

# Confidence reduction for partial/fuzzy matches
SOFT_PHRASE_PARTIAL_CONFIDENCE = 0.10  # Partial match gets lower confidence


def get_phrases_for_intent(intent: str) -> list:
    """Get all soft phrases for an intent"""
    return SOFT_PHRASES.get(intent, [])


def get_intent_for_phrase(phrase: str, normalizer=None) -> tuple:
    """
    Find best intent match for a phrase
    Returns (intent, confidence_boost, is_exact_match)
    """
    if normalizer is None:
        from brain.nlu.normalizer import Normalizer
        normalizer = Normalizer()
    
    normalized_phrase = normalizer.run(phrase)
    
    # Check exact matches first
    for intent, phrases in SOFT_PHRASES.items():
        normalized_phrases = [normalizer.run(p) for p in phrases]
        
        if normalized_phrase in normalized_phrases:
            return intent, SOFT_PHRASE_CONFIDENCE_BOOST, True
    
    # Check partial matches
    for intent, phrases in SOFT_PHRASES.items():
        normalized_phrases = [normalizer.run(p) for p in phrases]
        
        # Check if phrase contains any soft phrase keyword
        for norm_phrase in normalized_phrases:
            if norm_phrase in normalized_phrase or normalized_phrase in norm_phrase:
                return intent, SOFT_PHRASE_PARTIAL_CONFIDENCE, False
    
    return None, 0.0, False


def get_all_intents() -> list:
    """Get list of all intents with soft phrases"""
    return list(SOFT_PHRASES.keys())


def get_intent_count() -> int:
    """Get total number of skills/intents"""
    return len(SOFT_PHRASES)


def get_phrase_count_for_intent(intent: str) -> int:
    """Get number of soft phrases for an intent"""
    return len(SOFT_PHRASES.get(intent, []))


def print_soft_phrases_summary():
    """Print summary of all soft phrases"""
    print("\n" + "="*70)
    print("SOFT PHRASES SUMMARY - v0.0.4 NLU PIPELINE")
    print("="*70)
    print(f"Total Skills: {get_intent_count()}\n")
    
    for intent in sorted(SOFT_PHRASES.keys()):
        phrases = SOFT_PHRASES[intent]
        print(f"✓ {intent:35} {len(phrases):>2} phrases")
        for phrase in phrases[:3]:
            print(f"    • {phrase}")
        if len(phrases) > 3:
            print(f"    ... +{len(phrases)-3} more")
    
    total_phrases = sum(len(p) for p in SOFT_PHRASES.values())
    print(f"\nTotal Phrases: {total_phrases}")
    print("="*70 + "\n")


if __name__ == "__main__":
    print_soft_phrases_summary()
