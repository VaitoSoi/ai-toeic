node {
    stage("Build") {
        checkout scm
        docker.withRegistry("https://git.vaito.dev", "docker-login") {
            def image = docker.build "vaito/ai-toeic"
            image.push "latest"
            image.push "${env.BUILD_ID}"
        }
    } 
}