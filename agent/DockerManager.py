# agent/DockerManager.py

import os
import uuid
import docker
from docker.types import DeviceRequest

class DockerManager:
    """
    Manages a persistent Docker container for the ExecutorAgent's runtime,
    with resource constraints and a volume mapping for logs (or other data).
    """

    def __init__(self, container_image="python:3.10-slim",
                 cpu_shares=2,
                 memory_limit="2g",
                 enable_gpu=False,
                 logs_host_folder="./logs",
                 container_name_prefix="executor"):
        self.container_image = container_image
        self.cpu_shares = cpu_shares
        self.memory_limit = memory_limit
        self.enable_gpu = enable_gpu
        self.logs_host_folder = os.path.abspath(logs_host_folder)
        self.container_name = f"{container_name_prefix}_{uuid.uuid4().hex[:6]}"
        self.client = docker.from_env()
        self.container = None

        os.makedirs(self.logs_host_folder, exist_ok=True)
        self._create_container()

    def _create_container(self):
        """
        Create and start the container with resource constraints.
        By default, it runs 'tail -f /dev/null' so it stays alive.
        """
        host_config = self.client.api.create_host_config(
            cpu_shares=self.cpu_shares,
            mem_limit=self.memory_limit
        )

        kwargs = {
            "image": self.container_image,
            "name": self.container_name,
            "command": "tail -f /dev/null",
            "detach": True,
            "tty": True,
            "stdin_open": True,
            "volumes": {
                self.logs_host_folder: {
                    "bind": "/app/logs",
                    "mode": "rw"
                }
            },
            "host_config": host_config
        }

        if self.enable_gpu:
            # Docker 19.03+ can do device requests for GPUs
            kwargs["device_requests"] = [DeviceRequest(count=-1, capabilities=[["gpu"]])]

        self.container = self.client.containers.run(**kwargs)

    def install_requirements(self, requirements_path: str):
        """
        If you have a project_requirements.txt, install it in the container.
        """
        if not os.path.isfile(requirements_path):
            return
        cmd = f"pip install -r {requirements_path}"
        exit_code, output = self.container.exec_run(cmd)
        if exit_code != 0:
            print("[DockerManager] Error installing requirements:", output.decode("utf-8"))

    def copy_to_container(self, local_path: str, container_path: str):
        """
        Copy a local file to container using tar streaming.
        """
        import tarfile
        import io

        tar_stream = io.BytesIO()
        with tarfile.open(fileobj=tar_stream, mode='w') as tar:
            tar.add(local_path, arcname=os.path.basename(container_path))
        tar_stream.seek(0)

        base_dir = os.path.dirname(container_path)
        self.container.exec_run(f"mkdir -p {base_dir}")
        result = self.container.put_archive(base_dir, tar_stream)
        if not result:
            print(f"[DockerManager] Could not put file {local_path} to {container_path}.")

    def exec_python_file(self, filepath: str):
        """
        Execute a Python file inside the container and return (exit_code, output).
        """
        cmd = f"python {filepath}"
        exit_code, output = self.container.exec_run(cmd)
        return exit_code, output.decode("utf-8", errors="ignore")

    def stop_and_remove(self):
        if self.container:
            try:
                self.container.stop()
            except Exception as e:
                print(f"[DockerManager] Error stopping container: {e}")
            try:
                self.container.remove()
            except Exception as e:
                print(f"[DockerManager] Error removing container: {e}")
        self.container = None
