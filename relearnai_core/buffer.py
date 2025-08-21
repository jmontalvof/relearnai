import os, json, time
from collections import defaultdict

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "pattern_buffer.json")
os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)

class PatternBuffer:
    def __init__(self, trigger_count: int = 5):
        self.trigger_count = trigger_count
        self.counts = defaultdict(int)
        self.examples = {}
        if os.path.exists(DATA_PATH):
            try:
                data = json.load(open(DATA_PATH))
                self.counts.update(data.get("counts", {}))
                self.examples.update(data.get("examples", {}))
            except Exception:
                pass

    def add(self, signature: str, example: str):
        self.counts[signature] += 1
        self.examples.setdefault(signature, example[:500])
        self._persist()

    def needs_retraining(self):
        return [sig for sig, c in self.counts.items() if c >= self.trigger_count]

    def pop_ready(self):
        ready = self.needs_retraining()
        for sig in ready:
            self.counts.pop(sig, None)
            self.examples.pop(sig, None)
        self._persist()
        return ready

    def stats(self):
        return dict(total=len(self.counts), top=sorted(self.counts.items(), key=lambda x:-x[1])[:10])

    def _persist(self):
        json.dump({"counts": self.counts, "examples": self.examples, "ts": int(time.time())}, open(DATA_PATH,"w"))
