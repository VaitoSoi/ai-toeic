// Define variables globally for the script
def platforms = "linux/amd64,linux/arm64"
def imageName = "git.vaito.dev/vair.nooi/toeic"

node {
    stage ("Checkout") {
        checkout scm
    }
    
    docker.withRegistry("https://git.vaito.dev", "docker-login") {
        stage("Build Multi-Platform") {
            // Use env variables to ensure they are available to the shell block
            withEnv(["PLATFORMS=${platforms}", "IMAGE_NAME=${imageName}"]) {
                sh """
                docker buildx build \
                    --platform ${env.PLATFORMS} \
                    -t ${env.IMAGE_NAME}:${env.BUILD_ID} \
                    -t ${env.IMAGE_NAME}:latest \
                    --push .
                """
            }
        }
    } 
}