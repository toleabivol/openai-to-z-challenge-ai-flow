from crewai.tools import BaseTool
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
from pydantic import Field


class SearchTool(BaseTool):
    name: str = "Search"
    description: str = ("Useful for search-based queries. "
                        "Use this to find current information about public text records, maps, "
                        "historical records, and other public resources.")
    search: DuckDuckGoSearchAPIWrapper = Field(default_factory=DuckDuckGoSearchAPIWrapper)

    def _run(self, query: str) -> str:
        """Execute the search query and return results"""
        try:
            return self.search.run(query)
        except Exception as e:
            return f"Error performing search: {str(e)}"