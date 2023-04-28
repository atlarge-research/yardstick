terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "3.0.2"
    }
  }
}

resource "docker_image" "terraria_bot_image" {
  name = "terraria-bot-image"
  build {
    context    = "../../../PlayerEmulations"
    dockerfile = "Dockerfile"
  }

}

resource "docker_container" "terraria_bot" {
  name  = "terraria-bot"
  image = docker_image.terraria_bot_image.image_id

  env = [
    "TERRARIA_IP=${var.terraria_server_ip}",
  ]
  volumes {
    container_path = "/app"
    host_path      = abspath("${path.module}/../../../PlayerEmulations")
    read_only      = false
  }
  command = ["dotnet", "run", "--project", "/app/TrClientTest/TrClientTest.csproj"]
}
