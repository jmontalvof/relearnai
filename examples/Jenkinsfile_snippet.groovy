post {
  always {
    sh """curl -s -X POST http://RELEARN_CORE:8080/ingest \
      -H 'Content-Type: application/json' \
      -d '{"source":"jenkins","message":"${currentBuild.currentResult} - ${env.JOB_NAME}","host":"${env.NODE_NAME}","cluster":"cluster_A"}' || true"""
  }
}
