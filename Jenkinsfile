pipeline {
    agent any

    // Automatically trigger pipeline when changes are pushed
    triggers {
        // Poll GitHub every 2 minutes for changes
        pollSCM('H/2 * * * *')
    }

    environment {
        // Docker image name
        IMAGE_NAME    = 'attendance-system'
        CONTAINER_NAME = 'attendance-system'
        APP_PORT      = '8085'
    }

    stages {

        stage('Checkout') {
            steps {
                echo '📥 Pulling latest code from GitHub...'
                checkout scm
            }
        }

        stage('Build Docker Image') {
            steps {
                echo '🐳 Building Docker image...'
                script {
                    bat "docker build -t ${IMAGE_NAME}:latest ."
                }
            }
        }

        stage('Test') {
            steps {
                echo '🧪 Running smoke test...'
                script {
                    // Start a temporary container to verify the app boots
                    bat """
                        docker run -d --name ${CONTAINER_NAME}-test ^
                            --env-file .env ^
                            -p 9090:${APP_PORT} ^
                            ${IMAGE_NAME}:latest
                    """

                    // Wait for the app to start
                    bat 'ping -n 11 127.0.0.1 > nul'

                    // Check if the container is still running (basic health check)
                    bat "docker ps --filter name=${CONTAINER_NAME}-test --filter status=running"

                    // Cleanup test container
                    bat """
                        docker stop ${CONTAINER_NAME}-test || exit 0
                        docker rm ${CONTAINER_NAME}-test || exit 0
                    """
                }
            }
        }

        stage('Deploy') {
            steps {
                echo '🚀 Deploying application...'
                script {
                    // Stop and remove any existing container
                    bat """
                        docker stop ${CONTAINER_NAME} || exit 0
                        docker rm ${CONTAINER_NAME} || exit 0
                    """

                    // Deploy using docker-compose
                    bat 'docker-compose up -d --build'
                }
            }
        }

        stage('Cleanup') {
            steps {
                echo '🧹 Cleaning up old Docker images...'
                script {
                    // Remove dangling images to free disk space
                    bat 'docker image prune -f || exit 0'
                }
            }
        }
    }

    post {
        success {
            echo "✅ Pipeline completed successfully! App is running on port ${APP_PORT}"
        }
        failure {
            echo '❌ Pipeline failed! Check the logs above for details.'
            script {
                // Cleanup on failure
                bat """
                    docker stop ${CONTAINER_NAME}-test || exit 0
                    docker rm ${CONTAINER_NAME}-test || exit 0
                """
            }
        }
        always {
            echo '📋 Pipeline finished.'
        }
    }
}
