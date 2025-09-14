# 🔍 TruthLens - Real-Time Video Fact-Checker

![TruthLens Banner](https://img.shields.io/badge/HackMIT-2025-blue) ![Status](https://img.shields.io/badge/Status-Active-green) ![License](https://img.shields.io/badge/License-MIT-yellow)

**TruthLens** is an AI-powered Chrome extension that fact-checks political videos in real-time, helping viewers distinguish facts from fiction as they watch. Built for HackMIT 2025.

## 🎥 Demo

Watch TruthLens in action as it processes political speeches, debates, and news videos - extracting claims and verifying them against multiple sources within seconds.

## ✨ Key Features

- **🚀 Real-Time Processing**: Claims are extracted and verified as you watch
- **🎯 Smart Claim Detection**: AI identifies verifiable statements vs opinions
- **🔬 Multi-Source Verification**: Cross-references claims with news, academic papers, government data, and fact-checking sites
- **📊 Visual Confidence Scores**: Color-coded results (green/yellow/red) with 0-10 accuracy scores
- **⏱️ Timestamp Navigation**: Click any claim to jump to that moment in the video
- **📝 Detailed Evidence**: Expandable cards show sources and reasoning for each verdict

## 🏗️ Architecture

```mermaid
graph TB
    subgraph "Chrome Extension"
        A[YouTube Video] --> B[Side Panel UI]
        B --> C[WebSocket Client]
    end
    
    subgraph "FastAPI Backend"
        C <--> D[WebSocket Server]
        D --> E[Claim Extraction Agent]
        E --> F[Verification Orchestrator]
        
        subgraph "Verification Agents"
            F --> G[News Search]
            F --> H[Academic Search]
            F --> I[Fact-Check DB]
            F --> J[Government Data]
            F --> K[Temporal Analysis]
        end
    end
    
    subgraph "External APIs"
        E --> L[Claude 4 Sonnet]
        G --> M[Web Search APIs]
        H --> N[Academic APIs]
    end
```

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- Chrome Browser
- Anthropic API Key

### 1. Clone & Setup Environment

```bash
git clone https://github.com/yourusername/hackmit2025.git
cd hackmit2025

# Create .env file
echo "ANTHROPIC_API_KEY=your_key_here" > .env
```

### 2. Start Backend Server

```bash
# Install Python dependencies
pip install -r api_requirements.txt

# Start the API server
python api_server.py
```

### 3. Install Chrome Extension

```bash
# Build the extension
cd chrome-extension
npm install
npm run build

# Load in Chrome:
# 1. Open chrome://extensions/
# 2. Enable Developer Mode
# 3. Click "Load unpacked"
# 4. Select chrome-extension/dist folder
```

### 4. Start Fact-Checking!

1. Navigate to any YouTube video
2. Click the TruthLens extension icon
3. Click "Start Fact-Checking"
4. Watch claims appear in real-time

## 🧠 How It Works

### Claim Extraction Pipeline
1. **Transcript Fetching**: Downloads video captions from YouTube
2. **Intelligent Chunking**: Splits transcript into 30-60 second segments
3. **Claim Identification**: Claude 4 identifies verifiable statements
4. **Importance Scoring**: Prioritizes claims worth fact-checking (0.7+ score)

### Verification Process
Each high-importance claim undergoes multi-agent verification:

- **News Searcher**: Searches recent news articles for evidence
- **Academic Searcher**: Finds peer-reviewed studies and papers
- **Fact-Check Searcher**: Queries established fact-checking databases
- **Government Data Agent**: Checks official statistics and records
- **Temporal Consistency**: Analyzes claim consistency over time

### Synthesis & Scoring
An orchestrator agent synthesizes all findings to produce:
- **Verdict**: TRUE / FALSE / MISLEADING / PARTIALLY TRUE / UNVERIFIABLE
- **Confidence Score**: 0-10 numerical rating
- **Summary**: One-paragraph explanation with key evidence
- **Sources**: Credible citations with URLs

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Async REST API and WebSocket server
- **LangGraph** - Multi-agent orchestration framework
- **Claude 4 Sonnet** - Claim extraction and synthesis
- **Pydantic** - Data validation and structured outputs

### Frontend
- **React 19** - UI framework
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS** - Utility-first styling
- **Vite** - Fast build tooling
- **Chrome Extensions API** - Browser integration

### External Services
- **YouTube Transcript API** - Caption fetching
- **DuckDuckGo Search** - Web search fallback
- **Tavily API** - Enhanced fact-oriented search (optional)

## 📁 Project Structure

```
hackmit2025/
├── api_server.py              # FastAPI backend server
├── claim_extraction/          # Claim extraction agent
│   └── agent.py              # Claude-powered extractor
├── claim_verification/        # Verification system
│   ├── orchestrator.py       # Main verification coordinator
│   ├── agents.py             # Specialist verification agents
│   └── base_agent.py         # Base agent framework
├── chrome-extension/          # Browser extension
│   ├── src/
│   │   ├── sidepanel/       # React side panel UI
│   │   ├── background.ts    # Service worker
│   │   └── services/        # API communication
│   └── dist/                # Built extension
└── experiments/              # Testing scripts
```

## 🔧 Configuration

### Environment Variables
```bash
ANTHROPIC_API_KEY=sk-ant-api...  # Required: Claude API
TAVILY_API_KEY=tvly-...          # Optional: Better search
```

### Customization Options
- Adjust claim importance threshold in `claim_extraction/agent.py`
- Modify verification agents in `claim_verification/agents.py`
- Customize UI styling in `chrome-extension/src/sidepanel/`

## 📊 Performance

- **Extraction Speed**: ~30-60 seconds for 10-minute video
- **Verification Speed**: ~5-8 seconds per claim
- **Memory Usage**: ~500MB Python backend
- **Accuracy**: Prioritizes precision over recall

## 🔒 Privacy & Security

- All processing happens locally on your machine
- API keys never sent to browser
- Extension only activates on YouTube domains
- No user data collected or stored

## 🚧 Known Limitations

- Currently supports English videos only
- Requires videos with closed captions
- Verification quality depends on public information availability
- Processing time scales with video length

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🏆 HackMIT 2025 Submission

Built with ❤️ by Team TruthLens at HackMIT 2025

---

*Fighting misinformation, one video at a time.*