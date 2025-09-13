"""
Main orchestrator for claim verification system.
"""

import asyncio
from typing import List, Optional
from langchain_anthropic import ChatAnthropic

from agents import (
    NewsSearcherAgent,
    AcademicSearcherAgent,
    FactCheckSearcherAgent,
    GovernmentDataAgent,
    TemporalConsistencyAgent
)
from base_agent import BaseVerificationAgent


class OrchestratorAgent(BaseVerificationAgent):
    """Orchestrator that synthesizes results from all specialist agents."""
    
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

Output requirements:
- Start with a clear verdict: TRUE, FALSE, MISLEADING, PARTIALLY TRUE, or UNVERIFIABLE
- Provide comprehensive reasoning that synthesizes all agent findings
- Highlight key evidence and any important contradictions
- Note crucial context or caveats
- End with a consolidated list of the most credible sources

Remember: You're the final arbiter. Use the tools to resolve uncertainties and provide the most accurate assessment possible."""
        
    async def verify(self, claim: str, agent_results: List[str] = None) -> str:
        """
        Override verify to synthesize agent findings.
        
        Args:
            claim: The claim being verified
            agent_results: List of findings from specialist agents
            
        Returns:
            Synthesized assessment with verdict and sources
        """
        if not agent_results:
            # If called without agent results, just do a direct verification
            return await super().verify(claim)
        
        # Format agent results for synthesis
        agent_summaries = self._format_agent_results(agent_results)
        
        # Create the synthesis request
        synthesis_message = f"""CLAIM TO VERIFY: {claim}

=== SPECIALIST AGENT FINDINGS ===

{agent_summaries}

=== YOUR TASK ===

Synthesize all agent findings into a comprehensive final assessment. 

Steps to follow:
1. Analyze areas of agreement and contradiction between agents
2. Use search/scraping tools to resolve any ambiguities or verify conflicting information
3. Cross-reference sources mentioned by different agents
4. Determine the most credible conclusion based on evidence quality
5. Provide a clear verdict with comprehensive reasoning

Output format:
VERDICT: [TRUE/FALSE/MISLEADING/PARTIALLY TRUE/UNVERIFIABLE]

[Detailed natural language assessment explaining your reasoning, key evidence, and any important context or caveats]

SOURCES:
[Consolidated list of the most credible sources, with brief credibility notes]"""
        
        try:
            result = await self.agent.ainvoke({
                "messages": [("user", synthesis_message)]
            })
            
            # Extract the final message from the agent
            if result.get("messages"):
                last_message = result["messages"][-1]
                if hasattr(last_message, "content"):
                    return last_message.content
            
            return "Unable to synthesize findings due to processing error."
            
        except Exception as e:
            return f"Synthesis failed: {str(e)}"
    
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
        # Initialize Claude 4 Sonnet model
        self.model = ChatAnthropic(
            api_key=anthropic_api_key,
            model="claude-4-sonnet-20250514"
        )
        
        # Initialize all agents
        self.news_agent = NewsSearcherAgent(self.model)
        self.academic_agent = AcademicSearcherAgent(self.model)
        self.fact_check_agent = FactCheckSearcherAgent(self.model)
        self.gov_data_agent = GovernmentDataAgent(self.model)
        self.temporal_agent = TemporalConsistencyAgent(self.model)
        self.orchestrator = OrchestratorAgent(self.model)
        
        # TODO: Add memory system for contradiction detection
        self.memory = None
        
    async def verify_claim(self, claim: str) -> str:
        """
        Verify a single atomic claim.
        
        Args:
            claim: The atomic claim to verify
            
        Returns:
            Natural language assessment of the claim with sources
        """
        print(f"Verifying claim: {claim}")
        
        # Spawn all agents in parallel
        agent_tasks = [
            self.news_agent.verify(claim),
            self.academic_agent.verify(claim),
            self.fact_check_agent.verify(claim),
            self.gov_data_agent.verify(claim),
            self.temporal_agent.verify(claim)
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
            agent_results=agent_results
        )
        
        # TODO: Store in memory for future contradiction detection
        # if self.memory:
        #     self.memory.store_claim(claim, final_assessment)
        
        return final_assessment
    
    async def verify_claims_batch(self, claims: List[str]) -> List[str]:
        """
        Verify multiple claims in parallel.
        
        Args:
            claims: List of claims to verify
            
        Returns:
            List of natural language assessments
        """
        tasks = [self.verify_claim(claim) for claim in claims]
        return await asyncio.gather(*tasks)
