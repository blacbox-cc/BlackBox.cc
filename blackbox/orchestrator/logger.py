import json
from datetime import datetime
from pathlib import Path

def log_event(state, action, result):
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    event = {
        "timestamp": datetime.now().isoformat(),
        "state": state.__dict__ if hasattr(state, '__dict__') else state,
        "action": action,
        "result": result
    }
    
    with open(log_dir / "events.jsonl", "a") as f:
        f.write(json.dumps(event) + "\n")