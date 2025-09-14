"""
Simple summary agent that generates 2-3 sentence summaries of video transcripts.
This summary provides context to all other agents in the pipeline.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate


class VideoSummary(BaseModel):
    """Container for video transcript summary."""
    
    summary: str = Field(..., description="2-3 sentence summary of the video transcript")
    key_topics: List[str] = Field(default_factory=list, description="Main topics discussed in the video")
    speakers: List[str] = Field(default_factory=list, description="Identified speakers in the video")


class SummaryAgent:
    """Agent that creates concise summaries of video transcripts for context."""
    
    def __init__(self, model: Optional[ChatAnthropic] = None):
        # Default to Claude 3.5 Sonnet for efficiency
        self.model = model or ChatAnthropic(model="claude-3-5-sonnet-20241022")
        
        # Configure model with structured output
        self.structured_model = self.model.with_structured_output(VideoSummary)
        
        # Build the prompt template
        self.prompt = self._build_prompt()
        
        # Create the summary chain
        self.chain = self.prompt | self.structured_model
    
    def _build_prompt(self) -> ChatPromptTemplate:
        """Create prompt for generating video summaries."""
        return ChatPromptTemplate.from_messages([
            ("system", """You are a video transcript summarization agent. Your task is to create a concise 2-3 sentence summary of a video transcript that captures the main content and context.

Your summary should:
1. Be exactly 2-3 sentences long
2. Capture the main topic/theme of the video
3. Include key context that would help other agents understand what the video is about
4. Be neutral and factual, avoiding subjective language
5. Focus on the most important information discussed

Additionally, identify:
- Key topics: Main subjects or themes discussed (3-5 topics max)
- Speakers: Names or identifiers of people speaking (if identifiable from transcript)

The transcript may contain speaker changes indicated by ">>" symbols and timestamps in the format "[time + duration]"."""),
            ("user", """Video ID: {video_id}

Full transcript text:
\"\"\"
{transcript_text}
\"\"\"

Generate a 2-3 sentence summary that captures the main content and context of this video. Also identify the key topics and speakers.""")
        ])
    
    async def asummarize(self, video_id: str, transcript_text: str) -> VideoSummary:
        """Async summarization using the chain with structured output."""
        try:
            # Truncate transcript if too long (keep first ~8000 chars to stay within token limits)
            if len(transcript_text) > 8000:
                transcript_text = transcript_text[:8000] + "... [transcript truncated]"
            
            # Invoke the chain with the video_id and transcript
            result = await self.chain.ainvoke({
                "video_id": video_id, 
                "transcript_text": transcript_text
            })
            
            if isinstance(result, VideoSummary):
                return result
            
            # Fallback: return basic summary if something unexpected happens
            return VideoSummary(
                summary="Video transcript processed but summary generation failed.",
                key_topics=[],
                speakers=[]
            )
            
        except Exception as e:
            print(f"Error generating summary: {e}")
            # Return basic fallback summary on error
            return VideoSummary(
                summary="Video transcript could not be summarized due to processing error.",
                key_topics=[],
                speakers=[]
            )
    
    def summarize(self, video_id: str, transcript_text: str) -> VideoSummary:
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
            return asyncio.run(self.asummarize(video_id, transcript_text))
        else:
            return loop.run_until_complete(self.asummarize(video_id, transcript_text))


def format_summary_context(summary: VideoSummary, video_id: str) -> str:
    """Format video summary for use in agent prompts."""
    context = f"""VIDEO SUMMARY CONTEXT:
- Video ID: {video_id}
- Summary: {summary.summary}"""
    
    if summary.key_topics:
        context += f"\n- Key Topics: {', '.join(summary.key_topics)}"
    
    if summary.speakers:
        context += f"\n- Speakers: {', '.join(summary.speakers)}"
    
    context += "\n\nUse this summary to understand the overall context and content of the video when processing specific claims or segments."
    
    return context


def transcript_to_text(transcript_raw: List[Dict[str, Any]]) -> str:
    """Convert raw transcript data to plain text for summarization."""
    text_parts = []
    current_speaker = None
    
    for item in transcript_raw:
        text = item.get("text", "").strip()
        if not text:
            continue
        
        # Check for speaker changes (indicated by >> in some transcripts)
        if ">>" in text:
            # Extract speaker change
            parts = text.split(">>", 1)
            if len(parts) == 2:
                speaker_part = parts[0].strip()
                actual_text = parts[1].strip()
                if speaker_part != current_speaker:
                    current_speaker = speaker_part
                    text_parts.append(f"\n[Speaker: {speaker_part}] {actual_text}")
                else:
                    text_parts.append(actual_text)
            else:
                text_parts.append(text)
        else:
            text_parts.append(text)
    
    return " ".join(text_parts)
