"""
Test script that fetches a YouTube video transcript and extracts all claims from it.
Similar to experiments/test_youtube_transcript_api.py but focused on claim extraction.

Usage:
  python claim_extraction/test_video_claims.py VIDEO_ID
  python claim_extraction/test_video_claims.py 4dOgWZsDB6Q --chunk-size 60
"""
import argparse
import asyncio
import json
import os
import sys
from typing import List, Dict, Any

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi

from agent import ClaimExtractionAgent, ClaimMinimal

# Load environment variables
load_dotenv()


def fetch_transcript_raw(video_id: str) -> List[Dict[str, Any]]:
    """Fetch transcript using youtube-transcript-api."""
    try:
        ytt_api = YouTubeTranscriptApi()
        fetched = ytt_api.fetch(video_id)
        return fetched.to_raw_data()
    except Exception as e:
        raise SystemExit(f"Error fetching transcript: {e}")


def chunk_transcript(transcript_raw: List[Dict[str, Any]], chunk_size_seconds: float = 30.0) -> List[str]:
    """
    Chunk transcript into time-based segments for processing.
    
    Args:
        transcript_raw: Raw transcript from youtube-transcript-api
        chunk_size_seconds: Target size for each chunk in seconds
        
    Returns:
        List of text chunks
    """
    chunks = []
    current_chunk_text = []
    current_start = None
    
    for item in transcript_raw:
        start = item.get("start", 0.0)
        duration = item.get("duration", 0.0)
        end = start + duration
        text = item.get("text", "").strip()
        
        if not text:
            continue
            
        # Initialize first chunk
        if current_start is None:
            current_start = start
            current_chunk_text = [text]
            continue
        
        # Check if adding this item would exceed chunk size
        potential_duration = end - current_start
        
        if potential_duration > chunk_size_seconds and current_chunk_text:
            # Finalize current chunk
            chunks.append(" ".join(current_chunk_text))
            
            # Start new chunk
            current_start = start
            current_chunk_text = [text]
        else:
            # Add to current chunk
            current_chunk_text.append(text)
    
    # Add final chunk if it has content
    if current_chunk_text:
        chunks.append(" ".join(current_chunk_text))
    
    return chunks


async def extract_claims_from_video(video_id: str, chunk_size_seconds: float = 30.0, max_parallel: int = 3) -> List[ClaimMinimal]:
    """
    Extract all claims from a video transcript using parallel processing.
    
    Args:
        video_id: YouTube video ID
        chunk_size_seconds: Size of chunks to process
        max_parallel: Maximum number of parallel extraction tasks
        
    Returns:
        List of all extracted claims
    """
    print(f"Fetching transcript for video {video_id}...")
    transcript_raw = fetch_transcript_raw(video_id)
    print(f"Retrieved {len(transcript_raw)} transcript segments")
    
    print(f"Chunking transcript (target: {chunk_size_seconds}s per chunk)...")
    chunks = chunk_transcript(transcript_raw, chunk_size_seconds)
    print(f"Created {len(chunks)} chunks")
    
    # Initialize extraction agent
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit("ANTHROPIC_API_KEY environment variable is required")
    
    agent = ClaimExtractionAgent()
    
    print(f"Extracting claims from chunks (max {max_parallel} parallel)...")
    
    # Create semaphore to limit concurrent extractions
    semaphore = asyncio.Semaphore(max_parallel)
    
    async def extract_from_chunk(chunk_id: int, chunk_text: str):
        """Extract claims from a single chunk with semaphore control."""
        async with semaphore:
            try:
                print(f"Processing chunk {chunk_id+1}/{len(chunks)}...")
                result = await agent.aextract(video_id=video_id, chunk=chunk_text)
                chunk_claims = result.claims
                print(f"  Extracted {len(chunk_claims)} claims from chunk {chunk_id+1}")
                return chunk_claims, chunk_id
            except Exception as e:
                print(f"  Error processing chunk {chunk_id+1}: {e}")
                return [], chunk_id
    
    # Create tasks for all chunks
    extraction_tasks = [
        extract_from_chunk(i, chunk) 
        for i, chunk in enumerate(chunks)
    ]
    
    # Run all extractions in parallel
    results = await asyncio.gather(*extraction_tasks, return_exceptions=True)
    
    # Collect all claims
    all_claims = []
    successful_chunks = 0
    
    for result in results:
        if isinstance(result, Exception):
            print(f"Chunk extraction failed: {result}")
            continue
            
        chunk_claims, chunk_id = result
        all_claims.extend(chunk_claims)
        if chunk_claims:
            successful_chunks += 1
    
    print(f"Completed extraction from {successful_chunks}/{len(chunks)} chunks")
    return all_claims


def print_claims_summary(claims: List[ClaimMinimal], video_id: str):
    """Print a summary of extracted claims."""
    print(f"\n{'='*60}")
    print(f"CLAIM EXTRACTION RESULTS - VIDEO {video_id}")
    print(f"{'='*60}")
    print(f"Total claims extracted: {len(claims)}")
    
    if not claims:
        print("No claims found in this video.")
        return
    
    print(f"\nExtracted Claims:")
    print("-" * 40)
    
    for i, claim in enumerate(claims, 1):
        print(f"\nClaim {i}:")
        print(f"  Time: {claim.start_s:.1f}s - {claim.end_s:.1f}s")
        print(f"  Text: {claim.claim_text}")
    
    # Basic statistics
    if claims:
        avg_duration = sum(c.end_s - c.start_s for c in claims if c.end_s > c.start_s) / len(claims)
        print(f"\nStatistics:")
        print(f"  Average claim duration: {avg_duration:.1f}s")
        print(f"  Shortest claim: {min(len(c.claim_text) for c in claims)} characters")
        print(f"  Longest claim: {max(len(c.claim_text) for c in claims)} characters")


def save_claims_json(claims: List[ClaimMinimal], video_id: str, output_file: str):
    """Save claims to JSON file."""
    output_data = {
        "video_id": video_id,
        "total_claims": len(claims),
        "claims": [
            {
                "video_id": claim.video_id,
                "start_s": claim.start_s,
                "end_s": claim.end_s,
                "claim_text": claim.claim_text
            }
            for claim in claims
        ]
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\nClaims saved to: {output_file}")


async def main():
    """Main function to run the video claim extraction test."""
    parser = argparse.ArgumentParser(
        description="Extract all claims from a YouTube video transcript"
    )
    parser.add_argument("video_id", help="YouTube video ID (e.g., 4dOgWZsDB6Q)")
    parser.add_argument(
        "--chunk-size", 
        type=float, 
        default=30.0,
        help="Chunk size in seconds (default: 30.0)"
    )
    parser.add_argument(
        "--output",
        help="Output JSON file (default: claims_VIDEO_ID.json)"
    )
    
    args = parser.parse_args()
    
    try:
        # Extract claims
        claims = await extract_claims_from_video(args.video_id, args.chunk_size, max_parallel=10)
        
        # Print summary
        print_claims_summary(claims, args.video_id)
        
        # Save to file
        output_file = args.output or f"claims_{args.video_id}.json"
        save_claims_json(claims, args.video_id, output_file)
        
        print(f"\n✅ Claim extraction completed successfully!")
        
    except KeyboardInterrupt:
        print("\n⚠️ Extraction interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Extraction failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
