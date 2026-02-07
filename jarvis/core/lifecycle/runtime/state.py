# core/lifecycle/runtime/state.py
import threading
import time
from collections import deque


class RuntimeState:
    STATES = ("INIT", "BOOTING", "READY", "RUNNING", "STOPPING", "DEAD")

    def __init__(self):
        self._state = "INIT"
        self._cond = threading.Condition()
        # V0.0.3.1: Decision history for "why" command
        self.decision_history = deque(maxlen=20)
        self._decision_lock = threading.Lock()

    def set(self, value):
        if value not in self.STATES:
            raise ValueError(f"invalid state: {value}")
        with self._cond:
            self._state = value
            self._cond.notify_all()

    def get(self):
        with self._cond:
            return self._state

    def is_(self, value):
        return self.get() == value

    def wait_for(self, predicate, timeout=None):
        end = None if timeout is None else time.time() + timeout
        with self._cond:
            while not predicate():
                remaining = None if end is None else end - time.time()
                if remaining is not None and remaining <= 0:
                    return False
                self._cond.wait(timeout=remaining)
            return True

    # convenience
    def wait_ready(self, timeout=10.0):
        return self.wait_for(lambda: self._state == "READY", timeout=timeout)

    def is_running(self):
        return self.get() == "RUNNING"
    
    # V0.0.3.1: Decision management
    def add_decision(self, decision):
        """Store decision in history (thread-safe)"""
        with self._decision_lock:
            self.decision_history.append(decision)
    
    def get_last_decision(self):
        """Get most recent decision (thread-safe)"""
        with self._decision_lock:
            return self.decision_history[-1] if self.decision_history else None
    
    def get_decision_history(self, n=20):
        """Get last N decisions (thread-safe)"""
        with self._decision_lock:
            return list(self.decision_history)[-n:]
