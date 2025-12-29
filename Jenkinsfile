node {
    stage("Build") {
        checkout scm
        def image = docker.build "vaito/ai-toeic"
        image.push "latest"
        image.push "${env.BUILD_ID}"
    } 
}