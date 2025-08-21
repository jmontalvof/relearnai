pipeline {
  agent { label 'relearnai' }  // NO usar el controller
  options {
    timestamps()
    buildDiscarder(logRotator(numToKeepStr: '20'))
    disableConcurrentBuilds()
    timeout(time: 5, unit: 'MINUTES')
  }
  triggers {
    cron('H/5 * * * *')  // cada ~5 minutos
  }
  stages {
    stage('Prep env') {
      steps {
        sh '''
          python3 -m venv .venv || true
          . .venv/bin/activate
          pip install -q --upgrade pip
          pip install -q sentence-transformers scikit-learn torch pandas tqdm
        '''
      }
    }
    stage('Extract logs') {
      steps {
        sh '''
          mkdir -p logs out
          # Copia sólo el “tail” del log principal (ajusta ruta si hace falta)
          tail -n 10000 /var/log/jenkins/jenkins.log > logs/jenkins_tail.log || true
        '''
      }
    }
    stage('Detect anomalies') {
      steps {
        sh '''
          . .venv/bin/activate
          python3 detect_anom_bert.py \
            --in logs/jenkins_tail.log \
            --out out/anomalies.csv \
            --contamination 0.05 \
            --only-anom --top 50 || true
        '''
      }
    }
  }
  post {
    success {
      archiveArtifacts artifacts: 'out/anomalies.csv', onlyIfSuccessful: true
      // Opcional: avisar si hay anomalías (umbral)
      sh '''
        if [ -s out/anomalies.csv ]; then
          echo "Anomalías detectadas. Revisa el CSV."
        fi
      '''
    }
    failure {
      echo 'Job falló (timeout u otro error).'
    }
  }
}

