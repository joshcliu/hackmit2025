# HackMIT 2025 - TruthLens Submission

## 📝 Description of Project

TruthLens is a real-time fact-checking Chrome extension that verifies claims in political videos as you watch them. Using advanced AI agents powered by Claude 4 Sonnet and a multi-source verification system, TruthLens extracts claims from video transcripts, evaluates their importance, and fact-checks them against news sources, academic papers, government data, and fact-checking databases - all within seconds. The results appear in a sleek side panel with color-coded confidence scores, helping viewers distinguish facts from fiction in real-time.

## 💡 Inspiration

In an era of information overload and rapid misinformation spread, we were inspired by the challenge of helping people critically evaluate political content as they consume it. During election cycles and political debates, claims fly fast and viewers often lack the time or resources to fact-check everything they hear. We wanted to create a tool that acts as a real-time "truth companion" - democratizing access to fact-checking and empowering viewers to make informed judgments about the content they're watching. The rise of AI-generated content and deepfakes made this mission even more urgent.

## 🎯 What It Does

TruthLens transforms passive video watching into an interactive, educational experience:

1. **Automatic Claim Detection**: When you watch a YouTube video (especially political content), TruthLens automatically fetches the transcript and identifies verifiable claims vs. opinions

2. **Intelligent Prioritization**: Each claim gets an importance score (0-1). Only high-importance claims (≥0.7) are sent for verification to optimize processing time

3. **Multi-Agent Verification**: Five specialized AI agents work in parallel to verify each claim:
   - News Searcher: Finds recent news coverage
   - Academic Searcher: Locates peer-reviewed research
   - Fact-Check Searcher: Queries fact-checking databases
   - Government Data Agent: Checks official statistics
   - Temporal Consistency Agent: Analyzes historical consistency

4. **Real-Time Results**: Claims appear in the side panel as they're processed, with:
   - Color-coded scores (Green: True, Yellow: Partially True, Red: False)
   - Clickable timestamps to jump to that moment in the video
   - Expandable cards showing sources and detailed reasoning

5. **Educational Context**: Rather than just saying "true" or "false," TruthLens provides nuanced verdicts like "MISLEADING" or "NEEDS CONTEXT" with explanations

## 🔨 How We Built It

### Technology Stack

**Backend Architecture:**
- **FastAPI** for async REST API and WebSocket server for real-time updates
- **LangGraph** for orchestrating multiple AI agents that work in parallel
- **Claude 4 Sonnet** (Anthropic) for intelligent claim extraction and synthesis
- **Pydantic** for structured data validation ensuring type safety

**Frontend Development:**
- **React 19** with TypeScript for the Chrome extension's side panel UI
- **Tailwind CSS** for responsive, modern styling
- **Chrome Extensions Manifest V3** for secure browser integration
- **WebSocket client** for real-time bidirectional communication

**AI & Verification Pipeline:**
- Custom prompt engineering for claim extraction with importance scoring
- ReAct agent pattern for tool-calling capabilities
- Parallel processing architecture for multiple verification agents
- DuckDuckGo Search API (with Tavily as optional upgrade)
- YouTube Transcript API for caption fetching

### Development Process

1. **Phase 1**: Built the claim extraction agent using Claude to identify and extract atomic, verifiable claims from transcripts
2. **Phase 2**: Developed the multi-agent verification system with specialized agents for different evidence sources
3. **Phase 3**: Created the FastAPI backend with WebSocket support for real-time streaming
4. **Phase 4**: Built the Chrome extension with React, focusing on non-intrusive UX
5. **Phase 5**: Integrated all components and optimized for latency

## 🚧 Challenges We Ran Into

1. **Latency Optimization**: Initial versions took 30+ seconds per claim. We solved this by:
   - Implementing parallel agent execution
   - Adding importance scoring to skip trivial claims
   - Using Claude 4 Sonnet instead of larger models for speed

2. **WebSocket Stability**: Maintaining persistent connections between extension and server was tricky. We implemented:
   - Automatic reconnection logic
   - Message queuing for offline periods
   - Session management for multiple tabs

3. **Claim Extraction Accuracy**: Distinguishing verifiable claims from opinions required extensive prompt engineering:
   - Developed specific examples for edge cases
   - Added context preservation for pronoun resolution
   - Implemented temporal normalization for date/time claims

4. **Cross-Origin Restrictions**: Chrome's security model made API communication challenging:
   - Configured proper CORS headers
   - Used Chrome's side panel API instead of content scripts
   - Implemented secure message passing between components

5. **Source Credibility**: Not all web sources are equal. We built a credibility hierarchy:
   - Government data > Academic papers > Established media > Fact-check sites > Blogs

## 🏆 Accomplishments We're Proud Of

1. **End-to-End Integration**: Successfully built a complete pipeline from video transcript to verified claims in under 10 seconds per claim

2. **Multi-Agent Architecture**: Implemented a sophisticated LangGraph-based system where 5+ agents collaborate to verify claims from different angles

3. **Real-Time UX**: Created a seamless user experience with WebSocket streaming that shows results as they're processed, not after everything completes

4. **Nuanced Verdicts**: Rather than binary true/false, our system provides context-aware verdicts like "MISLEADING" with detailed explanations

5. **Production-Ready Code**: Despite the time constraints, we built maintainable, well-documented code with proper error handling and type safety

6. **Importance Scoring**: Our AI can distinguish between throwaway comments and serious claims worth fact-checking, saving processing time

## 📚 What We Learned

1. **Prompt Engineering is Crucial**: The difference between good and great claim extraction came down to carefully crafted prompts with specific examples

2. **Parallel Processing Wins**: Running verification agents in parallel vs. sequentially improved speed by 3-5x

3. **WebSockets > Polling**: For real-time updates, WebSocket connections provided a much better UX than HTTP polling

4. **Structured Output FTW**: Using Pydantic models with LLMs ensured consistent, type-safe responses

5. **Context Matters**: Many "false" claims are actually true but missing context - nuanced verdicts are essential

6. **Chrome Extension Complexity**: Building extensions involves navigating complex security models, content scripts, service workers, and message passing

7. **AI Agent Collaboration**: Multiple specialized agents working together outperform a single generalist agent

## 🚀 What's Next

### Short Term (Next Month)
1. **Multi-language Support**: Extend beyond English to Spanish, Mandarin, and other languages
2. **Caching Layer**: Add Redis caching to avoid re-verifying identical claims
3. **Browser Support**: Port extension to Firefox and Edge
4. **Mobile App**: Native iOS/Android apps for mobile video platforms

### Medium Term (3-6 Months)
1. **Live Stream Support**: Real-time fact-checking for live broadcasts and debates
2. **Social Media Integration**: Extend to Twitter/X videos, Instagram Reels, TikTok
3. **Collaborative Fact-Checking**: Allow users to contribute corrections and sources
4. **Historical Database**: Build a searchable database of verified claims for reference
5. **API Platform**: Offer TruthLens as an API for other developers

### Long Term Vision
1. **AI Deepfake Detection**: Integrate video/audio analysis to detect manipulated media
2. **Personalized Fact-Checking**: Learn user's interests and prioritize relevant claims
3. **Educational Platform**: Partner with schools to teach media literacy
4. **Decentralized Verification**: Blockchain-based consensus for claim verification
5. **Global Fact-Check Network**: Connect with international fact-checking organizations

### Technical Improvements
- Implement GraphRAG for better context understanding
- Add GPT-4 vision for analyzing charts/graphs in videos
- Use vector databases for semantic claim similarity
- Implement federated learning for privacy-preserving improvements
- Add real-time speaker diarization for multi-speaker videos

### Business Model Exploration
- Freemium model with advanced features
- Enterprise API for media companies
- Educational licenses for schools/universities
- Grants from organizations fighting misinformation

---

## Team

Built with passion during HackMIT 2025 by developers who believe in the power of technology to combat misinformation and empower informed citizenship.

**Tech Stack Mastery:**
- Backend: Python, FastAPI, LangGraph, Claude API
- Frontend: React, TypeScript, Chrome Extensions
- AI/ML: Prompt Engineering, Multi-Agent Systems, NLP

**Contact:**
[Your contact information here]

---

*"In a world of infinite content, truth should travel as fast as fiction."*
