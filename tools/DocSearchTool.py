import os
import fnmatch
from agency_swarm.tools import BaseTool
from pydantic import Field

class DocSearchTool(BaseTool):
    """
    Simple substring-based doc search for .md or .txt files in a specified folder.
    """

    query: str = Field(..., description="Search string to find in doc files.")
    docs_folder: str = Field(..., description="Path to docs directory.")
    max_results: int = Field(5, description="Maximum lines to return.")

    def run(self):
        results = []
        if not os.path.isdir(self.docs_folder):
            return f"[DocSearch] Folder not found: {self.docs_folder}"

        for root, dirs, files in os.walk(self.docs_folder):
            for fname in files:
                if fnmatch.fnmatch(fname, "*.md") or fnmatch.fnmatch(fname, "*.txt"):
                    full_path = os.path.join(root, fname)
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()
                        for line in lines:
                            if self.query.lower() in line.lower():
                                snippet = line.strip()
                                results.append(f"{fname}: {snippet}")
                                if len(results) >= self.max_results:
                                    return "\n".join(results)
        if not results:
            return f"[DocSearch] No matches for '{self.query}'."
        return "\n".join(results)
