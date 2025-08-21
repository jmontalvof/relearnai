import requests
CORE = "http://localhost:8080"

print("Entrenar modelo con mensajes 'normales'...")
normals = ["Build finished successfully","Checkout from git completed","Unit tests passed","Using cache for Docker layer"]
print(requests.post(f"{CORE}/fit", json={"messages": normals, "k": 2}).json())

print("Enviar eventos...")
events = [
    {"source":"jenkins","message":"Build finished successfully"},
    {"source":"jenkins","message":"Cannot contact node 'agent-12'","host":"agent-12","cluster":"cluster_A"},
    {"source":"jenkins","message":"Agent agent-5 is offline","host":"agent-5","cluster":"cluster_A"}
]
for ev in events:
    print(ev["message"], "->", requests.post(f"{CORE}/ingest", json=ev).json())

print("Acción de reinicio (simulada)...")
print(requests.post(f"{CORE}/actions/restart_agent", json={"provider":"cluster_A","host":"agent-5"}).json())
