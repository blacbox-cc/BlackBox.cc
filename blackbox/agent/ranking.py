import json
import statistics

def get_best_action(logs_path="logs/events.jsonl"):
    stats = {}
    try:
        with open(logs_path, "r") as f:
            for line in f:
                data = json.loads(line)
                # Ojo: tu JSON tiene la data dentro de "result"
                res = data.get("result", {})
                act = data.get("action")
                delta = res.get("delta_adjusted", 0)
                
                if act not in stats: stats[act] = []
                stats[act].append(delta)
    except FileNotFoundError: return {}

    ranking = {}
    for act, deltas in stats.items():
        # REGLA: Mínimo 3 muestras para ser confiable
        if len(deltas) >= 3:
            avg = statistics.mean(deltas)
            std = statistics.stdev(deltas) if len(deltas) > 1 else 0
            # Ranking robusto: Media castigada por varianza
            ranking[act] = avg - (std * 0.2)
            
    return ranking