from fastapi import FastAPI
from pydantic import BaseModel
import time

app = FastAPI(title="Provider MCP (sample)")

class RestartReq(BaseModel):
    host: str

@app.post("/actions/restart_agent")
def restart_agent(req: RestartReq):
    # Aquí ejecutarías systemctl / kubectl / etc. con permisos controlados
    time.sleep(0.2)
    return {"ok": True, "host": req.host, "action": "restart_agent", "msg": "simulated restart"}
