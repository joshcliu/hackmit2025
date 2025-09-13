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

    @validator("end_s")
    def _end_after_start(cls, v, values):  # type: ignore[override]
        start = values.get("start_s")
        if start is not None and v < start:
            raise ValueError("end_s must be >= start_s")
        return v


class ExtractionOutput(BaseModel):
    """Output wrapper for extracted claims."""

    claims: List[ClaimMinimal] = Field(
        default_factory=list,
        description="List of extracted claims from the text"
    )
    notes: Optional[str] = Field(
        default=None,
        description="Optional notes from the extractor (e.g., heuristics applied, extraction confidence)",
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

4. Handle timestamps:
   - If timestamps are provided in the text, use them for start_s and end_s
   - If not provided, set both to 0.0 (the caller will handle this)
   - Ensure end_s >= start_s"""),
            ("user", """Video ID: {video_id}

Text chunk from transcript:
\"\"\"
{chunk}
\"\"\"

Extract all verifiable claims from this text chunk. Return them as structured output with:
- claims: List of atomic, verifiable claims with video_id, timestamps, and claim_text""")
        ])

    async def aextract(self, video_id: str, chunk: str) -> ExtractionOutput:
        """Async extraction using the chain with structured output."""
        try:
            # Invoke the chain with the video_id and chunk
            result = await self.chain.ainvoke({"video_id": video_id, "chunk": chunk})
            
            # The structured model should return an ExtractionOutput directly
            if isinstance(result, ExtractionOutput):
                return result
            
            # Fallback: return empty result if something unexpected happens
            return ExtractionOutput(
                claims=[],
                notes="Failed to extract structured output from model response"
            )
            
        except Exception as e:
            # Return empty result with error note
            return ExtractionOutput(
                claims=[],
                notes=f"Extraction failed: {str(e)}"
            )

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
