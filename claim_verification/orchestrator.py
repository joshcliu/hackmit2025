"""
Main orchestrator for claim verification system.
"""

import asyncio
from typing import List, Optional
from langchain_anthropic import ChatAnthropic
from composio_langchain import LangchainProvider
from langgraph.prebuilt import create_react_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import Tool

from agents import (
    NewsSearcherAgent,
    AcademicSearcherAgent,
    FactCheckSearcherAgent,
    GovernmentDataAgent,
    TemporalConsistencyAgent
)


class OrchestratorAgent:
    """Orchestrator that synthesizes results from all specialist agents."""
    
    def __init__(self, model: ChatAnthropic, composio_toolset: Optional[LangchainProvider] = None):
        self.model = model
        self.composio = composio_toolset or LangchainProvider()
        self.tools = self._setup_tools()
        
    def _setup_tools(self):
        """Setup additional search tools for the orchestrator."""
        tools = []
        
        # Tavily search for additional investigation
        try:
            tavily_tools = self.composio.wrap_tools(app_name="tavily")
            if tavily_tools:
                tools.extend(tavily_tools)
        except Exception as e:
            print(f"Warning: Could not load Tavily for orchestrator: {e}")
            
        return tools
        
    async def synthesize(self, claim: str, agent_results: List[str]) -> str:
        """
        Synthesize all agent findings into a final assessment.
        Returns a natural language summary with sources.
        """
        
        # Format agent results for the synthesis prompt
        agent_summaries = self._format_agent_results(agent_results)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are the lead fact-checker synthesizing findings from multiple specialist agents.

Your job is to:
1. Review all agent assessments carefully
2. Identify where agents agree and where they conflict
3. Use the search tool if you need to resolve any ambiguities
4. Produce a clear, natural language verdict

Consider:
- Source credibility (government data > established media > blogs)
- Recency of information
- Consensus among agents
- Any important caveats or context needed

Your output should be a comprehensive natural language assessment that:
- Clearly states whether the claim is accurate, false, misleading, or needs context
- Explains the key evidence supporting your conclusion
- Notes any important caveats or nuances
- Is accessible to a general audience
- Ends with a consolidated list of the most credible sources

Format your response as:
[Natural language assessment of the claim, explaining your verdict and reasoning]

Sources:
[Consolidated list of the most credible sources from all agents]

Do NOT output confidence scores. Focus on clear, accessible explanation."""),
            ("user", """Claim being verified: {claim}

Agent Findings:
{agent_summaries}

Please synthesize these findings into a final verification assessment.""")
        ])
        
        # Create ReAct agent for synthesis
        synthesis_agent = create_react_agent(
            model=self.model,
            tools=self.tools,
            prompt=prompt
        )
        
        try:
            result = await synthesis_agent.ainvoke({
                "messages": [(
                    "user", 
                    prompt.format_messages(
                        claim=claim,
                        agent_summaries=agent_summaries
                    )[1].content
                )]
            })
            
            # Extract the final message
            if result.get("messages"):
                last_message = result["messages"][-1]
                if hasattr(last_message, "content"):
                    return last_message.content
                    
            return "Unable to synthesize findings."
            
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
            composio_api_key: Optional API key for Composio (not needed for Tavily)
        """
        # Initialize Composio toolset (no API key needed for Tavily)
        self.composio = LangchainProvider()
        
        # Initialize Claude 4 Sonnet model
        self.model = ChatAnthropic(
            api_key=anthropic_api_key,
            model="claude-4-sonnet-20250514"
        )
        
        # Initialize all agents
        self.news_agent = NewsSearcherAgent(self.model, self.composio)
        self.academic_agent = AcademicSearcherAgent(self.model, self.composio)
        self.fact_check_agent = FactCheckSearcherAgent(self.model, self.composio)
        self.gov_data_agent = GovernmentDataAgent(self.model, self.composio)
        self.temporal_agent = TemporalConsistencyAgent(self.model, self.composio)
        self.orchestrator = OrchestratorAgent(self.model, self.composio)
        
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
        final_assessment = await self.orchestrator.synthesize(
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
