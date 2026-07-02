pipeline {
    agent any
    environment {
        DOCKERHUB_CREDENTIALS = credentials('Dockerhub')
        SONAR_PROJECT_KEY = 'recharge-app'
        IMAGE_NAME = 'rashidali007/recharge-app'
    }
    stages {
        stage('clone repository') {
            steps {
                git credentialsId: 'Github_account',
                    branch: 'main',
                    url: 'https://github.com/rashid-007/recharge-repo.git'
            }
        }
        stage('SonarQube Analysis') {
            steps {
                withSonarQubeEnv('SonarQube') {
                    sh '''
                        /opt/sonar-scanner/bin/sonar-scanner \
                        -Dsonar.projectKey=${SONAR_PROJECT_KEY} \
                        -Dsonar.sources=. \
                        -Dsonar.host.url=http://sonarqube:9000
                    
                    '''
                }
            }
        }
        stage('Quality Gate') {
            steps {
                timeout(time: 2, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }
        stage('Docker Build Image') {
            steps {
                sh 'docker build -t ${IMAGE_NAME}:${BUILD_NUMBER} . '
            }
        }
        stage('Push to DockerHub') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'Dockerhub', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                    sh 'echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin'
                    sh 'docker push ${IMAGE_NAME}:${BUILD_NUMBER}'
                }
            }
        }
        stage('Deploy to kubernetes') {
            steps {
                sh ''' 
                    /usr/local/bin/kubectl set image deployment/recharge-deployment \
                     recharge-app=${IMAGE_NAME}:${BUILD_NUMBER}
                '''
            }
        }
    }
    post {
        success {
            echo "Congratulations! The deployment succeeded......."
        }
        failure {
            echo "Sorry, there is something wrong"
        }
    }
}
