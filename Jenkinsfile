node {
    stage ("Checkout") {
        checkout scm
    }
    
    docker.withRegistry("https://git.vaito.dev", "docker-login") {
        stage("Build app") {
            sh "docker buildx build -t git.vaito.dev/vair.nooi/toeic:${env.BUILD_ID} " +
                                   "-t git.vaito.dev/vair.nooi/toeic:latest " +
                                   "--platform linux/amd64,linux/arm64 " +
                                   "--push " +
                                   "--file app.Dockerfile ."
        }

        stage("Build backend") {
            sh "docker buildx build -t git.vaito.dev/vair.nooi/toeic-backend:${env.BUILD_ID} " +
                                   "-t git.vaito.dev/vair.nooi/toeic-backend:latest " +
                                   "--platform linux/amd64,linux/arm64 " +
                                   "--push " +
                                   "--file backend.Dockerfile ."
        }
    } 
}