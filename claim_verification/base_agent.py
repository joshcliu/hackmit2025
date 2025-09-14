"""
Base class for all verification agents.
"""

from typing import List
from pydantic import BaseModel
from langgraph.prebuilt import create_react_agent
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import Tool
import asyncio
from composio import Composio
from openai import OpenAI
import json


class SourceInfo(BaseModel):
    """Information about a source used in verification."""
    url: str
    title: str
    credibility_notes: str
    relevant_excerpt: str


class AgentOutput(BaseModel):
    """Structured output for all verification agents."""
    sentiment: str  # Natural language assessment
    sources: List[SourceInfo]  # Sources with credibility notes


class BaseVerificationAgent:
    """Base class for all specialized verification agents."""
    
    def __init__(self, model: ChatAnthropic):
        self.model = model
        self.tools = self._setup_tools()
        self.agent = self._create_agent()
        
    def _setup_tools(self):
        """Setup web search and scraping tools."""
        tools = []
        
        # Web search tool using Composio
        def web_search(query: str) -> str:
            """Search the web for information related to the query using Composio."""
            try:
                openai_client = OpenAI()
                composio = Composio()
                
                # User ID must be a valid UUID format
                user_id = "0000-0000-0000"  # Replace with actual user UUID from your database
                
                # Get Composio search tools
                composio_tools = composio.tools.get(user_id=user_id, toolkits=["COMPOSIO_SEARCH"])
                
                # Create completion with search query
                completion = openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "user",
                            "content": f"Search for information about: {query}",
                        },
                    ],
                    tools=composio_tools,
                )
                
                # Handle result from tool call
                result = composio.provider.handle_tool_calls(user_id=user_id, response=completion)
                
                # Extract and return the search results
                if result:
                    return json.dumps(result, indent=2)
                else:
                    return f"No results found for query: {query}"
                    
            except Exception as e:
                return f"Search failed: {str(e)}"
        
        tools.append(Tool(
            name="web_search",
            description="Search the web for information to verify claims using Composio",
            func=web_search
        ))
        
        # Add web scraping tool with fallback options
        def scrape_page(url: str) -> str:
            """Scrape a webpage and return clean text content."""
            # First try: Crawl4AI (if properly set up)
            try:
                from crawl4ai import AsyncWebCrawler
                
                async def async_scrape():
                    try:
                        async with AsyncWebCrawler(verbose=False) as crawler:
                            result = await crawler.arun(
                                url=url,
                                bypass_cache=True,
                                word_count_threshold=10,
                                excluded_tags=['script', 'style'],
                                remove_overlay=True
                            )
                            
                            if result.success:
                                content = result.markdown if result.markdown else result.cleaned_html
                                if len(content) > 5000:
                                    content = content[:5000] + "\n\n[Content truncated...]"
                                return f"Successfully scraped {url}:\n\n{content}"
                            else:
                                return None  # Signal to try fallback
                    except Exception:
                        return None  # Signal to try fallback
                
                # Try to run Crawl4AI
                try:
                    asyncio.get_running_loop()
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, async_scrape())
                        result = future.result(timeout=30)
                        if result:
                            return result
                except RuntimeError:
                    result = asyncio.run(async_scrape())
                    if result:
                        return result
                        
            except ImportError:
                pass  # Fall through to backup methods
            except Exception as e:
                if "Executable doesn't exist" in str(e) or "playwright" in str(e).lower():
                    print("⚠️  Playwright browsers not installed. Run 'playwright install' to use Crawl4AI")
                else:
                    print(f"⚠️  Crawl4AI failed: {e}")
            
            # Fallback 1: Try requests + BeautifulSoup
            try:
                import requests
                from bs4 import BeautifulSoup
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                }
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                
                # Get text content
                text = soup.get_text()
                
                # Clean up whitespace
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text = ' '.join(chunk for chunk in chunks if chunk)
                
                # Truncate if too long
                if len(text) > 5000:
                    text = text[:5000] + "\n\n[Content truncated...]"
                
                return f"Successfully scraped {url} (using requests+BeautifulSoup):\n\n{text}"
                
            except ImportError:
                return f"Could not scrape {url}: Missing dependencies. Install with: pip install requests beautifulsoup4"
            except Exception as e:
                return f"Failed to scrape {url}: {str(e)}"
        
        tools.append(Tool(
            name="scrape_page",
            description="Scrape and extract content from a webpage using Crawl4AI",
            func=scrape_page
        ))
        
        return tools
    
    def _create_agent(self):
        """Create ReAct agent for verification."""
        # Get the system prompt from the subclass
        system_prompt = self.get_prompt()
        
        return create_react_agent(
            model=self.model,
            tools=self.tools,
            prompt=system_prompt
        )
    
    def get_prompt(self):
        """Override in subclasses with specialized prompts."""
        raise NotImplementedError("Subclasses must implement get_prompt()")
    
    async def verify(self, claim: str) -> str:
        """
        Run verification and return natural language assessment.
        
        For now returns natural language. XML parsing will be added later.
        """
        try:
            # Format the claim with the appropriate prefix for this agent type
            user_message = f"Verify this claim: {claim}"
            
            result = await self.agent.ainvoke({"messages": [("user", user_message)]})
            
            # Extract the final message from the agent
            if result.get("messages"):
                last_message = result["messages"][-1]
                if hasattr(last_message, "content"):
                    return last_message.content
            
            return "Unable to verify claim due to processing error."
            
        except Exception as e:
            return f"Verification failed: {str(e)}"
