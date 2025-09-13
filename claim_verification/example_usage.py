"""
Example usage of the claim verification system.
"""

import asyncio
import os
from dotenv import load_dotenv
from claim_verification import ClaimVerificationOrchestrator


async def verify_single_claim():
    """Example of verifying a single claim."""
    
    # Initialize orchestrator
    orchestrator = ClaimVerificationOrchestrator(
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        composio_api_key=None  # Not needed for Tavily
    )
    
    # Example claim
    claim = "The unemployment rate is at 3.5%"
    
    print(f"\n{'='*60}")
    print(f"Verifying claim: {claim}")
    print(f"{'='*60}\n")
    
    # Verify the claim
    result = await orchestrator.verify_claim(claim)
    
    print("\nVerification Result:")
    print("-" * 40)
    print(result)
    print("-" * 40)


async def verify_multiple_claims():
    """Example of verifying multiple claims in parallel."""
    
    # Initialize orchestrator
    orchestrator = ClaimVerificationOrchestrator(
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        composio_api_key=None
    )
    
    # Multiple claims to verify
    claims = [
        "The unemployment rate is at 3.5%",
        "Crime rates in major cities are at an all-time high",
        "The federal deficit decreased by 1 trillion dollars last year"
    ]
    
    print(f"\n{'='*60}")
    print("Verifying multiple claims in parallel")
    print(f"{'='*60}\n")
    
    # Verify all claims in parallel
    results = await orchestrator.verify_claims_batch(claims)
    
    # Display results
    for claim, result in zip(claims, results):
        print(f"\n{'='*60}")
        print(f"Claim: {claim}")
        print(f"{'='*60}")
        print("\nAssessment:")
        print("-" * 40)
        print(result)
        print("-" * 40)


async def test_with_various_claims():
    """Test the system with different types of claims."""
    
    # Initialize orchestrator
    orchestrator = ClaimVerificationOrchestrator(
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        composio_api_key=None
    )
    
    test_claims = [
        # Statistical claim
        "GDP grew by 2.1% in the last quarter",
        
        # Comparative claim
        "This is the lowest inflation rate in 40 years",
        
        # Attribution claim
        "The President said the infrastructure bill will create 2 million jobs",
        
        # Historical claim
        "The last government shutdown was in 2019",
        
        # Complex claim
        "Healthcare costs have risen faster than wages for the past decade"
    ]
    
    print(f"\n{'='*60}")
    print("Testing Various Types of Claims")
    print(f"{'='*60}\n")
    
    for claim in test_claims:
        print(f"\n{'='*60}")
        print(f"Claim: {claim}")
        print(f"Type: {get_claim_type(claim)}")
        print(f"{'='*60}\n")
        
        result = await orchestrator.verify_claim(claim)
        
        print("Assessment:")
        print("-" * 40)
        print(result)
        print("-" * 40)
        
        # Add a small delay between claims to avoid rate limiting
        await asyncio.sleep(2)


def get_claim_type(claim: str) -> str:
    """Simple heuristic to categorize claim type."""
    claim_lower = claim.lower()
    
    if any(word in claim_lower for word in ["percent", "%", "grew", "rate", "gdp"]):
        return "Statistical"
    elif any(word in claim_lower for word in ["lowest", "highest", "most", "least", "than"]):
        return "Comparative"
    elif any(word in claim_lower for word in ["said", "stated", "announced", "according"]):
        return "Attribution"
    elif any(word in claim_lower for word in ["last", "was in", "enacted", "passed"]):
        return "Historical"
    else:
        return "General"


async def main():
    """Main function to run examples."""
    
    # Load environment variables
    load_dotenv()
    
    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY not found in environment variables")
        print("Please create a .env file with your Anthropic API key")
        return
    
    print("\n" + "="*60)
    print("CLAIM VERIFICATION SYSTEM - DEMO")
    print("="*60)
    
    # Run examples
    print("\n1. Single Claim Verification")
    await verify_single_claim()
    
    print("\n\n2. Parallel Claim Verification")
    await verify_multiple_claims()
    
    # Uncomment to test various claim types
    # print("\n\n3. Various Claim Types")
    # await test_with_various_claims()


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
