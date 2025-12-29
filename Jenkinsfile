node {
    stage ("Checkout") {
        checkout scm
    }
    
    docker.withRegistry("https://git.vaito.dev", "docker-login") {
        stage("Build") {
            def image = docker.build "vair.nooi/toeic"
            image.push "${env.BUILD_ID}"
            image.push "latest"
        }

        withCredentials([string(credentialsId: 'docker-compose-path', variable: 'DOCKER_COMPOSE_PATH')]) {
            if (env.DOCKER_COMPOSE_PATH != null && !env.DOCKER_COMPOSE_PATH.isEmpty()) {
                stage("Deploy") {
                    sh 'docker pull git.vaito.dev/vair.nooi/toeic:latest'
                    sh 'docker compose -f $DOCKER_COMPOSE_PATH down toeic'
                    sh 'docker compose -f $DOCKER_COMPOSE_PATH up toeic -d'
                }
            }
        }
    } 
}