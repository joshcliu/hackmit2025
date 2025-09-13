"""
Base class for all verification agents.
"""

from typing import List, Optional
from pydantic import BaseModel
from langgraph.prebuilt import create_react_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_anthropic import ChatAnthropic
from composio_langchain import LangchainProvider
from crawl4ai import AsyncWebCrawler
from langchain_core.tools import Tool


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
    
    def __init__(self, model: ChatAnthropic, composio_toolset: Optional[LangchainProvider] = None):
        self.model = model
        self.composio = composio_toolset or LangchainProvider()
        self.tools = self._setup_tools()
        self.agent = self._create_agent()
        
    def _setup_tools(self):
        """Setup Composio Tavily search and Crawl4AI tools."""
        tools = []
        
        # Tavily search through Composio (no API key needed)
        try:
            # Get Tavily search tool from Composio using LangchainProvider
            # Note: This may need configuration in Composio dashboard
            tavily_tools = self.composio.wrap_tools(app_name="tavily")
            if tavily_tools:
                tools.extend(tavily_tools)
            else:
                raise Exception("No Tavily tools available")
        except Exception as e:
            print(f"Warning: Could not load Tavily from Composio: {e}")
            # Create a mock search tool for development
            def mock_search(query: str) -> str:
                return f"Mock search results for: {query}"
            tools.append(Tool(
                name="search",
                description="Search the web for information",
                func=mock_search
            ))
        
        # Add Crawl4AI scraping tool
        async def scrape_page(url: str) -> str:
            """Scrape a webpage and return clean text content."""
            try:
                async with AsyncWebCrawler() as crawler:
                    result = await crawler.arun(
                        url=url,
                        word_count_threshold=10,
                        exclude_external_links=True,
                        remove_forms=True
                    )
                    return result.markdown[:3000]  # Limit content length
            except Exception as e:
                return f"Error scraping {url}: {str(e)}"
        
        tools.append(Tool(
            name="scrape_page",
            description="Scrape and extract content from a webpage",
            func=scrape_page
        ))
        
        return tools
    
    def _create_agent(self):
        """Create ReAct agent for verification."""
        # For now, we'll use natural language output with XML tags
        # Structured output will be parsed in a later iteration
        prompt = self.get_prompt()
        
        return create_react_agent(
            model=self.model,
            tools=self.tools,
            prompt=prompt
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
            result = await self.agent.ainvoke({"messages": [("user", claim)]})
            
            # Extract the final message from the agent
            if result.get("messages"):
                last_message = result["messages"][-1]
                if hasattr(last_message, "content"):
                    return last_message.content
            
            return "Unable to verify claim due to processing error."
            
        except Exception as e:
            return f"Verification failed: {str(e)}"
