import os, yaml, re
from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Optional, List
from .detector import AnomalyDetector
from .buffer import PatternBuffer
from .actions import ActionsClient

app = FastAPI(title="ReLearnAI Core")

CFG_PATH = os.path.join(os.path.dirname(__file__), "config.yaml")
cfg = yaml.safe_load(open(CFG_PATH))

detector = AnomalyDetector(distance_quantile=cfg["detector"]["distance_quantile"])
loaded = detector.load_latest()
buffer = PatternBuffer(trigger_count=cfg["thresholds"]["pattern_trigger_count"])
actions = ActionsClient(providers=cfg["providers"], rate_limit_per_host=cfg["thresholds"]["max_actions_per_host_hour"])

class LogEvent(BaseModel):
    source: str
    message: str
    level: str = "INFO"
    host: Optional[str] = None
    cluster: Optional[str] = "cluster_A"
    tags: Optional[List[str]] = None
    timestamp: Optional[str] = None

class FitRequest(BaseModel):
    messages: List[str]
    k: int = 8

@app.get("/health")
def health():
    model_ready = (detector.vectorizer is not None and
                   detector.kmeans is not None and
                   detector.threshold is not None)
    return {
        "status": "ok",
        "model_loaded": model_ready,
        "model_version": detector.version,
        "buffer": buffer.stats()
    }

def quick_clean(msg: str) -> str:
    # Limpieza mínima (timestamps, rutas y números largos)
    msg = re.sub(r"\b\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?\b", "<TIMESTAMP>", msg)
    msg = re.sub(r"(?:/[^ \t\n\r\f\v]+)+", "<PATH>", msg)
    msg = re.sub(r"\b\d{4,}\b", "<NUM>", msg)
    return msg

@app.post("/ingest")
def ingest(ev: LogEvent):
    cleaned = quick_clean(ev.message)
    res = detector.predict(cleaned)
    if res["label"] == "unknown":
        buffer.add(res["signature"], ev.message)
    return res

@app.post("/fit")
def fit(req: FitRequest):
    detector.fit(req.messages, k=req.k)
    version = detector.save_new()
    return {"ok": True, "version": version}

@app.post("/retrain")
def retrain():
    ready = buffer.pop_ready()
    if not ready:
        return {"ok": False, "reason": "no_patterns_ready"}
    return {"ok": True, "triggered_signatures": ready}

class ActionRequest(BaseModel):
    provider: str = Field(..., description="Nombre del provider MCP")
    host: str

@app.post("/actions/restart_agent")
def act_restart(req: ActionRequest):
    resp = actions.restart_agent(req.provider, req.host)
    return resp
