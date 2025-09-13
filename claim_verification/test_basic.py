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
    """Test that orchestrator can be initialized."""
    try:
        from orchestrator import ClaimVerificationOrchestrator
        
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            print("⚠️  No ANTHROPIC_API_KEY found - using test key")
            api_key = "test-key"
        
        orchestrator = ClaimVerificationOrchestrator(
            anthropic_api_key=api_key
        )
        
        print("✅ Orchestrator initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Initialization error: {e}")
        return False


async def test_simple_claim():
    """Test verifying a simple claim (if API key is available)."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("⚠️  Skipping claim verification test - no API key")
        return True
    
    try:
        from orchestrator import ClaimVerificationOrchestrator
        
        orchestrator = ClaimVerificationOrchestrator(
            anthropic_api_key=api_key
        )
        
        # Test with a simple, verifiable claim
        claim = "The Earth orbits around the Sun"
        print(f"\n📝 Testing claim: '{claim}'")
        
        result = await orchestrator.verify_claim(claim)
        
        if result and len(result) > 50:  # Basic check that we got a response
            print("✅ Claim verification completed")
            print(f"   Response length: {len(result)} characters")
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
