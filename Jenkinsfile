node {
    stage("Build") {
        checkout scm
        docker.withRegistry("https://git.vaito.dev", "git-login") {
            def image = docker.build "vaito/ai-toeic"
            image.push "latest"
            image.push "${env.BUILD_ID}"
        }
    } 
}