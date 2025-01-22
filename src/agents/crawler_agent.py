import requests
from bs4 import BeautifulSoup
from langchain.tools import Tool
from langchain.utilities import SerpAPIWrapper

class CrawlerAgent:
    def __init__(self, config: dict):
        self.max_results = config['max_results']
        self.max_depth = config['max_depth']
        self.search = SerpAPIWrapper()
        self.tools = [
            Tool(
                name="Search",
                func=self.search.run,
                description="Useful for searching the internet for recent or current events"
            )
        ]

    def crawl(self, query: str) -> str:
        search_results = self.search.run(query)
        content = []
        for result in search_results[:self.max_results]:
            url = result['link']
            page_content = self._fetch_page_content(url, depth=0)
            content.append(f"Source: {url}\n{page_content}")
        return "\n\n".join(content)

    def _fetch_page_content(self, url: str, depth: int) -> str:
        if depth >= self.max_depth:
            return ""
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            text = soup.get_text(separator='\n', strip=True)
            return text[:500]  # Limit to first 500 characters
        except Exception as e:
            return f"Error fetching content: {str(e)}"

