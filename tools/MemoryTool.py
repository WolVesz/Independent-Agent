from agency_swarm.tools import BaseTool
from pydantic import Field

class MemoryTool(BaseTool):
    """
    Provides a simple memory mechanism using Agency Swarm's shared_state.
    """

    key: str = Field(..., description="Key to read/write in memory.")
    value: str = Field("", description="Value to store if mode=write.")
    mode: str = Field(..., description="Either 'read' or 'write'.")

    def run(self):
        if self.mode == "write":
            self._shared_state.set(self.key, self.value)
            return f"Stored '{self.value}' under key='{self.key}'."
        elif self.mode == "read":
            val = self._shared_state.get(self.key, None)
            return f"Value for '{self.key}': {val}"
        else:
            return "[MemoryTool] Invalid mode. Use 'read' or 'write'."
