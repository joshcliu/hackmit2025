"""
Claim extraction agent (Claude Sonnet 4) that takes a chunk of text and
returns structured, minimal claims suitable for verification.

Minimal claim schema matches README's ClaimForVerification:
- video_id: str
- start_s: float
- end_s: float
- claim_text: str

This mirrors the style and dependencies used in claim_verification/base_agent.py
but focuses on extraction rather than verification.
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

    claims: List[ClaimMinimal] = Field(default_factory=list)
    notes: Optional[str] = Field(
        default=None,
        description="Optional notes from the extractor (e.g., heuristics applied)",
    )


class ClaimExtractionAgent:
    """Agent that extracts minimal claims from text using Claude Sonnet 4."""

    def __init__(self, model: Optional[ChatAnthropic] = None):
        # Default to Claude 3.7 Sonnet (or latest Sonnet-4) if not provided
        # Update model name as needed depending on availability in your environment
        self.model = model or ChatAnthropic(model="claude-3-7-sonnet-2025-06-20")
        self.prompt = self._build_prompt()

    def _build_prompt(self) -> ChatPromptTemplate:
        """Create prompt instructing the model to output JSON ONLY with minimal claims.

        The model is asked to:
        - Identify verifiable claims (skip subjective/personal preferences).
        - Provide start/end seconds when known; otherwise approximate or set to null.
        - Return a JSON object with a `claims` array only.
        """
        system = (
            "You are a precise claim extraction engine.\n"
            "Given a chunk of transcript text from a political video, identify atomic,\n"
            "externally verifiable claims. Ignore subjective statements (e.g., 'I love my family').\n"
            "Each claim should be a minimal, self-contained statement suitable for verification.\n"
            "Output strictly in JSON with a top-level `claims` array. No extra commentary.\n"
        )

        user = (
            "Video ID: {video_id}\n"
            "Text chunk (may contain multiple caption snippets; timestamps are optional in the text):\n"
            '"""\n{chunk}\n"""\n\n'
            "Rules:\n"
            "- Use `claim_text` to capture the atomic statement only.\n"
            "- If you can infer approximate start/end seconds from the chunk (e.g., provided), include them;\n"
            "  otherwise set them to 0 and 0 (caller may fill later).\n"
            "- Only include externally verifiable factual statements (statistics, events, properties, attributions).\n"
            "- Return valid JSON with shape: {{\"claims\": [{{\"video_id\": str, \"start_s\": float, \"end_s\": float, \"claim_text\": str}}...]}}\n"
        )

        return ChatPromptTemplate.from_messages([
            ("system", system),
            ("user", user),
        ])

    async def aextract(self, video_id: str, chunk: str) -> ExtractionOutput:
        """Async extraction entrypoint."""
        chain = self.prompt | self.model
        result = await chain.ainvoke({"video_id": video_id, "chunk": chunk})

        content = getattr(result, "content", None) or "{}"
        # LangChain may return a list of messages; ensure string
        if isinstance(content, list):
            content = "\n".join([getattr(c, "content", "") if hasattr(c, "content") else str(c) for c in content])

        # Parse JSON safely
        import json

        try:
            data = json.loads(content)
        except Exception:
            # Attempt to extract JSON substring
            import re

            match = re.search(r"\{[\s\S]*\}$", content)
            if match:
                data = json.loads(match.group(0))
            else:
                data = {"claims": []}

        claims_in = data.get("claims", []) or []
        claims: List[ClaimMinimal] = []
        for c in claims_in:
            try:
                claims.append(
                    ClaimMinimal(
                        video_id=c.get("video_id", video_id),
                        start_s=float(c.get("start_s", 0) or 0),
                        end_s=float(c.get("end_s", 0) or 0),
                        claim_text=(c.get("claim_text", "") or "").strip(),
                    )
                )
            except Exception:
                # Skip malformed entries
                continue

        return ExtractionOutput(claims=claims)

    def extract(self, video_id: str, chunk: str) -> ExtractionOutput:
        """Sync wrapper for convenience (runs the underlying async call)."""
        import asyncio

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if loop.is_running():  # In notebooks or async contexts, run nested
            return asyncio.run(self.aextract(video_id, chunk))
        else:
            return loop.run_until_complete(self.aextract(video_id, chunk))
