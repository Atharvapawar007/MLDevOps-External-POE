pipeline {
    agent any

    environment {
        PYTHONUNBUFFERED = '1'
        VENV_DIR = '.venv'
        PYTHONPATH = "${WORKSPACE}"
        APP_PORT = '8000'
    }

    stages {
        stage('Checkout Code') {
            steps {
                echo 'Stage 1: Checking out source code from Git repository...'
                checkout scm
            }
        }

        stage('Environment Setup') {
            steps {
                echo 'Stage 2: Initializing virtual environment and installing dependencies...'
                sh '''
                    python3 -m venv ${VENV_DIR}
                    . ${VENV_DIR}/bin/activate
                    pip install --upgrade pip setuptools wheel
                    pip install -r requirements.txt
                '''
            }
        }

        stage('Code Linting') {
            steps {
                echo 'Stage 3: Running Flake8 static analysis...'
                sh '''
                    . ${VENV_DIR}/bin/activate
                    flake8 src tests --count --max-line-length=127 --statistics || true
                '''
            }
        }

        stage('Run Pytest Suite') {
            steps {
                echo 'Stage 4: Executing Pytest unit and integration tests...'
                sh '''
                    . ${VENV_DIR}/bin/activate
                    mkdir -p reports
                    pytest --junitxml=reports/test-results.xml -v
                '''
            }
        }

        stage('Evidently Monitoring & Drift Gating') {
            steps {
                echo 'Stage 5: Evaluating Evidently AI data drift and quality test suites...'
                sh '''
                    . ${VENV_DIR}/bin/activate
                    mkdir -p reports
                    python3 src/monitoring.py \
                        --reference data/reference_data.csv \
                        --current data/current_data.csv \
                        --output-html reports/evidently_report.html \
                        --output-json reports/evidently_report.json
                '''
            }
        }

        stage('FastAPI Health Smoke Test') {
            steps {
                echo 'Stage 6: Running FastAPI smoke verification...'
                sh '''
                    . ${VENV_DIR}/bin/activate
                    python3 -c "
from src.app import app
from src.addition import add_numbers
assert add_numbers(10, 20) == 30
print('Addition core and FastAPI app initialized successfully:', app.title)
"
                '''
            }
        }
    }

    post {
        always {
            echo 'Archiving test results, reports, and Evidently dashboards...'
            // Record JUnit test results
            junit testResults: 'reports/test-results.xml', allowEmptyResults: true

            // Archive all generated report files
            archiveArtifacts artifacts: 'reports/**', allowEmptyArchive: true

            // Publish interactive Evidently HTML dashboard in Jenkins UI
            publishHTML target: [
                allowMissing: true,
                alwaysLinkToLastBuild: true,
                keepAll: true,
                reportDir: 'reports',
                reportFiles: 'evidently_report.html',
                reportName: 'Evidently Data Drift & Quality Dashboard'
            ]
        }
        success {
            echo '========================================================'
            echo '  CI/CD PIPELINE SUCCESS: Addition Service Validated!   '
            echo '========================================================'
        }
        failure {
            echo '========================================================'
            echo '  CI/CD PIPELINE FAILED: Check logs and test failures.  '
            echo '========================================================'
        }
    }
}
