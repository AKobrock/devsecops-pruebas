pipeline {
    agent any

    environment {
        PATH      = "C:\\Users\\askok\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin;${env.PATH}"
        APP_IMAGE = "vulnapp"
        APP_NAME  = "vulnapp"
        RED       = "devsecops"
    }

    stages {
        stage('Checkout') {
            steps {
                echo "Commit: ${env.GIT_COMMIT}  Build: ${env.BUILD_NUMBER}"
                bat 'if exist reports rmdir /s /q reports'
                bat 'mkdir reports'
            }
        }

        stage('Build') {
            steps {
                bat 'docker build -t %APP_IMAGE%:%BUILD_NUMBER% -t %APP_IMAGE%:latest .'
            }
        }

        stage('Test') {
            steps {
                catchError(buildResult: 'UNSTABLE', stageResult: 'UNSTABLE') {
                    bat 'docker run --rm -v "%WORKSPACE%":/src -w /src python:3.11-slim sh -c "pip install -q -r requirements.txt pytest && pytest -v -p no:cacheprovider --junitxml=reports/pytest.xml test_app.py"'
                }
            }
            post {
                always { junit allowEmptyResults: true, testResults: 'reports/pytest.xml' }
            }
        }

        stage('SAST - Bandit') {
            steps {
                script {
                    def rc = bat(returnStatus: true, script: 'docker run --rm -v "%WORKSPACE%":/src -w /src python:3.11-slim sh -c "pip install -q bandit && bandit app.py -f html -o reports/bandit.html; bandit app.py"')
                    if (rc != 0) { unstable("Bandit encontro problemas de seguridad") }
                }
            }
        }

        stage('Dependencias - pip-audit') {
            steps {
                script {
                    def rc = bat(returnStatus: true, script: 'docker run --rm -v "%WORKSPACE%":/src -w /src python:3.11-slim sh -c "pip install -q pip-audit && pip-audit -r requirements.txt --desc -f markdown -o reports/pip-audit.md; rc=$?; cat reports/pip-audit.md 2>/dev/null; exit $rc"')
                    if (rc != 0) { unstable("pip-audit encontro dependencias con vulnerabilidades (CVE)") }
                }
            }
        }

        stage('Deploy') {
            steps {
                bat 'docker network inspect %RED% >nul 2>&1 || docker network create %RED%'
                bat 'docker rm -f %APP_NAME% >nul 2>&1 & exit /b 0'
                bat 'docker run -d --name %APP_NAME% --network %RED% -p 5000:5000 %APP_IMAGE%:latest'
                bat 'ping -n 6 127.0.0.1 >nul'
                bat 'curl -s "http://localhost:5000/hello?name=TEST"'
            }
        }

        stage('DAST - OWASP ZAP') {
            steps {
                script {
                    def rc = bat(returnStatus: true, script: 'docker run --rm --network %RED% -v "%WORKSPACE%\\reports":/zap/wrk:rw zaproxy/zap-stable zap-full-scan.py -t "http://%APP_NAME%:5000/hello?name=test" -m 1 -r zap_report.html -J zap_report.json')
                    if (rc != 0) { unstable("OWASP ZAP detecto alertas") }
                }
            }
        }

        stage('Monitoring') {
            steps {
                bat 'docker compose -f monitoring\\docker-compose.yml up -d'
                echo 'Grafana: http://localhost:3000 (admin/admin)  Prometheus: http://localhost:9090'
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'reports/**', allowEmptyArchive: true, fingerprint: true
        }
    }
}