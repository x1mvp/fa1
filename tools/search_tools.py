from crewai_tools import BaseTool
from pydantic import Field, BaseModel
from typing import Type
import requests
import json
from bs4 import BeautifulSoup

class DuckDuckGoInput(BaseModel):
    query: str = Field(..., description="Search query for DuckDuckGo")

class DuckDuckGoSearchTool(BaseTool):
    name: str = "duckduckgo_search"
    description: str = "Search the web using DuckDuckGo instant answers API (no API key required)"
    args_schema: Type[BaseModel] = DuckDuckGoInput
    
    def _run(self, query: str) -> str:
        try:
            # DuckDuckGo instant answers API (no key required)
            url = "https://api.duckduckgo.com/"
            params = {
                'q': query,
                'format': 'json',
                'no_html': 1,
                'skip_disambig': 1
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            results = []
            
            # Abstract/Instant Answer
            if data.get('Abstract'):
                results.append(f"Answer: {data['Abstract']}")
                if data.get('AbstractURL'):
                    results.append(f"Source: {data['AbstractURL']}")
            
            # Related Topics
            if data.get('RelatedTopics'):
                for topic in data['RelatedTopics'][:5]:
                    if isinstance(topic, dict) and topic.get('Text'):
                        results.append(f"Related: {topic['Text']}")
            
            return "\n".join(results) if results else "No results found for query: " + query
            
        except Exception as e:
            return f"Search error: {str(e)}"

class WebScraperInput(BaseModel):
    url: str = Field(..., description="URL to scrape for content")

class WebScraperTool(BaseTool):
    name: str = "web_scraper"
    description: str = "Scrape web page content from a given URL"
    args_schema: Type[BaseModel] = WebScraperInput
    
    def _run(self, url: str) -> str:
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for element in soup(['script', 'style']):
                element.decompose()
            
            # Get title
            title = soup.find('title')
            title_text = title.get_text().strip() if title else "No title found"
            
            # Get main content (try common content tags)
            content_tags = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            content_parts = [tag.get_text().strip() for tag in content_tags if tag.get_text().strip()]
            
            # Limit content length
            content = '\n'.join(content_parts[:20])
            
            result = f"Title: {title_text}\n\nContent:\n{content}"
            
            if len(result) > 3000:
                result = result[:3000] + "..."
            
            return result
            
        except Exception as e:
            return f"Failed to scrape {url}: {str(e)}"
