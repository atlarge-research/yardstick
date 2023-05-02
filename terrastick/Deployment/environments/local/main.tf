terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "3.0.2"
    }
  }
}

provider "docker" {
  host = "unix:///var/run/docker.sock"
}

locals {
  terraria_server_ip = cidrhost(var.default_docker_subnet, 2)
}

module "terraria_server" {
  source             = "../../modules/docker_server"
  terraria_server_ip = local.terraria_server_ip
}

module "terraria_bot" {
  source             = "../../modules/docker_bot"
  terraria_server_ip = local.terraria_server_ip
  depends_on = [
    module.terraria_server
  ]
}


