import time
from plumbum import local
from yardstick_benchmark.model import Node
from pathlib import Path
import os


class Das(object):
    def __init__(self):
        self._reservation_map = dict()

    def _wait_for_ready(self, reservation_number: int) -> None:
        preserve = local["preserve"]
        ready = False
        while not ready:
            llist = preserve["-llist"]()
            for line in llist.split("\n")[3:]:
                parts = line.split()
                r = int(parts[0])
                if reservation_number == r:
                    ready = parts[6] == "R"
                    break
            if not ready:
                time.sleep(1)

    def _get_machines(self, reservation_number: int) -> list[str]:
        preserve = local["preserve"]
        llist = preserve["-llist"]()
        for line in llist.split("\n")[3:]:
            parts = line.split()
            r = int(parts[0])
            if reservation_number == r:
                return parts[8:]
        raise KeyError(f"reservation {reservation_number} does not exist")

    def provision(self, num=1, time_s=900) -> list[Node]:
        preserve = local["preserve"]
        reservation = int(preserve["-np", num, "-t", time_s]().split()[2][:-1])
        self._wait_for_ready(reservation)
        machines = self._get_machines(reservation)
        res = [
            Node(host=host, wd=Path(f"/local/{os.getlogin()}/yardstick/{host}"))
            for host in machines
        ]
        self._reservation_map[reservation] = set(res)
        return res

    def _cancel_reservation(self, number: int) -> None:
        preserve = local["preserve"]
        preserve["-c", number]()

    def release(self, machines: list[Node]) -> None:
        machines_to_release = set(machines)
        reservations_to_cancel = set()
        for item in self._reservation_map.items():
            item[1].difference_update(machines_to_release)
            if len(item[1]) == 0:
                reservations_to_cancel.add(item[0])
        for reservation in reservations_to_cancel:
            self._cancel_reservation(reservation)
            del self._reservation_map[reservation]

class SingleHost(object):
    """Provisioner for single-host deployments (local or remote)."""
    def __init__(self, host: str, username: str, port: int = 22):
        """
        Initialize SingleHost provisioner.
    
        Args:
            host: Hostname or IP address
            username: SSH username
            port: SSH port (default 22)
        """
        self.host = host
        self.username = username
        self.port = port

    def provision(self, num: int = 1) -> list[Node]:
        """Return a single node (num is ignored)."""
        if num > 1:
            raise ValueError("SingleHost provisioner only supports single-node deployments")
        return [Node(host=self.host, wd=Path(f"/home/{self.username}/yardstick"))]

    def release(self, machines: list[Node]) -> None:
        """No-op: cannot terminate production systems."""
        pass

class AwsEc2(object):
    """Provisioner for AWS EC2 instances."""
    def __init__(self, region: str = 'us-east-1', ami_id: str = None, instance_type: str = 't3.micro', 
                    key_name: str = None, security_group_ids: list = None, username: str = 'ec2-user'):
        """
        Initialize AwsEc2 provisioner.
    
        Args:
            region: AWS region
            ami_id: AMI ID to use (default: latest Amazon Linux 2)
            instance_type: EC2 instance type
            key_name: SSH key pair name (must already exist in AWS)
            security_group_ids: List of security group IDs
            username: SSH username for the AMI
        """
        try:
            import boto3
            self.ec2 = boto3.client('ec2', region_name=region)
            self.region = region
        except ImportError:
            raise ImportError("boto3 is required for AwsEc2 provisioner. Install with: pip install boto3")
    
        self.ami_id = ami_id
        self.instance_type = instance_type
        self.key_name = key_name
        self.security_group_ids = security_group_ids or []
        self.username = username
        self._instances = []

    def _get_default_ami(self) -> str:
        """Get the latest Amazon Linux 2 AMI ID if not specified."""
        if self.ami_id:
            return self.ami_id
    
        response = self.ec2.describe_images(
            Owners=['amazon'],
            Filters=[
                {'Name': 'name', 'Values': ['amzn2-ami-hvm-*-x86_64-gp2']},
                {'Name': 'state', 'Values': ['available']}
            ]
        )
        if not response['Images']:
            raise RuntimeError("No Amazon Linux 2 AMI found")
    
        # Sort by creation date, get the latest
        latest = sorted(response['Images'], key=lambda x: x['CreationDate'])[-1]
        return latest['ImageId']

    def provision(self, num: int = 1) -> list[Node]:
        """Launch num EC2 instances and return Node objects."""
        ami_id = self._get_default_ami()
    
        # Launch instances
        run_response = self.ec2.run_instances(
            ImageId=ami_id,
            MinCount=num,
            MaxCount=num,
            InstanceType=self.instance_type,
            KeyName=self.key_name,
            SecurityGroupIds=self.security_group_ids,
        )
    
        instance_ids = [inst['InstanceId'] for inst in run_response['Instances']]
        self._instances.extend(instance_ids)
    
        # Wait for instances to be running
        waiter = self.ec2.get_waiter('instance_running')
        waiter.wait(InstanceIds=instance_ids)
    
        # Get public IPs
        describe_response = self.ec2.describe_instances(InstanceIds=instance_ids)
        nodes = []
        for reservation in describe_response['Reservations']:
            for instance in reservation['Instances']:
                public_ip = instance.get('PublicIpAddress')
                if not public_ip:
                    raise RuntimeError(f"Instance {instance['InstanceId']} has no public IP")
                nodes.append(Node(
                    host=public_ip,
                    wd=Path(f"/home/{self.username}/yardstick")
                ))
    
        return nodes

    def release(self, machines: list[Node]) -> None:
        """Terminate all provisioned instances."""
        if self._instances:
            self.ec2.terminate_instances(InstanceIds=self._instances)
            # Wait for termination
            waiter = self.ec2.get_waiter('instance_terminated')
            waiter.wait(InstanceIds=self._instances)
            self._instances.clear()
