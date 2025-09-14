# Live Political Video Fact-Checker

## Project Overview
A real-time fact-checking system for political videos that verifies claims as they're being made. The system uses a Chrome extension to capture and transcribe video content, then leverages LangGraph agents to verify claims and display results in real-time.

## Architecture

### System Components

```
┌─────────────────────┐
│  Chrome Extension   │
│   (Frontend)        │
├─────────────────────┤
│ • Audio capture     │
│ • Transcription     │
│ • Result display    │
│ • WebSocket client  │
└──────────┬──────────┘
           │
      WebSocket/HTTP
           │
┌──────────▼──────────┐
│   Backend Service   │
│   (Python/FastAPI)  │
├─────────────────────┤
│ • Claim detection   │
│ • Claim extraction  │
│ • Verification      │
│ • LangGraph agents  │
└─────────────────────┘
```

## Backend Design (Agent Layer)

### Input/Output Flow

**Input**: Transcribed text chunks (5-10 seconds of speech)
**Output**: Verified claims with confidence scores and sources

### Processing Pipeline

```
Text Chunk (5-10s)
    ↓
[1. Claim Detection]
    ↓
Has Claim? ──No──→ Return null
    │Yes
    ↓
[2. Claim Extraction]
    ↓
[3. Claim Cleaning]
    ↓
[4. Parallel Verification]
    ├── Web Search Agent
    ├── Fact Database Agent
    └── Context Analysis Agent
    ↓
[5. Synthesis & Scoring]
    ↓
Return Results to Frontend
```

### Agent Descriptions

#### 1. **Claim Detection Agent**
- **Purpose**: Quickly identify if text contains verifiable claims
- **Input**: Raw transcribed text chunk
- **Output**: Boolean (contains_claim) + claim type
- **Latency Target**: <500ms

#### 2. **Claim Extraction Agent**
- **Purpose**: Extract specific, verifiable statements
- **Input**: Text chunk identified as containing claims
- **Output**: List of atomic claims
- **Example**: 
  - Input: "The unemployment rate dropped to 3.5% last month, the lowest in 50 years"
  - Output: ["Unemployment rate is 3.5%", "This is the lowest in 50 years"]

#### 3. **Claim Cleaning Agent**
- **Purpose**: Standardize claims for better verification
- **Tasks**:
  - Remove filler words
  - Resolve pronouns to proper nouns
  - Add temporal context
  - Normalize numbers/dates
- **Example**:
  - Input: "He said it went up by twenty percent"
  - Output: "Biden stated [topic] increased by 20%"

#### 4. **Verification Agents (Parallel)**

##### 4a. Web Search Agent
- **Purpose**: Find supporting/contradicting evidence online
- **Tools**: Tavily API, SerpAPI, or Perplexity API
- **Returns**: Top 3 relevant sources with credibility scores

##### 4b. Fact Database Agent
- **Purpose**: Check against previously verified claims
- **Tools**: Vector database (Pinecone/Weaviate) with embedded claims
- **Returns**: Similar verified claims with outcomes

##### 4c. Context Analysis Agent
- **Purpose**: Analyze claim within video context
- **Checks**:
  - Is this consistent with previous statements?
  - Is context being misrepresented?
  - Are there important caveats?

#### 5. **Synthesis Agent**
- **Purpose**: Combine all verification results
- **Output**:
  - Verification status (Verified/Disputed/Unverifiable/Needs Context)
  - Confidence score (0-1)
  - Brief explanation
  - Supporting sources

### Data Structures

```python
# Input
class TextChunk:
    text: str
    timestamp: float
    chunk_id: str
    video_context: Optional[str]  # Previous chunks for context

# Output
class VerificationResult:
    chunk_id: str
    timestamp: float
    claims: List[ClaimResult]
    processing_time: float

class ClaimResult:
    original_text: str
    cleaned_claim: str
    status: Literal["verified", "disputed", "unverifiable", "needs_context"]
    confidence: float  # 0-1
    explanation: str
    sources: List[Source]
    
class Source:
    title: str
    url: str
    credibility: Literal["high", "medium", "low"]
    relevant_quote: str

### Minimal Claim Schema (Verifier Input)

For transcript-based processing, each extracted claim fed into the verifier should use this minimal structure.

```python
from dataclasses import dataclass

@dataclass
class ClaimForVerification:
    """Minimal claim payload produced by the extractor and consumed by the verifier."""
    video_id: str   # YouTube video ID
    start_s: float  # start time (seconds) of the utterance containing the claim
    end_s: float    # end time (seconds) of the utterance containing the claim
    exact_quote: str # exact quote from the transcript containing the claim
    claim_text: str # atomic, normalized claim text (cleaned and concise version for verification)
    speaker: str    # name or identifier of the person who made the claim
    importance_score: float # importance score from 0.0 to 1.0 indicating verification priority
```

Notes:
- `exact_quote` preserves the original wording, capitalization, and speech patterns from the transcript
- `claim_text` is a cleaned, clear, and concise version suitable for fact-checking (normalized grammar, removed filler words, complete sentence)
- `start_s`/`end_s` refer to the transcript time bounds that cover this claim (can span multiple caption snippets if merged into a sentence)
- `importance_score` helps prioritize which claims to verify first (0.8-1.0 for high priority disputed claims, 0.4-0.7 for medium priority factual statements, 0.0-0.3 for low priority obvious facts)

### API Endpoints

```
POST /api/verify-chunk
Request:
{
    "text": "chunk text here",
    "timestamp": 145.2,
    "chunk_id": "chunk_123",
    "context": "previous chunk text"  // optional
}

Response:
{
    "chunk_id": "chunk_123",
    "claims": [...],
    "processing_time": 4.2
}

WebSocket /ws/verify-stream
- Bidirectional streaming for real-time updates
- Sends preliminary results, then refined results
```

### Performance Requirements

- **Latency**: 5-10 seconds end-to-end
- **Throughput**: Handle multiple concurrent chunks
- **Accuracy**: Prioritize precision over recall (avoid false positives)

### Tech Stack

- **Framework**: FastAPI (async support)
- **Agent Orchestration**: LangGraph
- **LLM**: GPT-4o-mini for speed, GPT-4o for complex claims
- **Search**: Tavily API (optimized for factual search)
- **Caching**: Redis
- **Vector DB**: Pinecone/Chroma for claim similarity
- **Queue**: Celery/RQ for async processing

### Development Phases

1. **Phase 1 (MVP)**: Basic claim detection and web search
2. **Phase 2**: Add fact database and caching
3. **Phase 3**: Context analysis and confidence scoring
4. **Phase 4**: Optimization for speed and accuracy

## Frontend (Chrome Extension)

### Responsibilities
- Capture audio from video elements
- Transcribe using Web Speech API or send to backend
- Display verification results as overlay
- Maintain WebSocket connection

### Key Features
- Non-intrusive UI overlay
- Color-coded claim indicators (green/red/yellow)
- Expandable source panel
- Settings for sensitivity levels

## Getting Started

### Backend Setup
```bash
# Clone repository
git clone [repo-url]
cd hackmit2025/backend

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Add your API keys (OpenAI, Tavily, etc.)

# Run the server
uvicorn main:app --reload
```

### Testing the Backend
```bash
# Test claim verification
curl -X POST http://localhost:8000/api/verify-chunk \
  -H "Content-Type: application/json" \
  -d '{"text": "The unemployment rate is at 3.5%", "chunk_id": "test_1"}'
```

## Environment Variables

```
OPENAI_API_KEY=
TAVILY_API_KEY=
REDIS_URL=
DATABASE_URL=
```

## Team Responsibilities

- **Backend (Agent Layer)**: Claim processing, verification logic, LangGraph implementation
- **Frontend (Chrome Extension)**: Audio capture, transcription, UI/UX
- **Infrastructure**: WebSocket server, caching, deployment

## Resources

- [LangGraph Documentation](https://python.langchain.com/docs/langgraph)
- [Chrome Extension Manifest V3](https://developer.chrome.com/docs/extensions/mv3/)
- [Tavily Search API](https://tavily.com/)
