#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Detectar anomalías en logs (Jenkins) con embeddings (MiniLM) + IsolationForest.
Requisitos: pip install sentence-transformers scikit-learn torch pandas tqdm
Uso: python detect_anom_bert.py --in jenkins.log --out resultados.csv --only-anom --top 50
"""
import re, argparse
from pathlib import Path
import numpy as np, pandas as pd
from tqdm import tqdm
from sklearn.ensemble import IsolationForest
from sentence_transformers import SentenceTransformer

def normalize_line(line: str) -> str:
    s = line.strip()
    s = re.sub(r'\b\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?\b', '<TIMESTAMP>', s)
    s = re.sub(r'\b\d{2}/\d{2}/\d{4}[ T]\d{2}:\d{2}:\d{2}\b', '<TIMESTAMP>', s)
    s = re.sub(r'https?://\S+', '<URL>', s)
    s = re.sub(r'(/[A-Za-z0-9._$%+\-]+)+', '<PATH>', s)
    s = re.sub(r'[A-Za-z]:\\[^ \t\n\r\f\v"]+', '<WIN_PATH>', s)
    s = re.sub(r'\b\d{1,3}(?:\.\d{1,3}){3}\b', '<IP>', s)
    s = re.sub(r'\b\S+@\S+\.\S+\b', '<EMAIL>', s)
    s = re.sub(r'(?:build\s*#\s*|#)\d+', 'build #<N>', s, flags=re.IGNORECASE)
    s = re.sub(r'\bPID\s*=\s*\d+\b', 'PID=<N>', s, flags=re.IGNORECASE)
    s = re.sub(r'\bagent[-_ ]?[A-Za-z0-9._-]+\b', 'agent-<ID>', s, flags=re.IGNORECASE)
    s = re.sub(r'\b\d{4,}\b', '<NUM>', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def load_lines(path: Path, limit=None):
    lines = []
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            if line.strip():
                lines.append(line.rstrip('\n'))
            if limit and len(lines) >= limit:
                break
    return lines

def main():
    ap = argparse.ArgumentParser(description="Anomalías con embeddings (MiniLM) + IsolationForest")
    ap.add_argument('--in', dest='infile', required=True, help='Archivo de log input (txt)')
    ap.add_argument('--out', dest='outfile', help='CSV de salida (opcional)')
    ap.add_argument('--contamination', type=float, default=0.05, help='Proporción esperada de anomalías')
    ap.add_argument('--model', default='sentence-transformers/all-MiniLM-L6-v2', help='Modelo de embeddings')
    ap.add_argument('--only-anom', action='store_true', help='Mostrar solo anomalías')
    ap.add_argument('--top', type=int, default=0, help='Top-N por score si --only-anom')
    ap.add_argument('--limit', type=int, default=None, help='Máx líneas a leer')
    args = ap.parse_args()

    in_path = Path(args.infile)
    if not in_path.exists():
        raise SystemExit(f"No existe el archivo: {in_path}")

    print(f"📥 Leyendo {in_path} ...")
    raw = load_lines(in_path, args.limit)
    clean = [normalize_line(l) for l in raw]

    print(f"🧠 Cargando modelo: {args.model}")
    enc = SentenceTransformer(args.model)

    print(f"🔢 Embeddings de {len(clean)} líneas...")
    emb = enc.encode(clean, batch_size=64, normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=True)

    print("🌲 Entrenando IsolationForest...")
    iso = IsolationForest(contamination=args.contamination, random_state=42, n_estimators=200, n_jobs=-1)
    iso.fit(emb)

    print("🔎 Prediciendo...")
    pred = iso.predict(emb)           # 1 normal, -1 anomalía
    score = -iso.decision_function(emb)

    import pandas as pd
    df = pd.DataFrame({'raw': raw, 'clean': clean, 'label': np.where(pred==-1,'anomaly','normal'), 'score': score})

    if args.outfile:
        df.to_csv(args.outfile, index=False)
        print(f"💾 Guardado: {args.outfile}")

    if args.only_anom:
        dfa = df[df.label=='anomaly'].sort_values('score', ascending=False)
        if args.top > 0: dfa = dfa.head(args.top)
        for _, r in dfa.iterrows():
            print(f"[ANOM] {r.score:.3f} :: {r.raw}")
    else:
        for _, r in df.iterrows():
            tag = "ANOM" if r.label=="anomaly" else "OK  "
            print(f"[{tag}] {r.score:.3f} :: {r.raw}")

if __name__ == '__main__':
    main()
