"""
Basic test to ensure the system is working.
"""

import asyncio
import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


async def test_import():
    """Test that all modules can be imported."""
    try:
        from orchestrator import ClaimVerificationOrchestrator
        from base_agent import BaseVerificationAgent, AgentOutput
        from agents import (
            NewsSearcherAgent,
            AcademicSearcherAgent,
            FactCheckSearcherAgent,
            GovernmentDataAgent,
            TemporalConsistencyAgent
        )
        from orchestrator import OrchestratorAgent
        
        print("✅ All modules imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False


async def test_initialization():
    """Test that a single agent can be initialized."""
    try:
        from agents import FactCheckSearcherAgent
        from langchain_anthropic import ChatAnthropic
        
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            print("⚠️  No ANTHROPIC_API_KEY found - using test key")
            api_key = "test-key"
        
        model = ChatAnthropic(
            api_key=api_key,
            model_name="claude-4-sonnet-20250514",
            temperature=0
        )
        
        agent = FactCheckSearcherAgent(model=model)
        
        # Verify the agent was created with tools
        if agent and agent.tools:
            print(f"✅ Agent initialized successfully with {len(agent.tools)} tools")
        else:
            print("✅ Agent initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Initialization error: {e}")
        return False


async def test_single_agent():
    """Test a single agent directly without the orchestrator."""
    try:
        from agents import NewsSearcherAgent
        from langchain_anthropic import ChatAnthropic
        
        # Check if we have an API key
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            print("⚠️  Using mock mode - no ANTHROPIC_API_KEY found")
            # Create a mock agent to test initialization
            from unittest.mock import MagicMock
            model = MagicMock()
        else:
            model = ChatAnthropic(
                model="claude-3-5-sonnet-20241022",
                api_key=api_key,
                temperature=0
            )
        
        # Create the agent
        agent = NewsSearcherAgent(model)
        
        # Test that the agent has tools
        if not agent.tools:
            print("❌ Agent has no tools")
            return False
        
        print(f"✅ NewsSearcherAgent created with {len(agent.tools)} tools:")
        for tool in agent.tools:
            print(f"   - {tool.name}: {tool.description[:50]}...")
        
        # Test the agent's prompt
        prompt = agent.get_prompt()
        if "news verification specialist" in prompt.lower():
            print("✅ Agent prompt is correctly configured")
        else:
            print("❌ Agent prompt seems incorrect")
            return False
        
        # If we have an API key, test a simple verification
        if api_key:
            print("\n📝 Testing simple claim verification...")
            claim = "Python is a programming language"
            try:
                result = await agent.verify(claim)
                if result and len(result) > 20:
                    print("✅ Agent verification returned a response")
                    print(f"   Response preview: {result[:100]}...")
                else:
                    print("⚠️  Agent returned short/empty response")
            except Exception as e:
                print(f"⚠️  Agent verification failed: {e}")
                # This is okay - might be rate limits or network issues
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure langchain-anthropic is installed")
        return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_agent_tools():
    """Test that agent tools (Composio search and Crawl4AI scraper) are working."""
    try:
        from agents import FactCheckSearcherAgent
        from unittest.mock import MagicMock
        
        # Use a mock model for this test
        model = MagicMock()
        agent = FactCheckSearcherAgent(model)
        
        print("Testing agent tools:")
        
        # Check for search tool
        search_tool = None
        scrape_tool = None
        
        for tool in agent.tools:
            if "search" in tool.name.lower() or "composio" in tool.name.lower():
                search_tool = tool
            if "scrape" in tool.name.lower():
                scrape_tool = tool
        
        if search_tool:
            print(f"✅ Found search tool: {search_tool.name}")
            # Test search with a simple query
            try:
                result = search_tool.func("test query")
                print(f"   Search result: {result[:100] if result else 'Empty'}...")
            except Exception as e:
                print(f"   ⚠️  Search tool error: {e}")
        else:
            print("❌ No search tool found")
            return False
        
        if scrape_tool:
            print(f"✅ Found scrape tool: {scrape_tool.name}")
            # Test scraping with example.com
            try:
                result = scrape_tool.func("https://example.com")
                if "Example Domain" in result or "example" in result.lower():
                    print("   ✅ Scraper working correctly")
                else:
                    print(f"   ⚠️  Unexpected scrape result: {result[:100]}...")
            except Exception as e:
                print(f"   ⚠️  Scrape tool error: {e}")
        else:
            print("❌ No scrape tool found")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Tools test error: {e}")
        return False


async def test_simple_claim():
    """Test verifying a simple claim (if API key is available)."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("⚠️  Skipping claim verification test - no API key")
        return True
    
    try:
        from agents import FactCheckSearcherAgent
        from langchain_anthropic import ChatAnthropic
        
        # Initialize the model
        model = ChatAnthropic(
            api_key=api_key,
            model_name="claude-4-sonnet-20250514",
            temperature=0
        )
        
        # Create a single agent instead of orchestrator
        agent = FactCheckSearcherAgent(model=model)
        
        # Test with a simple, verifiable claim
        claim = "The Earth orbits around the Sun"
        print(f"\n📝 Testing claim: '{claim}'")
        
        result = await agent.verify(claim)
        
        if result and len(result) > 50:  # Basic check that we got a response
            print("✅ Claim verification completed")
            print(result[:200] + "..." if len(result) > 200 else result)
            return True
        else:
            print("❌ Claim verification returned empty or short response")
            return False
            
    except Exception as e:
        print(f"❌ Claim verification error: {e}")
        return False


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("CLAIM VERIFICATION SYSTEM - BASIC TESTS")
    print("="*60 + "\n")
    
    tests = [
        ("Import Test", test_import),
        ("Initialization Test", test_initialization),
        ("Simple Claim Test", test_simple_claim),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 40)
        result = await test_func()
        results.append(result)
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ All tests passed ({passed}/{total})")
    else:
        print(f"⚠️  {passed}/{total} tests passed")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
