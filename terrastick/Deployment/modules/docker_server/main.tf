terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "3.0.2"
    }
  }
}

resource "docker_container" "terraria_server" {
  name = "terraria-server"
  //image = "ghcr.io/beardedio/terraria:tshock-latest"
  image = "ryshe/terraria:tshock-latest"

  ports {
    internal = "7777"
    external = "7777"
  }

  volumes {
    //container_path = "/config"
    container_path = "/root/.local/share/Terraria/Worlds"
    host_path      = abspath("${path.module}/../../config")
    read_only      = false
  }

  stdin_open = true
  tty        = true

  env = [
    //"world=2022DistSys.wld"
    "WORLD_FILENAME=2022DistSys.wld"
  ]
}
