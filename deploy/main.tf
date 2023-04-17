terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      # version = "~> 3.0.1"
    }
  }
}

provider "docker" {
    host = "unix:///Users/abalaji/.docker/run/docker.sock"
}


resource "docker_network" "bot-net" {
  name = "bot-net"
  internal = true
  ipam_config {
    subnet = "172.28.0.0/16"
    gateway = "172.28.0.1"
  }

}

resource "docker_container" "terraria" {
  name = "terraria"
  image = "ghcr.io/beardedio/terraria:tshock-latest"
    ports {
        internal = 7777
        external = 7777
    }


  volumes {
    container_path = "/config"
    #  make host path configurable ?
    host_path = "/Users/abalaji/repos/TrProtocol/deploy/config"
    read_only = false
  }
  stdin_open = true
  tty = true 

  env = [
    "worldpath","./2022DistSys.wld"
  ]

  networks_advanced {
    name = docker_network.bot-net.name
    aliases = ["terraria"]
    ipv4_address = "172.28.0.2"
  }


}

resource "docker_image" "bot" {
  name="bot_image"
    build {
        context = "/Users/abalaji/repos/TrProtocol/PlayerEmulations"
        dockerfile = "Dockerfile"
    }

}

resource "docker_container" "botcontainer" {
    name = "bot_container"
    image = docker_image.bot.image_id
    networks_advanced {
        name = docker_network.bot-net.name
        aliases = ["bot"]
    }

    # add terraria container's ip to env
    env = [
        "TERRARIA_IP=172.28.0."
    ]
    volumes {
        container_path = "/app"
        host_path = "/Users/abalaji/repos/TrProtocol/PlayerEmulations/"
        read_only = false
    }
    command = ["dotnet", "run", "--project", "/app/TrClientTest/TrClientTest.csproj"]
    depends_on = [docker_container.terraria]
}



