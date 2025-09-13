"""
Claim extraction agent (Claude Sonnet 4) that takes a chunk of text and
returns structured, minimal claims suitable for verification.

Minimal claim schema matches README's ClaimForVerification:
- video_id: str
- start_s: float
- end_s: float
- claim_text: str

Uses a react_agent pattern with structured output via Pydantic models.
"""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, validator
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate


class ClaimMinimal(BaseModel):
    """Minimal claim payload produced by the extractor and consumed by the verifier."""

    video_id: str = Field(..., description="YouTube video ID")
    start_s: float = Field(..., description="Start time (seconds) of the utterance containing the claim")
    end_s: float = Field(..., description="End time (seconds) of the utterance containing the claim")
    claim_text: str = Field(..., description="Atomic, normalized claim text (what to verify)")
    speaker: str = Field(..., description="Name or identifier of the person who made the claim")
    importance_score: float = Field(..., description="Importance score from 0.0 to 1.0 indicating verification priority")

    @validator("end_s")
    def _end_after_start(cls, v, values):  # type: ignore[override]
        start = values.get("start_s")
        if start is not None and v < start:
            raise ValueError("end_s must be >= start_s")
        return v

    @validator("importance_score")
    def _importance_in_range(cls, v):  # type: ignore[override]
        if not 0.0 <= v <= 1.0:
            raise ValueError("importance_score must be between 0.0 and 1.0")
        return v


class ExtractionOutput(BaseModel):
    """Output wrapper for extracted claims."""

    claims: List[ClaimMinimal] = Field(
        default_factory=list,
        description="List of extracted claims from the text"
    )


class ClaimExtractionAgent:
    """Agent that extracts minimal claims from text using Claude Sonnet 4 with structured output."""

    def __init__(self, model: Optional[ChatAnthropic] = None):
        # Default to Claude 4 Sonnet if not provided
        self.model = model or ChatAnthropic(model="claude-4-sonnet-20250514")
        
        # Configure model with structured output
        self.structured_model = self.model.with_structured_output(ExtractionOutput)
        
        # Build the prompt template
        self.prompt = self._build_prompt()
        
        # Create the extraction chain
        self.chain = self.prompt | self.structured_model

    def _build_prompt(self) -> ChatPromptTemplate:
        """Create prompt for claim extraction with structured output.

        The model is asked to:
        - Identify verifiable claims (skip subjective/personal preferences).
        - Provide start/end seconds when known; otherwise approximate or set to 0.
        - Return structured output as ExtractionOutput model.
        """
        return ChatPromptTemplate.from_messages([
            ("system", """You are a precise claim extraction engine for political fact-checking.

Your task is to analyze transcript text from a political video and extract atomic, externally verifiable claims.

Guidelines for extraction:
1. Focus on FACTUAL claims that can be verified:
   - Statistics and numbers (e.g., "unemployment is at 3.5%")
   - Historical events and dates (e.g., "the bill was passed in 2021")
   - Specific attributions (e.g., "Senator X voted for Y")
   - Policy positions and promises (e.g., "I will increase funding by $1B")
   - Comparisons with concrete metrics (e.g., "crime is higher than last year")

2. SKIP subjective or opinion statements:
   - Personal feelings (e.g., "I love my family")
   - Value judgments (e.g., "this is the best policy")
   - Predictions without specific metrics (e.g., "things will get better")
   - Vague statements (e.g., "we need to do more")

3. Create ATOMIC claims:
   - Each claim should be self-contained and independently verifiable
   - Break compound statements into separate claims
   - Include necessary context within the claim text
   - IGNORE repeated or duplicate claims - only extract each unique claim once

4. Identify the speaker:
   - The ">>" symbol in transcript lines indicates a change in speaker
   - Determine who made each claim from context and speaker changes
   - Use names, titles, or roles as appropriate
   - If unclear from transcript, use "Unknown"

5. Handle timestamps:
   - Parse timestamps from the transcript format: "134 [186.82s + 2.90s]" means start=186.82s, end=189.72s
   - For each claim, identify which transcript lines it spans and use those timestamps
   - If timestamps are unclear, estimate based on surrounding context
   - If no timestamps available, set both to 0.0
   - Ensure end_s >= start_s

6. Assign importance scores (0.0 to 1.0) based on verification priority:
   
   HIGH IMPORTANCE (0.8-1.0):
   - Disputed current/historical claims that can be fact-checked: "Current inflation is probably the worst in the nation's history"
   - Controversial but verifiable statistics: "The Biden administration has allowed millions of criminals to enter the country"
   - Disputed causation claims about past events: "My policies caused unemployment to drop to 3.5%"
   - Controversial historical interpretations: "The 2020 election had widespread irregularities"
   - Specific personal anecdotes used as evidence: "A person named Amanda in Texas appeared on stage in Chicago and nearly bled out, having sepsis twice because she couldn't get medical care"
   
   MEDIUM IMPORTANCE (0.4-0.7):
   - Simple factual statements that can be easily verified: "Donald Trump and Kamala Harris are currently tied in polling"
   - Basic historical facts: "Roe vs. Wade was the law of the land for 52 years"
   - Straightforward policy positions: "I will cut taxes by $2000 per family"
   - General policy positions: "I support universal healthcare"
   - Broad historical references: "We rebuilt our military"
   - Measurable outcomes without disputed causation: "Crime decreased by 15% in our city"
   
   LOW IMPORTANCE (0.0-0.3):
   - Obvious factual statements: "J.D. Vance is Donald Trump's running mate"
   - Future predictions that cannot be verified: "My opponent's plan will result in $5 trillion to America's deficit"
   - Unverifiable policy impact claims: "The Inflation Reduction Act will save families $2000 per year"
   - Pure opinion/subjective statements: "This is the greatest economy ever"
   - Personal feelings: "I love my family"
   - Vague promises: "We will make things better"

   Reserve HIGH priority for claims about current or past events that are factual but disputed. Assign LOW priority to future predictions and unverifiable policy outcomes."""),
            ("user", """Video ID: {video_id}

Text chunk from transcript (format: "line_number [start_time + duration] TEXT"):
\"\"\"
{chunk}
\"\"\"

Extract all verifiable claims from this text chunk. Return them as structured output with:
- claims: List of atomic, verifiable claims with video_id, timestamps, claim_text, speaker, and importance_score

IMPORTANT: 
- Parse timestamps carefully from the transcript format. For example: "134 [186.82s + 2.90s] >> SO I WAS RAISED AS A" means start_s=186.82, end_s=189.72
- The ">>" symbol indicates a change in speaker - use this to identify who is making each claim
- If a claim spans multiple lines, use the start of the first line and end of the last line

For each claim, identify the speaker and assign an importance_score from 0.0 to 1.0 based on the guidelines above.""")
        ])

    async def aextract(self, video_id: str, chunk: str) -> ExtractionOutput:
        """Async extraction using the chain with structured output."""
        try:
            # Invoke the chain with the video_id and chunk
            result = await self.chain.ainvoke({"video_id": video_id, "chunk": chunk})
            
            # The structured model should return an ExtractionOutput directly
            if isinstance(result, ExtractionOutput):
                # Deduplicate claims based on claim text (case-insensitive)
                seen_claims = set()
                unique_claims = []
                
                for claim in result.claims:
                    claim_key = claim.claim_text.lower().strip()
                    if claim_key not in seen_claims:
                        seen_claims.add(claim_key)
                        unique_claims.append(claim)
                
                return ExtractionOutput(claims=unique_claims)
            
            # Fallback: return empty result if something unexpected happens
            return ExtractionOutput(claims=[])
            
        except Exception as e:
            # Return empty result on error
            return ExtractionOutput(claims=[])

    def extract(self, video_id: str, chunk: str) -> ExtractionOutput:
        """Sync wrapper for convenience (runs the underlying async call)."""
        import asyncio

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if loop.is_running():  # In notebooks or async contexts
            # Use nest_asyncio for nested event loops
            import nest_asyncio
            nest_asyncio.apply()
            return asyncio.run(self.aextract(video_id, chunk))
        else:
            return loop.run_until_complete(self.aextract(video_id, chunk))
