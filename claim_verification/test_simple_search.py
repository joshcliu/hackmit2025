#!/usr/bin/env python3
"""
Simple test to verify DuckDuckGo search works.
"""

import asyncio
from langchain_community.tools import DuckDuckGoSearchResults

def test_direct_search():
    """Test DuckDuckGo search directly (without the agent)."""
    print("=" * 60)
    print("Testing DuckDuckGo Search Directly")
    print("=" * 60)
    
    try:
        # Create the search tool
        search = DuckDuckGoSearchResults(
            num_results=3,
            name="duckduckgo_search",
            description="Search the web"
        )
        
        # Test query
        query = "What is the height of the Eiffel Tower in meters?"
        print(f"\nSearching for: {query}")
        print("-" * 40)
        
        # Run search
        results = search.invoke(query)
        print("\nResults:")
        print(results)
        
        print("\n✅ DuckDuckGo search is working!")
        
    except ImportError as e:
        print(f"\n❌ Import error: {e}")
        print("\nPlease install required packages:")
        print("  pip install langchain-community duckduckgo-search")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure you have installed: pip install langchain-community duckduckgo-search")
        print("2. Check your internet connection")
        print("3. Try updating the packages: pip install --upgrade langchain-community duckduckgo-search")

async def test_with_agent():
    """Test DuckDuckGo through the verification agent."""
    print("\n" + "=" * 60)
    print("Testing DuckDuckGo Through Verification Agent")
    print("=" * 60)
    
    try:
        from langchain_anthropic import ChatAnthropic
        from base_agent import BaseVerificationAgent
        import os
        
        # Check for API key
        if not os.getenv("ANTHROPIC_API_KEY"):
            print("\n⚠️  ANTHROPIC_API_KEY not set. Skipping agent test.")
            print("Set it with: export ANTHROPIC_API_KEY=your-key-here")
            return
        
        class TestAgent(BaseVerificationAgent):
            """Simple test agent."""
            def get_prompt(self):
                return "You are a test agent. Use the search tool to find information."
        
        # Initialize
        model = ChatAnthropic(
            model="claude-3-5-sonnet-20241022",
            temperature=0
        )
        agent = TestAgent(model=model)
        
        print("\nAvailable tools:")
        for tool in agent.tools:
            print(f"  - {tool.name}: {tool.description}")
        
        # Test claim
        claim = "The Eiffel Tower is 324 meters tall"
        print(f"\nVerifying claim: '{claim}'")
        print("-" * 40)
        
        result = await agent.verify(claim)
        print("\nAgent result:")
        print(result)
        
        print("\n✅ Agent with DuckDuckGo search is working!")
        
    except Exception as e:
        print(f"\n❌ Agent test failed: {e}")

def main():
    """Run all tests."""
    # Test direct search first
    test_direct_search()
    
    # Then test with agent
    try:
        asyncio.run(test_with_agent())
    except KeyboardInterrupt:
        print("\n\nTest interrupted.")

if __name__ == "__main__":
    main()
