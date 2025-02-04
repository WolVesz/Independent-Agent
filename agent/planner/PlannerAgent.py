import logging
import os
import yaml
from agency_swarm import Agent
from tools.MemoryTool import MemoryTool
from agent.container_logging import setup_dual_logger


class PlannerAgent(Agent):
    """
    The Planner/CEO agent. Receives user requests, breaks them into tasks,
    instructs ExecutorAgent, and checks results with EvaluatorAgent.
    """

    def __init__(self, config_file="./config/agent_config.yaml"):
        # Load config for logging
        if not os.path.isfile(config_file):
            raise FileNotFoundError(f"PlannerAgent could not find config at {config_file}")

        with open(config_file, "r") as f:
            self.config = yaml.safe_load(f)

        logs_folder = self.config["agent"]["logs_folder"]
        ext_level = getattr(logging, self.config["agent"]["external_log_level"], logging.DEBUG)
        cont_level = getattr(logging, self.config["agent"]["container_log_level"], logging.INFO)

        super().__init__(
            name="PlannerAgent",
            description="Agent that plans tasks, delegates to Executor/evaluator",
            instructions=os.path.join(os.path.dirname(__file__), "instructions_planner.md"),
            tools=[MemoryTool],
            temperature=0.2,
            max_prompt_tokens=20000
        )

        self.logger = setup_dual_logger("PlannerAgent", logs_folder, external_level=ext_level, container_level=cont_level)

    def on_agent_init(self):
        self.logger.info("PlannerAgent initialized.")
        super().on_agent_init()

    def teardown(self):
        self.logger.info("PlannerAgent is shutting down.")
        super().teardown()
