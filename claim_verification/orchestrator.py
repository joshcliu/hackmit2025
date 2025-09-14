"""
Main orchestrator for claim verification system.
"""

import asyncio
from typing import List, Optional
from langchain_anthropic import ChatAnthropic
from pydantic import BaseModel, Field

from claim_verification.agents import (
    NewsSearcherAgent,
    AcademicSearcherAgent,
    FactCheckSearcherAgent,
    GovernmentDataAgent,
    TemporalConsistencyAgent
)
from claim_verification.base_agent import BaseVerificationAgent


class VerificationResult(BaseModel):
    """Structured output for claim verification."""
    verdict: str = Field(
        description="The final verdict: TRUE, FALSE, MISLEADING, PARTIALLY TRUE, or UNVERIFIABLE"
    )
    summary: str = Field(
        description="Detailed explanation of the verdict with key evidence and reasoning"
    )
    score: float = Field(
        description="Numerical score from 0-10 (0=definitely false, 5=uncertain, 10=definitely true)",
        ge=0,
        le=10
    )
    sources: List[str] = Field(
        description="List of credible sources used as citations with URLs when available"
    )


class OrchestratorAgent(BaseVerificationAgent):
    """Orchestrator that synthesizes results from all specialist agents."""
    
    def _create_agent(self):
        """Create ReAct agent for the orchestrator."""
        from langgraph.prebuilt import create_react_agent
        
        # Get the system prompt
        system_prompt = self.get_prompt()
        
        # Create agent without structured output binding to avoid tool conflicts
        return create_react_agent(
            model=self.model,
            tools=self.tools,
            response_format=VerificationResult,
            prompt=system_prompt
        )
    
    def get_prompt(self):
        """Return the synthesis-focused system prompt for the orchestrator."""
        return """You are the lead fact-checker synthesizing findings from multiple specialist verification agents.

Your role is to:
1. Carefully analyze all agent assessments
2. Identify points of agreement and conflict between agents
3. Use search and scraping tools to resolve ambiguities or gather additional context
4. Cross-validate sources across different agent findings
5. Produce a clear, comprehensive verdict

Critical considerations:
- Source credibility hierarchy: Government data > Academic papers > Established media > Fact-check sites > Blogs/social media
- Temporal consistency: Recent information supersedes older claims unless historical context is needed
- Consensus patterns: Strong agreement across agents increases confidence
- Contradiction handling: When agents disagree, dig deeper to understand why
- Context importance: Some claims may be technically true but misleading without context

Tools at your disposal:
- web_search: Search for additional verification information (DuckDuckGo or Tavily)
- scrape_page: Extract and analyze content from specific webpages

You must provide a structured response with:
1. verdict: Choose exactly one: TRUE, FALSE, MISLEADING, PARTIALLY TRUE, or UNVERIFIABLE
2. summary: Comprehensive yet concise explanation (3-4 sentences per paragraph max, max 3 paragraphs) synthesizing all findings, evidence, and reasoning
3. score: Rate 0-10 where 0=definitely false, 5=uncertain/mixed, 10=definitely true, on a decimal scale
4. sources: List the most credible sources with URLs when available

Remember: You're the final arbiter. Use the tools to resolve uncertainties and provide the most accurate assessment possible."""
        
    async def verify(self, claim: str, agent_results: List[str] = None, video_context: str = "") -> VerificationResult:
        """
        Override verify to synthesize agent findings.
        
        Args:
            claim: The claim being verified
            agent_results: List of findings from specialist agents
            video_context: Video metadata context for temporal verification
            
        Returns:
            Synthesized assessment with verdict and sources
        """
        if not agent_results:
            # If called without agent results, just do a direct verification
            # This shouldn't happen for the orchestrator, but handle it gracefully
            return VerificationResult(
                verdict="UNVERIFIABLE",
                summary="No agent results provided for synthesis.",
                score=5.0,
                sources=[]
            )
        
        # Format agent results for synthesis
        agent_summaries = self._format_agent_results(agent_results)
        
        # Create the synthesis request with video context
        context_section = f"\n\n=== VIDEO CONTEXT ===\n{video_context}\n" if video_context else ""
        
        synthesis_message = f"""CLAIM TO VERIFY: {claim}{context_section}

=== SPECIALIST AGENT FINDINGS ===

{agent_summaries}

=== YOUR TASK ===

Synthesize all agent findings into a comprehensive final assessment. Consider the video's publication date when evaluating temporal claims.

Steps to follow:
1. Analyze areas of agreement and contradiction between agents
2. Use search/scraping tools to resolve any ambiguities or verify conflicting information
3. Cross-reference sources mentioned by different agents
4. Consider the temporal context - evaluate claims based on information available at the video's publication date
5. Determine the most credible conclusion based on evidence quality
6. Provide a structured verdict with comprehensive reasoning

Provide your response as a structured output with these exact fields:
- verdict: Choose one: TRUE, FALSE, MISLEADING, PARTIALLY TRUE, or UNVERIFIABLE
- summary: Detailed assessment explaining your reasoning, key evidence, and important context
- score: Numerical rating from 0-10 (0=definitely false, 10=definitely true)
- sources: List of credible sources with URLs"""

        result = await self.agent.ainvoke({
            "messages": [("user", synthesis_message)]
        })

        if result.get("structured_response"):
            return result.get("structured_response")
        else:
            return VerificationResult(
                verdict="UNVERIFIABLE",
                summary="Unable to synthesize findings due to processing error.",
                score=5.0,
                sources=[]
            )
    
    def _format_agent_results(self, results: List[str]) -> str:
        """Format agent results for the synthesis prompt."""
        agent_names = [
            "News Verification Agent",
            "Academic Research Agent", 
            "Fact-Check Agent",
            "Government Data Agent",
            "Temporal Analysis Agent"
        ]
        
        formatted = []
        for name, result in zip(agent_names, results):
            if result and not result.startswith("Error") and not result.startswith("Verification failed"):
                formatted.append(f"### {name}:\n{result}\n")
        
        return "\n".join(formatted) if formatted else "No agent results available."


class ClaimVerificationOrchestrator:
    """
    Main orchestrator class for parallel claim verification.
    Designed to be called asynchronously for multiple claims.
    """
    
    def __init__(self, anthropic_api_key: str, composio_api_key: Optional[str] = None):
        """
        Initialize the orchestrator.
        
        Args:
            anthropic_api_key: API key for Claude
            composio_api_key: Optional API key for Composio (deprecated, use COMPOSIO_API_KEY env var)
        """
        # Initialize Claude 4 Sonnet model for orchestrator
        self.model = ChatAnthropic(
            api_key=anthropic_api_key,
            model="claude-4-sonnet-20250514"
        )
        
        # Initialize Claude Haiku model for agents (faster and cheaper)
        self.agent_model = ChatAnthropic(
            api_key=anthropic_api_key,
            model="claude-3-5-haiku-20241022"
        )
        
        # Initialize all agents with Haiku model
        self.news_agent = NewsSearcherAgent(self.agent_model)
        self.academic_agent = AcademicSearcherAgent(self.agent_model)
        self.fact_check_agent = FactCheckSearcherAgent(self.agent_model)
        self.gov_data_agent = GovernmentDataAgent(self.agent_model)
        self.temporal_agent = TemporalConsistencyAgent(self.agent_model)
        self.orchestrator = OrchestratorAgent(self.model)  # Orchestrator uses Sonnet
        
        # TODO: Add memory system for contradiction detection
        self.memory = None
        
    async def verify_claim(self, claim: str, video_context: str = "", summary_context: str = "") -> VerificationResult:
        """
        Verify a single atomic claim.
        
        Args:
            claim: The atomic claim to verify
            video_context: Video metadata context for temporal verification
            summary_context: Video summary context for better understanding
            
        Returns:
            Structured verification result with verdict, summary, score, and sources
        """
        print(f"Verifying claim: {claim}")
        
        # Combine video context and summary context
        combined_context = f"{video_context}\n\n{summary_context}".strip()
        
        # Spawn all agents in parallel with combined context
        agent_tasks = [
            self.news_agent.verify(claim, combined_context),
            self.academic_agent.verify(claim, combined_context),
            self.fact_check_agent.verify(claim, combined_context),
            self.gov_data_agent.verify(claim, combined_context),
            self.temporal_agent.verify(claim, combined_context)
        ]
        
        # Gather all results with error handling
        agent_results = []
        results = await asyncio.gather(*agent_tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Agent {i} failed: {result}")
                agent_results.append(f"Error: {str(result)}")
            else:
                agent_results.append(result)
        
        # Orchestrator synthesizes all findings
        print("Synthesizing agent findings...")
        final_assessment = await self.orchestrator.verify(
            claim=claim,
            agent_results=agent_results,
            video_context=combined_context
        )
        
        # TODO: Store in memory for future contradiction detection
        # if self.memory:
        #     self.memory.store_claim(claim, final_assessment)
        
        return final_assessment
    
    async def verify_claims_batch(self, claims: List[str]) -> List[VerificationResult]:
        """
        Verify multiple claims in parallel.
        
        Args:
            claims: List of claims to verify
            
        Returns:
            List of structured verification results
        """
        tasks = [self.verify_claim(claim) for claim in claims]
        return await asyncio.gather(*tasks)
