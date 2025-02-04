import logging
import os
import yaml
from agency_swarm import Agent
from tools.MemoryTool import MemoryTool
from agent.container_logging import setup_dual_logger


class EvaluatorAgent(Agent):
    """
    The evaluator checks the Executor's results.
    If results are invalid, it recommends retry or escalation to Planner.
    """

    def __init__(self, config_file="./config/agent_config.yaml"):
        if not os.path.isfile(config_file):
            raise FileNotFoundError(f"EvaluatorAgent missing config at {config_file}")

        with open(config_file, "r") as f:
            self.config = yaml.safe_load(f)

        logs_folder = self.config["agent"]["logs_folder"]
        ext_level = getattr(logging, self.config["agent"]["external_log_level"], logging.DEBUG)
        cont_level = getattr(logging, self.config["agent"]["container_log_level"], logging.INFO)

        super().__init__(
            name="EvaluatorAgent",
            description="Agent that evaluates Executor outputs",
            instructions=os.path.join(os.path.dirname(__file__), "instructions_evaluator.md"),
            tools=[MemoryTool],
            temperature=0.2,
            max_prompt_tokens=20000
        )

        self.logger = setup_dual_logger("EvaluatorAgent", logs_folder, external_level=ext_level, container_level=cont_level)

    def on_agent_init(self):
        self.logger.info("EvaluatorAgent initialized.")
        super().on_agent_init()

    def teardown(self):
        self.logger.info("EvaluatorAgent shutting down.")
        super().teardown()

    def evaluate_result(self, result_text: str):
        """
        A simple check to see if the result_text indicates success or error.
        More sophisticated logic can parse results for correctness.
        """
        # Example logic: if "error" or "exception" in text -> fail
        lowered = result_text.lower()
        if "error" in lowered or "traceback" in lowered or "fail" in lowered:
            # Suggest a retry
            return False, "evaluator: The result seems erroneous. Requesting retry or alternative approach."
        # Otherwise success
        return True, "evaluator: The result seems valid."
