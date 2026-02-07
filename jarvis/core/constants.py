# core/constants.py
"""Centralized constants for JarvisAI system"""

# System events
EVENT_JARVIS_RESPONSE = "jarvis.response"
EVENT_MEMORY_SHORT_TERM_UPDATED = "memory.short_term.updated"
EVENT_INPUT_TEXT = "input.text"
EVENT_INPUT_VOICE = "input.voice"
EVENT_NLU_ENTITIES_DETECTED = "nlu.entities.detected"
EVENT_NLU_INTENT = "nlu.intent"
EVENT_NLU_ERROR = "nlu.error"

# V0.0.3.1 Cognitive events
EVENT_OBSERVATION_CREATED = "cognitive.observation_created"
EVENT_INTERPRETATION_COMPLETED = "cognitive.interpretation_completed"
EVENT_DECISION_MADE = "cognitive.decision_made"
EVENT_ACTION_EXECUTED = "cognitive.action_executed"
EVENT_OUTCOME_RECORDED = "cognitive.outcome_recorded"

# Runtime states
STATE_BOOTING = "BOOTING"
STATE_READY = "READY"
STATE_RUNNING = "RUNNING"
STATE_STOPPING = "STOPPING"
STATE_DEAD = "DEAD"

# Default configuration
DEFAULT_CONFIG = {
    "name": "Jarvis",
    "version": "1.0",
    "workers": 4,
    "short_term_memory_max": 20,
    "data_collection": False,
    "tts": False,
    "debug_nlu": False,
    "crash_on_error": False
}
