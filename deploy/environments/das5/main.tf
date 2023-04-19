resource "external" "DAS5Provisioner" {
  program = ["bash", "-c", <<EOF
    ssh ${var.user}@${var.host} "preserve -np ${var.num} -t 900"
  EOF
  ]
}

data "external" "waitForReservationReady" {
  depends_on = [
    external.DAS5Provisioner,
  ]
  program = ["bash", "-c", <<EOF
    until ssh ${var.user}@${var.host} "preserve -llist" | grep -q "^${external.DAS5Provisioner.result}: ${var.user}"; do
      sleep 5
    done
    while read -r line; do
      fields=($line)
      if [[ ${fields[0]} = "${external.DAS5Provisioner.result}" && ${fields[1]} = "${var.user}" ]]; then
            echo ${fields}
          exit 0
        fi
      fi
    done < <(ssh ${var.user}@${var.host} "preserve -llist")
    exit 1
  EOF
  ]
}

resource "null_resource" "DAS5Provisioner" {
  count = var.num
  triggers = {
    reservation_number = data.external.DAS5Provisioner.result
    node_address = element(data.waitForReservationReady.result, count.index + 7)
  }
}

output "nodes" {
  value = [for i in range(var.num) : {
    user = var.user
    address = element(data.waitForReservationReady.result, i + 8)
    host = var.host
    worker_binary_path = var.worker_binary_path
  }]
}