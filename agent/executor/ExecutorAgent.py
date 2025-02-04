import os
import uuid
import logging
import yaml
from agency_swarm import Agent
from tools.MemoryTool import MemoryTool
from tools.DocSearchTool import DocSearchTool
from agent.DockerManager import DockerManager
from agent.container_logging import setup_dual_logger


class ExecutorAgent(Agent):
    """
    The Executor/Developer agent that runs code in a Docker container.
    It includes:
    - snippet retry up to max_snippet_retries
    - basic loop detection to avoid infinite error loops
    - doc search to consult local references
    """

    def __init__(self, config_file="./config/agent_config.yaml"):
        if not os.path.isfile(config_file):
            raise FileNotFoundError(f"ExecutorAgent missing config at {config_file}")
        with open(config_file, "r") as f:
            self.config = yaml.safe_load(f)

        agent_cfg = self.config["agent"]
        logs_folder = agent_cfg["logs_folder"]
        ext_level = getattr(logging, agent_cfg["external_log_level"], logging.DEBUG)
        cont_level = getattr(logging, agent_cfg["container_log_level"], logging.INFO)

        # Docker resource config
        docker_cfg = agent_cfg["docker_resources"]
        cpu_shares = docker_cfg["cpu_shares"]
        mem_limit = docker_cfg["memory_limit"]
        gpu_enabled = docker_cfg["gpu_enabled"]

        # Retry & loop detection
        self.max_snippet_retries = agent_cfg["max_snippet_retries"]
        self.loop_detection_count = agent_cfg["loop_detection_count"]

        super().__init__(
            name="ExecutorAgent",
            description="Agent that writes and runs code in Docker",
            instructions=os.path.join(os.path.dirname(__file__), "instructions_executor.md"),
            tools=[MemoryTool, DocSearchTool],
            temperature=0.3,
            max_prompt_tokens=20000
        )

        self.logger = setup_dual_logger("ExecutorAgent", logs_folder, external_level=ext_level,
                                        container_level=cont_level)

        # Initialize Docker manager
        self.docker_manager = DockerManager(
            container_image="python:3.10-slim",
            cpu_shares=cpu_shares,
            memory_limit=mem_limit,
            enable_gpu=gpu_enabled,
            logs_host_folder=logs_folder,
            container_name_prefix="ExecutorAgent"
        )

        self.snippet_attempts = {}  # snippet_code -> how many times we've tried
        self.last_snippet = None

    def on_agent_init(self):
        self.logger.info("ExecutorAgent init complete. Docker container ready.")
        super().on_agent_init()

        # Possibly install project requirements if environment variable is set
        project_reqs = os.getenv("PROJECT_REQUIREMENTS_TXT", "")
        if project_reqs:
            self.logger.info(f"Installing project requirements: {project_reqs}")
            self.docker_manager.install_requirements(project_reqs)

    def teardown(self):
        self.logger.info("ExecutorAgent shutting down, removing Docker container.")
        self.docker_manager.stop_and_remove()
        super().teardown()

    def run_python_snippet(self, code: str):
        """
        Attempt to run the code snippet. We'll do up to max_snippet_retries
        if there's an error or we detect a loop.
        """
        snippet_key = code.strip()
        attempts = self.snippet_attempts.get(snippet_key, 0)

        if attempts >= self.max_snippet_retries:
            self.logger.warning(f"[Executor] Already tried snippet too many times.")
            return (1, "[Executor] Max retries exceeded. Escalate to Planner.")

        # Check if this is a loop: if the agent is repeating the same snippet consecutively
        if self.last_snippet == code:
            # if repeated snippet is used more than loop_detection_count times in a row
            if attempts >= self.loop_detection_count:
                self.logger.warning("[Executor] Loop detected with identical snippet. Escalate.")
                return (1, "[Executor] Loop detected. Escalate to Planner.")

        # Track attempt
        self.snippet_attempts[snippet_key] = attempts + 1
        self.last_snippet = code

        # 1) Write snippet to local tmp file
        snippet_id = uuid.uuid4().hex[:6]
        local_snippet_path = f"/tmp/snippet_{snippet_id}.py"
        with open(local_snippet_path, "w", encoding="utf-8") as f:
            f.write(code)

        # 2) Copy to container
        container_snippet_path = f"/tmp/snippets/snippet_{snippet_id}.py"
        self._ensure_dir_in_container("/tmp/snippets")
        self.docker_manager.copy_to_container(local_snippet_path, container_snippet_path)

        # 3) Execute
        exit_code, output = self.docker_manager.exec_python_file(container_snippet_path)
        # 4) Log
        if exit_code == 0:
            self.logger.debug(f"[Snippet {snippet_id} OK] {output}")
        else:
            self.logger.debug(f"[Snippet {snippet_id} ERR] {output}")

        return (exit_code, output)

    def _ensure_dir_in_container(self, dirpath: str):
        cmd = f"mkdir -p {dirpath}"
        self.docker_manager.container.exec_run(cmd)
