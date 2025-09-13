"""
Basic tests for the claim extraction agent.
Mirrors the structure of claim_verification/test_basic.py.
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
    """Test that claim extraction modules can be imported."""
    try:
        from agent import ClaimExtractionAgent, ClaimMinimal, ExtractionOutput  # noqa: F401
        print("✅ claim_extraction modules imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False


async def test_initialization():
    """Test that the extraction agent can be initialized."""
    try:
        from agent import ClaimExtractionAgent

        # Ensure there's some key in env so ChatAnthropic can initialize without error
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            print("⚠️  No ANTHROPIC_API_KEY found - setting test key for initialization")
            os.environ["ANTHROPIC_API_KEY"] = "test-key"

        agent = ClaimExtractionAgent()
        assert agent is not None

        print("✅ Extraction agent initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Initialization error: {e}")
        return False


async def test_simple_extraction():
    """Test extracting a simple claim (if a real API key is available)."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    # Heuristic: treat 'test-key' as placeholder and skip networked test
    if not api_key or api_key == "test-key":
        print("⚠️  Skipping extraction test - no real ANTHROPIC_API_KEY provided")
        return True

    try:
        from agent import ClaimExtractionAgent

        agent = ClaimExtractionAgent()
        chunk = (
            "134 [186.82s + 2.90s] >> SO I WAS RAISED AS A\n"
            "135 [188.89s + 2.70s] MIDDLE-CLASS KID.\n"
            "136 [189.82s + 4.14s] AND I AM ACTUALLY THE ONLY\n"
            "137 [191.69s + 3.34s] PERSON ON THIS STAGE WHO HAS A\n"
            "138 [194.06s + 2.57s] PLAN THAT IS ABOUT LIFTING UP\n"
            "139 [195.13s + 2.60s] THE MIDDLE CLASS AND WORKING\n"
            "140 [196.73s + 3.50s] PEOPLE OF AMERICA.\n"
            "141 [198.03s + 3.80s] I BELIEVE IN THE AMBITION, THE\n"
            "142 [200.33s + 2.84s] ASPIRATIONS, THE DREAMS OF THE\n"
            "143 [201.94s + 3.07s] AMERICAN PEOPLE.\n"
            "144 [203.27s + 2.80s] AND THAT IS WHY I IMAGINE AND\n"
            "145 [205.10s + 4.24s] HAVE ACTUALLY A PLAN TO BUILD\n"
            "146 [206.17s + 3.44s] WHAT I CALL AN OPPORTUNITY\n"
            "147 [209.44s + 1.10s] ECONOMY.\n"
            "148 [209.71s + 2.80s] BECAUSE HERE'S THE THING.\n"
            "149 [210.78s + 3.44s] WE KNOW THAT WE HAVE A SHORTAGE\n"
            "150 [212.88s + 4.17s] OF HOMES AND HOUSING, AND THE\n"
            "151 [214.31s + 3.64s] COST OF HOUSING IS TOO EXPENSIVE\n"
            "152 [217.15s + 4.07s] FOR FAR TOO MANY PEOPLE.\n"
            "153 [218.18s + 4.47s] WE KNOW THAT YOUNG FAMILIES NEED\n"
            "154 [221.32s + 3.70s] SUPPORT TO RAISE THEIR CHILDREN.\n"
            "155 [222.75s + 4.07s] AND I INTEND ON EXTENDING A TAX\n"
            "156 [225.12s + 3.94s] CUT FOR THOSE FAMILIES OF\n"
            "157 [226.93s + 3.14s] $6,000, WHICH IS THE LARGEST\n"
            "158 [229.16s + 2.00s] CHILD TAX CREDIT THAT WE HAVE\n"
            "159 [230.16s + 2.90s] GIVEN IN A LONG TIME.\n"
            "160 [231.53s + 3.94s] SO THAT THOSE YOUNG FAMILIES CAN\n"
            "161 [233.17s + 5.64s] AFFORD TO BUY A CRIB, BUY A CAR\n"
            "162 [235.57s + 3.50s] SEAT, BUY CLOTHES FOR THEIR\n"
            "163 [238.91s + 1.94s] CHILDREN.\n"
        )
        video_id = "TEST_VIDEO_ID"

        out = await agent.aextract(video_id=video_id, chunk=chunk)

        if out and getattr(out, "claims", None):
            print(f"✅ Claim extraction completed; extracted {len(out.claims)} claims:")
            
            # Print all extracted claims
            for i, c in enumerate(out.claims, 1):
                # Basic structural validation
                ok = (
                    isinstance(c.video_id, str)
                    and isinstance(c.start_s, float)
                    and isinstance(c.end_s, float)
                    and isinstance(c.claim_text, str)
                    and len(c.claim_text) > 0
                )
                
                status = "✅" if ok else "❌"
                print(f"   {status} Claim {i}: video_id={c.video_id}, start={c.start_s}, end={c.end_s}")
                print(f"      claim_text: '{c.claim_text}'")
            
            return True

        print("❌ Extraction returned no claims or malformed output")
        return False

    except Exception as e:
        print(f"❌ Extraction error: {e}")
        return False


async def main():
    """Run all tests for claim extraction."""
    print("\n" + "=" * 60)
    print("CLAIM EXTRACTION - BASIC TESTS")
    print("=" * 60 + "\n")

    tests = [
        ("Import Test", test_import),
        ("Initialization Test", test_initialization),
        ("Simple Extraction Test", test_simple_extraction),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 40)
        result = await test_func()
        results.append(result)

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

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
