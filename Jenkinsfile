node {
    stage ("Checkout") {
        checkout scm
    }

    docker.withRegistry("https://git.vaito.dev", "docker-login") {
        stage("Build") {
            def image = docker.build "vair.nooi/ai-toeic"
            image.push "latest"
            image.push "${env.BUILD_ID}"
        }
    } 
}