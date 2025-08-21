# ReLearnAI – Agente de Detección y Reentrenamiento Autónomo

## 📌 Descripción
ReLearnAI es un agente de inteligencia artificial diseñado para **detectar anomalías en logs** (por ejemplo, en Jenkins) y **adaptarse automáticamente** a nuevos patrones.  
En lugar de depender de reglas fijas, el agente:
- Aprende de los **patrones normales**.
- Detecta **nuevas casuísticas** en los registros.
- Se **reentrena automáticamente** cuando aparecen incidencias recurrentes.

Esto lo hace ideal para:
- **DevOps**: diagnóstico de fallos en Jenkins, despliegues, procesos batch.
- **Ciberseguridad**: identificación de patrones sospechosos en logs.
- **Networking**: detección de anomalías en tráfico o servicios.

---

## ⚙️ Arquitectura
1. **Logs** → lectura de registros (ej. `jenkins.log`).
2. **Preprocesamiento** → limpieza de timestamps, IDs, rutas.
3. **Modelo BERT** → embeddings semánticos de cada línea de log.
4. **Detección de anomalías** → IsolationForest identifica patrones fuera de lo normal.
5. **Buffer de patrones normales** → referencia para detecciones futuras.
6. **Reentrenamiento autónomo** → si un patrón anómalo se repite, se integra.

---

## 🚀 Ejemplo de Integración en Jenkins
Un stage de pipeline puede ejecutar el agente periódicamente:

```groovy
stage('Detect anomalies') {
  steps {
    sh '''
      . .venv/bin/activate
      python3 detect_anom_bert.py         --in logs/jenkins_tail.log         --out out/anomalies.csv         --contamination 0.05         --only-anom --top 50 || true
    '''
  }
}
```

- Lee las últimas líneas de log (`jenkins_tail.log`).
- Detecta anomalías y las guarda en `out/anomalies.csv`.
- Muestra en consola las 50 más raras.
- Nunca rompe el pipeline (por `|| true`).

---

## 📊 Ejemplos de Casuísticas Detectadas
- Nodos **offline**.
- Problemas de **memoria o hilos**.
- **Procesos colgados**.
- **Falta de espacio** en disco.
- Errores tras **actualización de plugins**.

---

## 📦 Instalación y Uso

### 1. Clonar el repositorio
```bash
git clone https://github.com/tuusuario/relearnai.git
cd relearnai
```

### 2. Crear entorno virtual
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Ejecutar análisis de logs
```bash
python detect_anom_bert.py   --in logs/ejemplo.log   --out out/anomalies.csv   --contamination 0.05   --only-anom --top 50
```

---

## 📌 Roadmap
- [x] Detección de anomalías en logs de Jenkins.
- [x] Integración con pipeline CI/CD.
- [ ] Notificaciones vía Slack/Email.
- [ ] Dashboards en Grafana/Kibana.
- [ ] Reentrenamiento automático en producción.
- [ ] Extensión a seguridad y networking.

---

## 🛡️ Licencia
MIT License
