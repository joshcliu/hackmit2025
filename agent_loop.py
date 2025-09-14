"""
Main orchestration loop that processes video transcripts end-to-end:
1. Chunks transcript into N parts
2. Creates N parallel extraction agents to extract claims from each chunk
3. Creates C_i parallel verification agents for each extracted claim
4. Outputs final results

Uses agents from agents/claim_extraction/ and agents/claim_verification/ packages.
"""
import asyncio
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import json
from datetime import datetime

# Import extraction agent
from agents.claim_extraction import ClaimExtractionAgent, ClaimMinimal, ExtractionOutput

# Import verification orchestrator
from agents.claim_verification.orchestrator import ClaimVerificationOrchestrator

# Import video metadata utilities
from video_metadata import get_video_metadata, format_video_context, VideoMetadata

# Import summary agent
from summary_agent import SummaryAgent, format_summary_context, transcript_to_text


@dataclass
class TranscriptChunk:
    """Represents a chunk of transcript for processing."""
    chunk_id: int
    start_s: float
    end_s: float
    text: str
    video_id: str


@dataclass
class VerifiedClaim:
    """Final output combining extracted claim with verification result."""
    claim: ClaimMinimal
    verification_result: str
    processing_time_s: float
    chunk_id: int


class AgentLoop:
    """Main orchestrator for the full extraction + verification pipeline."""
    
    def __init__(self, 
                 anthropic_api_key: Optional[str] = None,
                 chunk_size_seconds: float = 30.0,
                 max_parallel_extractions: int = 5,
                 max_parallel_verifications: int = 10):
        """
        Initialize the agent loop.
        
        Args:
            anthropic_api_key: API key for Anthropic (if None, uses env var)
            chunk_size_seconds: Target size for transcript chunks
            max_parallel_extractions: Max concurrent extraction agents
            max_parallel_verifications: Max concurrent verification agents
        """
        self.anthropic_api_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY must be provided or set in environment")
            
        self.chunk_size_seconds = chunk_size_seconds
        self.max_parallel_extractions = max_parallel_extractions
        self.max_parallel_verifications = max_parallel_verifications
        
        # Initialize agents
        self.extraction_agent = ClaimExtractionAgent()
        self.verification_orchestrator = ClaimVerificationOrchestrator(
            anthropic_api_key=self.anthropic_api_key
        )
        self.summary_agent = SummaryAgent()
    
    def chunk_transcript(self, transcript_raw: List[Dict[str, Any]], video_id: str) -> List[TranscriptChunk]:
        """
        Chunk transcript into segments based on time duration.
        
        Args:
            transcript_raw: Raw transcript from youtube-transcript-api (list of dicts with text, start, duration)
            video_id: YouTube video ID
            
        Returns:
            List of transcript chunks
        """
        chunks = []
        current_chunk_text = []
        current_start = None
        current_end = None
        chunk_id = 0
        
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
                current_end = end
                current_chunk_text = [text]
                continue
            
            # Check if adding this item would exceed chunk size
            potential_duration = end - current_start
            
            if potential_duration > self.chunk_size_seconds and current_chunk_text:
                # Finalize current chunk
                chunks.append(TranscriptChunk(
                    chunk_id=chunk_id,
                    start_s=current_start,
                    end_s=current_end,
                    text=" ".join(current_chunk_text),
                    video_id=video_id
                ))
                
                # Start new chunk
                chunk_id += 1
                current_start = start
                current_end = end
                current_chunk_text = [text]
            else:
                # Add to current chunk
                current_chunk_text.append(text)
                current_end = max(current_end, end)
        
        # Add final chunk if it has content
        if current_chunk_text and current_start is not None:
            chunks.append(TranscriptChunk(
                chunk_id=chunk_id,
                start_s=current_start,
                end_s=current_end,
                text=" ".join(current_chunk_text),
                video_id=video_id
            ))
        
        return chunks
    
    async def extract_claims_from_chunk(self, chunk: TranscriptChunk, video_context: str = "", summary_context: str = "") -> List[ClaimMinimal]:
        """Extract claims from a single chunk."""
        try:
            result = await self.extraction_agent.aextract(
                video_id=chunk.video_id,
                chunk=chunk.text,
                video_context=video_context,
                summary_context=summary_context
            )
            
            # Update timing info for extracted claims if they don't have it
            claims = []
            for claim in result.claims:
                if claim.start_s == 0.0 and claim.end_s == 0.0:
                    # Use chunk timing as fallback
                    claim.start_s = chunk.start_s
                    claim.end_s = chunk.end_s
                claims.append(claim)
            
            return claims
            
        except Exception as e:
            print(f"Error extracting claims from chunk {chunk.chunk_id}: {e}")
            return []
    
    async def verify_claim(self, claim: ClaimMinimal, chunk_id: int, video_context: str = "", summary_context: str = "") -> VerifiedClaim:
        """Verify a single claim."""
        start_time = asyncio.get_event_loop().time()
        
        try:
            verification_result = await self.verification_orchestrator.verify_claim(claim.claim_text, video_context, summary_context)
            processing_time = asyncio.get_event_loop().time() - start_time
            
            return VerifiedClaim(
                claim=claim,
                verification_result=verification_result,
                processing_time_s=processing_time,
                chunk_id=chunk_id
            )
            
        except Exception as e:
            processing_time = asyncio.get_event_loop().time() - start_time
            return VerifiedClaim(
                claim=claim,
                verification_result=f"Verification failed: {str(e)}",
                processing_time_s=processing_time,
                chunk_id=chunk_id
            )
    
    async def process_transcript(self, transcript_raw: List[Dict[str, Any]], video_id: str) -> List[VerifiedClaim]:
        """
        Process entire transcript: chunk → extract → verify.
        
        Args:
            transcript_raw: Raw transcript from youtube-transcript-api
            video_id: YouTube video ID
            
        Returns:
            List of verified claims with results
        """
        print(f"Processing transcript for video {video_id}")
        
        # Step 0: Get video metadata for context
        try:
            video_metadata = get_video_metadata(video_id)
            video_context = format_video_context(video_metadata)
            print(f"Retrieved video metadata: {video_metadata.title} (published {video_metadata.publish_date.strftime('%Y-%m-%d')})")
        except Exception as e:
            print(f"Warning: Could not fetch video metadata: {e}")
            video_context = ""
        
        # Step 0.5: Generate video summary for context
        try:
            transcript_text = transcript_to_text(transcript_raw)
            video_summary = await self.summary_agent.asummarize(video_id, transcript_text)
            summary_context = format_summary_context(video_summary, video_id)
            print(f"Generated video summary: {video_summary.summary}")
        except Exception as e:
            print(f"Warning: Could not generate video summary: {e}")
            summary_context = ""
        
        # Step 1: Chunk transcript
        chunks = self.chunk_transcript(transcript_raw, video_id)
        print(f"Created {len(chunks)} chunks (target: {self.chunk_size_seconds}s each)")
        
        # Step 2: Extract claims from all chunks in parallel (with concurrency limit)
        print("Extracting claims from chunks...")
        semaphore_extract = asyncio.Semaphore(self.max_parallel_extractions)
        
        async def extract_with_semaphore(chunk: TranscriptChunk):
            async with semaphore_extract:
                return await self.extract_claims_from_chunk(chunk, video_context, summary_context), chunk.chunk_id
        
        extraction_tasks = [extract_with_semaphore(chunk) for chunk in chunks]
        extraction_results = await asyncio.gather(*extraction_tasks, return_exceptions=True)
        
        # Collect all claims
        all_claims = []
        total_claims_by_chunk = {}
        
        for i, result in enumerate(extraction_results):
            if isinstance(result, Exception):
                print(f"Chunk {i} extraction failed: {result}")
                total_claims_by_chunk[i] = 0
                continue
                
            claims, chunk_id = result
            total_claims_by_chunk[chunk_id] = len(claims)
            
            for claim in claims:
                all_claims.append((claim, chunk_id))
        
        print(f"Extracted {len(all_claims)} total claims from {len(chunks)} chunks")
        for chunk_id, count in total_claims_by_chunk.items():
            print(f"  Chunk {chunk_id}: {count} claims")
        
        if not all_claims:
            print("No claims extracted, stopping pipeline")
            return []
        
        # Step 3: Verify all claims in parallel (with concurrency limit)
        print("Verifying claims...")
        semaphore_verify = asyncio.Semaphore(self.max_parallel_verifications)
        
        async def verify_with_semaphore(claim_and_chunk):
            claim, chunk_id = claim_and_chunk
            async with semaphore_verify:
                return await self.verify_claim(claim, chunk_id, video_context, summary_context)
        
        verification_tasks = [verify_with_semaphore(claim_and_chunk) for claim_and_chunk in all_claims]
        verified_claims = await asyncio.gather(*verification_tasks, return_exceptions=True)
        
        # Filter out exceptions
        final_results = []
        for result in verified_claims:
            if isinstance(result, Exception):
                print(f"Verification failed: {result}")
                continue
            final_results.append(result)
        
        print(f"Successfully verified {len(final_results)} claims")
        return final_results
    
    def save_results(self, results: List[VerifiedClaim], output_file: str):
        """Save results to JSON file."""
        output_data = {
            "timestamp": datetime.now().isoformat(),
            "total_claims": len(results),
            "results": []
        }
        
        for result in results:
            output_data["results"].append({
                "claim": {
                    "video_id": result.claim.video_id,
                    "start_s": result.claim.start_s,
                    "end_s": result.claim.end_s,
                    "claim_text": result.claim.claim_text
                },
                "verification_result": result.verification_result,
                "processing_time_s": result.processing_time_s,
                "chunk_id": result.chunk_id
            })
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"Results saved to {output_file}")


async def main():
    """Example usage of the agent loop."""
    # Example: Load transcript from youtube-transcript-api
    from youtube_transcript_api import YouTubeTranscriptApi
    
    video_id = "4dOgWZsDB6Q"  # Example video ID
    
    try:
        # Fetch transcript
        ytt_api = YouTubeTranscriptApi()
        fetched = ytt_api.fetch(video_id)
        transcript_raw = fetched.to_raw_data()
        
        print(f"Loaded transcript with {len(transcript_raw)} segments")
        
        # Initialize and run agent loop
        loop = AgentLoop(
            chunk_size_seconds=60.0,  # 1-minute chunks
            max_parallel_extractions=3,  # Conservative for API limits
            max_parallel_verifications=5
        )
        
        results = await loop.process_transcript(transcript_raw, video_id)
        
        # Save results
        output_file = f"results_{video_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        loop.save_results(results, output_file)
        
        # Print summary
        print(f"\nPipeline completed successfully!")
        print(f"Total verified claims: {len(results)}")
        if results:
            avg_processing_time = sum(r.processing_time_s for r in results) / len(results)
            print(f"Average verification time: {avg_processing_time:.2f}s per claim")
        
    except Exception as e:
        print(f"Pipeline failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
