# Claim Verification System

A parallel agent-based system for real-time political claim verification using Claude 4 Sonnet and Composio search integration.

## Quick Start

### 1. Install Dependencies

```bash
cd claim_verification
pip install -r requirements.txt
```

Or using uv:
```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

### 2. Set Up Environment Variables

```bash
# Copy the example env file
cp env.example .env

# Edit .env and add your API keys
# ANTHROPIC_API_KEY=your-anthropic-key-here
# COMPOSIO_API_KEY=your-composio-key-here
```

### 3. Run Example

```bash
python example_usage.py
```

## Architecture Overview

### System Components

```
                    Atomic Claim
                         │
                         ▼
              ┌──────────────────────┐
              │   Spawn Parallel     │
              │   Specialized Agents │
              │  (ReAct + Composio)  │
              └──────────────────────┘
                         │
        ┌────────┬───────┴────────┬──────────┬──────────┐
        ▼        ▼                ▼          ▼          ▼
   News Agent  Academic Agent  Fact-Check  Gov Data  Temporal
                                  Agent      Agent     Agent
        │        │                │          │          │
        └────────┴────────────────┴──────────┴──────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  Orchestrator Agent  │
              │  (Reconcile & Synth) │
              └──────────────────────┘
                         │
                         ▼
               Natural Language Assessment
```

### Specialized Agents

1. **News Searcher Agent** 
   - Searches recent news articles from reputable outlets
   - Prioritizes recent reporting (last 30 days)
   - Assesses source credibility

2. **Academic Searcher Agent**
   - Finds peer-reviewed research and studies
   - Focuses on methodology quality
   - Explains findings in accessible language

3. **Fact-Check Searcher Agent**
   - Checks Snopes, FactCheck.org, PolitiFact, etc.
   - Summarizes fact-checker consensus
   - Notes thoroughness of investigations

4. **Government Data Agent**
   - Verifies against official statistics (BLS, Census, CDC)
   - Prioritizes primary sources
   - Notes data currency and revisions

5. **Temporal Consistency Agent**
   - Analyzes time-related aspects
   - Detects cherry-picked periods
   - Verifies historical comparisons

### Orchestrator Agent

Synthesizes all agent findings by:
- Identifying consensus and conflicts
- Weighting evidence by source credibility
- Producing clear natural language verdict
- Consolidating credible sources

## Usage

### Basic Usage

```python
import asyncio
from claim_verification import ClaimVerificationOrchestrator

async def main():
    # Initialize orchestrator
    orchestrator = ClaimVerificationOrchestrator(
        anthropic_api_key="your-api-key"
    )
    
    # Verify a claim
    claim = "The unemployment rate is at 3.5%"
    result = await orchestrator.verify_claim(claim)
    print(result)

asyncio.run(main())
```

### Batch Verification

```python
# Verify multiple claims in parallel
claims = [
    "The unemployment rate is at 3.5%",
    "GDP grew by 2.1% last quarter",
    "Crime rates are at an all-time high"
]

results = await orchestrator.verify_claims_batch(claims)
for claim, result in zip(claims, results):
    print(f"Claim: {claim}")
    print(f"Result: {result}\n")
```

### API Integration

```python
from fastapi import FastAPI
from claim_verification import ClaimVerificationOrchestrator

app = FastAPI()
orchestrator = ClaimVerificationOrchestrator(anthropic_api_key="...")

@app.post("/verify")
async def verify_claim(claim: str):
    result = await orchestrator.verify_claim(claim)
    return {"assessment": result}
```

## Technical Implementation

### Base Agent Pattern

All agents inherit from `BaseVerificationAgent` with the only difference being their specialized prompts:

```python
class BaseVerificationAgent:
    def __init__(self, model: ChatAnthropic, composio_toolset: ComposioToolSet):
        self.model = model
        self.composio = composio_toolset
        self.tools = self._setup_tools()
        self.agent = self._create_agent()
    
    def get_prompt(self):
        """Override in subclasses with specialized prompts."""
        raise NotImplementedError
```

### Adding New Agents

Simply extend the base class with a new prompt:

```python
class EconomicDataAgent(BaseVerificationAgent):
    def get_prompt(self):
        return ChatPromptTemplate.from_messages([
            ("system", "You are an economic data specialist..."),
            ("user", "Verify: {claim}")
        ])
```

### Technology Stack

- **LLM**: Claude 4 Sonnet (`claude-4-sonnet-20250514`)
- **Agent Framework**: LangGraph ReAct agents
- **Search**: Composio search (Action.COMPOSIO_SEARCH_SEARCH)
- **Web Scraping**: Crawl4AI
- **Async**: Full async/await support

## Output Format

Natural language assessment with:
- Clear verdict (accurate/false/misleading/needs context)
- Key evidence explanation
- Important caveats
- Consolidated source list

Example:
```
Based on comprehensive analysis across multiple sources, this claim appears to be 
accurate. The 3.5% unemployment rate for September 2024 is confirmed by official 
Bureau of Labor Statistics data...

Sources:
- Bureau of Labor Statistics (bls.gov): September 2024 employment report
- Reuters (reuters.com): "US unemployment falls to 3.5%" 
- PolitiFact (politifact.com): Rated "True" - unemployment claim verified
```

## Performance

- **Verification Time**: 5-8 seconds per claim
- **Parallel Processing**: All agents run simultaneously
- **Batch Support**: Multiple claims processed in parallel
- **Error Handling**: Graceful degradation if agents fail

## Testing

Run basic tests:
```bash
python test_basic.py
```

Test various claim types:
```bash
python example_usage.py
```

## Project Structure

```
claim_verification/
├── __init__.py           # Package initialization
├── base_agent.py         # Base agent class
├── agents.py             # Specialized agents
├── orchestrator.py       # Main orchestrator
├── example_usage.py      # Usage examples
├── test_basic.py         # Basic tests
├── requirements.txt      # Dependencies
└── env.example          # Example environment file
```

## Troubleshooting

### Import Errors
- Ensure you're in the virtual environment
- Check that all dependencies are installed
- Use absolute imports when importing locally

### Composio Search Setup
- Requires COMPOSIO_API_KEY environment variable
- Uses Action.COMPOSIO_SEARCH_SEARCH for web search
- Falls back to mock search if API key not configured
- Configure Composio dashboard for production use

### Rate Limiting
- Add delays between claims
- Use batch verification
- Consider implementing caching

## Future Enhancements

- [ ] Memory system for contradiction detection
- [ ] XML parsing for structured outputs
- [ ] Caching layer for search results
- [ ] WebSocket interface for real-time updates
- [ ] Semantic similarity for claim comparison
- [ ] Confidence scoring based on source agreement