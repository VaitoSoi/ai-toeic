node {
    stage ("Checkout") {
        checkout scm
    }
    
    docker.withRegistry("https://git.vaito.dev", "docker-login") {
        stage("Build") {
            def image = docker.build "vair.nooi/toeic" --platform linux/amd64,linux/arm64
            image.push "${env.BUILD_ID}"
            image.push "latest"
        }
    } 
}