import requests, time

class ActionsClient:
    def __init__(self, providers: dict, rate_limit_per_host: int = 3):
        self.providers = providers
        self.rate_limit_per_host = rate_limit_per_host
        self.exec_window = {}  # (host, action) -> [timestamps]

    def _allow(self, host: str, action: str):
        key = (host, action)
        now = time.time()
        window = [t for t in self.exec_window.get(key, []) if now - t < 3600]
        self.exec_window[key] = window
        if len(window) >= self.rate_limit_per_host:
            return False
        window.append(now)
        self.exec_window[key] = window
        return True

    def restart_agent(self, provider_name: str, host: str):
        if provider_name not in self.providers:
            return {"ok": False, "reason": "unknown_provider"}
        if not self._allow(host, "restart_agent"):
            return {"ok": False, "reason": "rate_limited"}
        url = f"{self.providers[provider_name]}/actions/restart_agent"
        try:
            r = requests.post(url, json={"host": host}, timeout=5)
            return r.json() if r.ok else {"ok": False, "status": r.status_code}
        except requests.RequestException as e:
            return {"ok": False, "error": str(e)}
