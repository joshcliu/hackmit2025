"""
Base class for all verification agents.
"""

from typing import List
from pydantic import BaseModel
from langgraph.prebuilt import create_react_agent
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import Tool
import asyncio


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
        search_tool_loaded = False
        
        # Primary option: DuckDuckGo (free, no API key required!)
        # This is the simplest and most reliable option
        try:
            from langchain_community.tools import DuckDuckGoSearchResults
            
            # Initialize DuckDuckGo search (no API key needed!)
            search_tool = DuckDuckGoSearchResults(
                num_results=5,
                name="duckduckgo_search",
                description="Search the web for information using DuckDuckGo (free, no API key required)"
            )
            tools.append(search_tool)
            print("✅ Loaded DuckDuckGo search tool (free)")
            search_tool_loaded = True
            
        except ImportError:
            print("⚠️  langchain-community not installed. Install with: pip install langchain-community duckduckgo-search")
        except Exception as e:
            print(f"⚠️  Failed to initialize DuckDuckGo: {e}")
        
        # Final fallback to mock search if nothing else works
        if not search_tool_loaded:
            def mock_search(query: str) -> str:
                return f"Mock search results for: {query}\nNote: Install langchain-community for real search"
            
            tools.append(Tool(
                name="web_search",
                description="Search the web for information (mock mode - install langchain-community)",
                func=mock_search
            ))
            print("⚠️  Using mock search tool (install langchain-community for real search)")
        
        # Add Crawl4AI scraping tool
        def scrape_page(url: str) -> str:
            """Scrape a webpage using Crawl4AI and return clean text content."""
            try:
                # Import Crawl4AI components
                from crawl4ai import AsyncWebCrawler
                
                # Create an async wrapper to run Crawl4AI in sync context
                async def async_scrape():
                    try:
                        # Initialize the crawler
                        async with AsyncWebCrawler(verbose=False) as crawler:
                            # Crawl the page
                            result = await crawler.arun(
                                url=url,
                                bypass_cache=True,
                                # Use markdown format for better readability
                                word_count_threshold=10,
                                excluded_tags=['script', 'style'],
                                remove_overlay=True
                            )
                            
                            if result.success:
                                # Return the markdown content which is cleaner
                                content = result.markdown if result.markdown else result.cleaned_html
                                # Truncate if too long
                                if len(content) > 5000:
                                    content = content[:5000] + "\n\n[Content truncated...]"
                                return f"Successfully scraped {url}:\n\n{content}"
                            else:
                                return f"Failed to scrape {url}: {result.error_message if hasattr(result, 'error_message') else 'Unknown error'}"
                    except Exception as e:
                        return f"Error during crawling: {str(e)}"
                
                # Run the async function in a sync context
                # Check if there's already an event loop running
                try:
                    asyncio.get_running_loop()
                    # If we're already in an async context, create a new thread
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, async_scrape())
                        return future.result(timeout=30)
                except RuntimeError:
                    # No event loop running, we can use asyncio.run directly
                    return asyncio.run(async_scrape())
                    
            except ImportError as e:
                print(f"Warning: Crawl4AI not installed: {e}")
                return "Crawl4AI not available. Please install it with: pip install crawl4ai"
            except Exception as e:
                print(f"Warning: Scraping failed: {e}")
                return f"Error scraping {url}: {str(e)}"
        
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
