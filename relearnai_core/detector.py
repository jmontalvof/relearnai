from dataclasses import dataclass
from typing import Optional, List
import os, time
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_distances
import joblib

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")
os.makedirs(MODELS_DIR, exist_ok=True)

@dataclass
class DetectionResult:
    label: str              # "normal" | "unknown"
    distance: float
    nearest_cluster: Optional[int]
    signature: str
    version: str

class AnomalyDetector:
    def __init__(self, distance_quantile: float = 0.95):
        self.distance_quantile = distance_quantile
        self.vectorizer = None
        self.kmeans = None
        self.threshold = None
        self.version = "v0"

    def load_latest(self) -> bool:
        path = os.path.join(MODELS_DIR, "latest.joblib")
        if not os.path.exists(path): 
            return False
        bundle = joblib.load(path)
        self.vectorizer = bundle["vectorizer"]
        self.kmeans = bundle["kmeans"]
        self.threshold = bundle["threshold"]
        self.version = bundle.get("version","v0")
        return True

    def save_new(self) -> str:
        ts = int(time.time())
        self.version = f"v{ts}"
        bundle = dict(vectorizer=self.vectorizer, kmeans=self.kmeans, threshold=self.threshold, version=self.version)
        joblib.dump(bundle, os.path.join(MODELS_DIR, f"model_{self.version}.joblib"))
        joblib.dump(bundle, os.path.join(MODELS_DIR, "latest.joblib"))
        return self.version

    def fit(self, messages: List[str], k: int = 8):
        if len(messages) < 10:
            k = max(2, min(4, max(2, len(messages)//2)))
        self.vectorizer = TfidfVectorizer(min_df=1, max_features=5000, ngram_range=(1,2))
        X = self.vectorizer.fit_transform(messages)
        self.kmeans = KMeans(n_clusters=k, n_init=10, random_state=42)
        self.kmeans.fit(X)
        # umbral por cuantil de distancia al centroide propio
        dists = []
        for i in range(X.shape[0]):
            cl = self.kmeans.labels_[i]
            d = cosine_distances(X[i], self.kmeans.cluster_centers_[cl].reshape(1,-1))[0,0]
            dists.append(d)
        self.threshold = float(np.quantile(dists, self.distance_quantile)) if dists else 0.5

    def _signature(self, message: str) -> str:
        import re, hashlib
        txt = re.sub(r"\s+"," ", message.strip().lower())
        return hashlib.sha1(txt.encode()).hexdigest()[:12]

    def predict(self, message: str):
        if self.vectorizer is None or self.kmeans is None or self.threshold is None:
            sig = self._signature(message)
            return dict(label="unknown", distance=1.0, nearest_cluster=None, signature=sig, version=self.version)
        x = self.vectorizer.transform([message])
        dists = cosine_distances(x, self.kmeans.cluster_centers_)
        nearest = int(np.argmin(dists, axis=1)[0])
        dist = float(dists[0, nearest])
        label = "normal" if dist <= self.threshold else "unknown"
        sig = self._signature(message)
        return dict(label=label, distance=dist, nearest_cluster=nearest, signature=sig, version=self.version)
