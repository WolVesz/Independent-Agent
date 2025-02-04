# Agency.py

from agency_swarm import Agency
from agent.planner.PlannerAgent import PlannerAgent
from agent.executor.ExecutorAgent import ExecutorAgent
from agent.evaluator.EvaluatorAgent import EvaluatorAgent

def create_production_agency():
    planner = PlannerAgent()
    executor = ExecutorAgent()
    evaluator = EvaluatorAgent()

    # The top-level list means "these agents can receive user messages"
    # Then we define sub-lists for direct communication flows.
    # e.g. [planner, executor] means planner can initiate convos with executor, and executor can reply.
    # same for [planner, evaluator].
    # If we also want executor <-> evaluator direct path, we can add [executor, evaluator].
    agency = Agency([
        planner,  # user can talk to planner directly
        [planner, executor],
        [planner, evaluator],
        [executor, evaluator]
    ])

    return agency
