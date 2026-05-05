import time
import statistics

from node.collector import DataCollector
from node.executor import execute_action
from orchestrator.logger import log_event

from agent.scoring import calculate_score, get_window_score, get_penalty
from agent.brain import get_action_to_perform


# =========================
# 1. OBSERVACIÓN
# =========================

def collect_window(collector, history, n=3, delay=0.5):
    samples = []

    for _ in range(n):
        snap = collector.collect_system_snapshot()
        score = calculate_score(snap)

        history.append(score)
        samples.append(score)

        time.sleep(delay)

    avg = statistics.mean(samples)
    std = statistics.stdev(samples) if len(samples) > 1 else 0

    return avg, std, samples


# =========================
# 2. DECISIÓN
# =========================

def decide_action(use_agent=True):
    if use_agent:
        return get_action_to_perform(epsilon=0.2)
    else:
        return input("\nAcción > ").upper()


# =========================
# 3. EJECUCIÓN
# =========================

def execute(action):
    try:
        return execute_action(action)
    except Exception as e:
        return {"success": False, "error": str(e)}


# =========================
# 4. EVALUACIÓN
# =========================

def evaluate(before_avg, after_avg, action):
    raw_delta = after_avg - before_avg
    penalty = get_penalty(action)
    delta_adjusted = raw_delta - penalty

    return raw_delta, penalty, delta_adjusted


# =========================
# 5. LOGGING
# =========================

def log_result(state_snapshot, action, before_avg, after_avg, raw_delta, penalty, delta_adjusted, std_before):
    log_event(state_snapshot, action, {
        "before_avg": round(before_avg, 2),
        "after_avg": round(after_avg, 2),
        "raw_delta": round(raw_delta, 2),
        "delta_adjusted": round(delta_adjusted, 2),
        "penalty": penalty,
        "std_before": round(std_before, 2),
        "is_stable": std_before < 5.0
    })


# =========================
# LOOP PRINCIPAL
# =========================

# Modificación en el LOOP PRINCIPAL de main.py

def run_loop(use_agent=True):
    collector = DataCollector(consent=True)
    scores_history = []
    iteration = 0  # <--- CONTADOR DE ITERACIONES

    print("\n" + "="*40)
    print("      BLACKBOX CORE v0.0.5 - ONLINE")
    print("="*40)

    while True:
        iteration += 1
        try:
            print(f"\n[ITERACIÓN #{iteration:03}]", end=" ", flush=True)
            
            # 1. BEFORE WINDOW
            print("Leyendo baseline...", end="", flush=True)
            before_avg, std_before, _ = collect_window(collector, scores_history)
            print(f" OK (Score: {before_avg})")

            # 2. DECISIÓN
            action = decide_action(use_agent)
            print(f"| Acción elegida: {action}")

            # 3. EJECUCIÓN
            print("| Ejecutando...", end="", flush=True)
            execute(action)
            print(" OK")

            # 4. AFTER WINDOW
            print("| Midiendo impacto...", end="", flush=True)
            after_avg, _, _ = collect_window(collector, scores_history)
            print(f" OK (Score: {after_avg})")

            # 5. EVALUACIÓN
            raw_delta, penalty, delta_adjusted = evaluate(before_avg, after_avg, action)

            # 6. LOGGING Y FEEDBACK VISUAL
            log_result({}, action, before_avg, after_avg, raw_delta, penalty, delta_adjusted, std_before)
            
            # Formateo de impacto para verlo rápido
            impacto = "✅ MEJORA" if delta_adjusted > 0 else "❌ EMPEORA"
            print(f"└─ RESULTADO: {impacto} | Δ Adj: {round(delta_adjusted, 2)} | Penalty: {penalty}")

            time.sleep(2)

        except KeyboardInterrupt:
            print(f"\n[SESIÓN FINALIZADA] Total iteraciones: {iteration}")
            break

# =========================
# ENTRYPOINT
# =========================

if __name__ == "__main__":
    run_loop(use_agent=True)  # True = autónomo, False = manual