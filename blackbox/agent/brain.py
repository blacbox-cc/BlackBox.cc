
from typing import Any

def decide(state: Any) -> Any:
    # Este es el embrión de la IA. 
    # Por ahora, mapeo directo. Mañana, lógica de optimización.
    ctx = state.context.lower()
    
    if "abre" in ctx:
        app = ctx.replace("abre", "").strip()
        return {"type": "APP_OPEN", "params": {"app_name": app}}
    
    return {"type": "IDLE", "params": {}}

import random
from agent.ranking import get_best_action

def get_action_to_perform(epsilon=0.2):
    """
    Política Epsilon-Greedy:
    - Con probabilidad 'epsilon' (20%), explora algo al azar.
    - Con probabilidad '1-epsilon' (80%), elige la mejor acción según el ranking.
    """
    ranking = get_best_action() # Lee los logs
    
    # Si no hay datos suficientes, exploramos
    if not ranking or random.random() < epsilon:
        return random.choice(["IDLE", "SPAWN_DUMMY", "ADJUST_PRIORITY"])
    
    # Elegir la mejor según el score del ranking
    best_action = max(ranking, key=ranking.get)
    return best_action