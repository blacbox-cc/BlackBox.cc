import statistics

def calculate_score(telemetry: dict) -> float:
    """
    Calcula la salud del sistema. 
    A menor uso de recursos, mayor puntaje (más espacio para computar).
    """
    cpu = telemetry.get("cpu_percent", 100)
    ram = telemetry.get("memory_percent", 100)
    
    # Penalizamos el uso. El máximo castigo es -100.
    # El puntaje máximo posible es 0 (sistema vacío).
    score = - (cpu * 0.6 + ram * 0.4)
    return round(score, 2)

def get_window_score(history: list, size: int = 3) -> float:
    """Calcula el promedio de una ventana para reducir ruido."""
    if len(history) < size:
        return 0.0
    return round(statistics.mean(history[-size:]), 2)

def get_penalty(action: str) -> float:
    """Costo intrínseco de cada acción."""
    penalties = {
        "SIMULATE_LOAD": 15.0,  # Muy intrusiva
        "ADJUST_PRIORITY": 2.0, # Leve
        "IDLE": 0.0,            # Gratis
        "CHECK_CPU": 0.5        # Costo mínimo de cómputo
    }
    return penalties.get(action, 5.0)