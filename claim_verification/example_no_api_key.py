#!/usr/bin/env python3
"""
Example of using the verification system WITHOUT any API keys.

This demonstrates:
- Using DuckDuckGo for free web search (no API key needed)
- Mock mode for the LLM (for testing the tool setup)

To run with real verification:
1. Set ANTHROPIC_API_KEY in your .env file
2. Optionally set TAVILY_API_KEY for better search results
"""

import asyncio
import os
from unittest.mock import MagicMock, AsyncMock
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class MockVerificationAgent:
    """Mock agent for testing without Anthropic API key."""
    
    def __init__(self):
        from base_agent import BaseVerificationAgent
        
        # Create a test subclass
        class TestAgent(BaseVerificationAgent):
            def get_prompt(self):
                return "You are a fact-checking agent. Verify claims using web search."
        
        # Create mock model that just returns the search results
        mock_model = MagicMock()
        mock_model.ainvoke = AsyncMock(return_value={
            "messages": [MagicMock(content="Based on search results, this claim appears to be accurate.")]
        })
        
        # Initialize with mock model
        self.agent = TestAgent(mock_model)
        self.tools = self.agent.tools
    
    async def verify(self, claim: str) -> str:
        """Run mock verification using real search tools."""
        print(f"\n🔍 Verifying claim: {claim}")
        
        # Find search tool
        search_tool = next((t for t in self.tools if 'search' in t.name.lower()), None)
        
        if search_tool:
            print(f"   Using tool: {search_tool.name}")
            try:
                # Perform actual search
                results = search_tool.func(claim)
                print(f"   ✅ Found search results")
                
                # In a real agent, the LLM would analyze these results
                # For demo, just show we got results
                if results:
                    return f"Search completed successfully. Results found for: {claim}\n\nSample results:\n{str(results)[:500]}..."
                else:
                    return "No search results found."
            except Exception as e:
                return f"Search failed: {e}"
        else:
            return "No search tool available."


async def main():
    """Run example verification without API keys."""
    
    print("=" * 60)
    print("CLAIM VERIFICATION - NO API KEY DEMO")
    print("=" * 60)
    print("\nThis demo shows the search tools working without any API keys.")
    print("DuckDuckGo search is completely free!\n")
    
    # Check if we have API keys
    has_anthropic = bool(os.getenv("ANTHROPIC_API_KEY"))
    has_tavily = bool(os.getenv("TAVILY_API_KEY"))
    
    print(f"API Keys Status:")
    print(f"  ANTHROPIC_API_KEY: {'✅ Set' if has_anthropic else '❌ Not set (using mock)'}")
    print(f"  TAVILY_API_KEY: {'✅ Set' if has_tavily else '❌ Not set (using DuckDuckGo)'}")
    
    if has_anthropic:
        print("\n💡 You have Anthropic API key set! Use example_usage.py for full verification.")
    
    # Create mock agent for testing
    print("\n" + "-" * 40)
    print("Creating verification agent...")
    
    try:
        agent = MockVerificationAgent()
        print(f"✅ Agent created with {len(agent.tools)} tool(s)")
        
        # Test claims
        test_claims = [
            "The Earth is approximately 4.5 billion years old",
            "Python was created by Guido van Rossum",
            "The speed of light is 299,792,458 meters per second"
        ]
        
        print("\n" + "-" * 40)
        print("Testing verification with free DuckDuckGo search...")
        
        for claim in test_claims:
            result = await agent.verify(claim)
            print(f"\nResult: {result[:200]}...")
            print("-" * 40)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("✅ Search tools work without any API keys!")
    print("📝 To enable full verification:")
    print("   1. Set ANTHROPIC_API_KEY for Claude-powered analysis")
    print("   2. Optionally set TAVILY_API_KEY for premium search")
    print("\n💡 Even without API keys, DuckDuckGo search is fully functional!")


if __name__ == "__main__":
    asyncio.run(main())
