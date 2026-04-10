pipeline {
    agent any

    environment {
        PYTHON_VERSION = '3.10'
        APP_NAME = 'pdf-hub'
        VENV_DIR = 'venv'
        DEPLOY_USER = credentials('deploy-user')
        DEPLOY_HOST = '${DEPLOY_SERVER}'
        DEPLOY_PATH = '/opt/pdf-hub'
        APP_PORT = '5000'
    }

    triggers {
        githubPush()
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Setup Environment') {
            steps {
                script {
                    if (isUnix()) {
                        sh '''
                            python3 -m venv ${VENV_DIR}
                            source ${VENV_DIR}/bin/activate
                            python3 -m pip install --upgrade pip
                            pip install -r requirements.txt
                        '''
                    } else {
                        bat '''
                            python -m venv %VENV_DIR%
                            call %VENV_DIR%\\Scripts\\activate.bat
                            python -m pip install --upgrade pip
                            pip install -r requirements.txt
                        '''
                    }
                }
            }
        }

        stage('Code Quality') {
            steps {
                script {
                    if (isUnix()) {
                        sh '''
                            source ${VENV_DIR}/bin/activate
                            python3 -m py_compile app.py
                            echo "✓ Python syntax validation passed"
                        '''
                    } else {
                        bat '''
                            call %VENV_DIR%\\Scripts\\activate.bat
                            python -m py_compile app.py
                            echo ✓ Python syntax validation passed
                        '''
                    }
                }
            }
        }

        stage('Build Artifact') {
            steps {
                script {
                    if (isUnix()) {
                        sh '''
                            mkdir -p build
                            cp -r app.py requirements.txt templates/ static/ build/
                            echo "Build number: ${BUILD_NUMBER}" > build/VERSION.txt
                            tar -czf ${APP_NAME}-${BUILD_NUMBER}.tar.gz build/
                        '''
                    } else {
                        bat '''
                            if exist build rmdir /s /q build
                            mkdir build
                            copy app.py build\\
                            copy requirements.txt build\\
                            xcopy /E /I templates build\\templates
                            xcopy /E /I static build\\static
                            echo Build number: %BUILD_NUMBER% > build\\VERSION.txt
                        '''
                    }
                }
            }
        }

        stage('Approval') {
            when {
                branch 'main'
            }
            steps {
                script {
                    input message: 'Approve deployment to production?', ok: 'Deploy'
                }
            }
        }

        stage('Deploy to Server') {
            when {
                branch 'main'
            }
            steps {
                script {
                    if (isUnix()) {
                        sh '''
                            # Stop the running app
                            ssh -i ~/.ssh/id_rsa ${DEPLOY_USER}@${DEPLOY_HOST} \
                                "cd ${DEPLOY_PATH} && pkill -f 'python app.py' || true"
                            
                            # Copy new artifact
                            scp -i ~/.ssh/id_rsa -r build/ \
                                ${DEPLOY_USER}@${DEPLOY_HOST}:${DEPLOY_PATH}/
                            
                            # Deploy and start
                            ssh -i ~/.ssh/id_rsa ${DEPLOY_USER}@${DEPLOY_HOST} \
                                "cd ${DEPLOY_PATH}/build && \
                                 python3 -m venv venv && \
                                 source venv/bin/activate && \
                                 pip install -r requirements.txt && \
                                 nohup python app.py > app.log 2>&1 &"
                        '''
                    } else {
                        echo "Windows deployment: Use WinRM or manual deployment script"
                    }
                }
            }
        }

        stage('Health Check') {
            when {
                branch 'main'
            }
            steps {
                script {
                    if (isUnix()) {
                        sh '''
                            sleep 5
                            ssh -i ~/.ssh/id_rsa ${DEPLOY_USER}@${DEPLOY_HOST} \
                                "curl -s http://localhost:${APP_PORT}/ > /dev/null && \
                                 echo '✓ Application is running' || \
                                 echo '✗ Health check failed'"
                        '''
                    }
                }
            }
        }
    }

    post {
        always {
            cleanWs()
        }
        success {
            echo "✓ Pipeline completed successfully"
        }
        failure {
            echo "✗ Pipeline failed - Check logs above"
        }
    }
}
