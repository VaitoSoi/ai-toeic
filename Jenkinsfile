node {
    stage ("Checkout") {
        checkout scm
    }
    
    docker.withRegistry("https://git.vaito.dev", "docker-login") {
        stage("Build") {
            sh """
            docker buildx build \
                --platform ${platforms} \
                -t ${imageName}:${env.BUILD_ID} \
                -t ${imageName}:latest \
                --push .
            """
        }
    } 
}