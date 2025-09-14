# Complete Setup Guide for Fact-Checking System

This guide will help you set up and run the complete fact-checking system with the Chrome extension frontend and Python backend.

## Architecture Overview

The system consists of:
1. **Chrome Extension** - Side panel UI that appears on YouTube videos
2. **FastAPI Backend** - REST API + WebSocket server for claim extraction and verification
3. **Claim Extraction Agent** - Uses Claude to extract claims from video transcripts
4. **Claim Verification System** - Multi-agent system that verifies claims using web search

## Prerequisites

- Python 3.9+
- Node.js 18+ and npm
- Chrome browser
- Anthropic API key (required)
- Tavily API key (optional, for better search results)

## Step 1: Backend Setup

### 1.1 Install Python Dependencies

```bash
# Install API server dependencies
pip install -r api_requirements.txt

# Or using uv (faster)
uv pip install -r api_requirements.txt
```

### 1.2 Configure API Keys

```bash
# Copy the example environment file
cp env.example .env

# Edit .env and add your Anthropic API key
# ANTHROPIC_API_KEY=sk-ant-api...
```

### 1.3 Start the API Server

```bash
python api_server.py
```

The server will start on `http://127.0.0.1:8000`. You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

Test that it's working by visiting http://127.0.0.1:8000 in your browser.

## Step 2: Chrome Extension Setup

### 2.1 Install Dependencies

```bash
cd chrome-extension
npm install
```

### 2.2 Build the Extension

```bash
npm run build
```

This creates a `dist` folder with the built extension.

### 2.3 Load Extension in Chrome

1. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode" (top right toggle)
3. Click "Load unpacked"
4. Select the `chrome-extension/dist` folder
5. The extension should appear with the name "Fact-Check AI"

## Step 3: Using the System

### 3.1 Basic Usage

1. **Start the Backend**: Make sure `api_server.py` is running
2. **Navigate to YouTube**: Go to any YouTube video
3. **Open Side Panel**: Click the extension icon or use the Chrome side panel
4. **Start Fact-Checking**: Click "Start Fact-Checking" button
5. **Watch Real-Time Updates**: Claims will appear as they're extracted and verified

### 3.2 What Happens During Processing

1. **Transcript Fetching**: Downloads the video's closed captions
2. **Claim Extraction**: AI extracts verifiable claims from the transcript
3. **Importance Scoring**: Each claim gets an importance score (0-1)
4. **Verification**: High-importance claims (≥0.7) are fact-checked using web search
5. **Real-Time Updates**: Claims appear in the UI as they're processed

### 3.3 Understanding the Results

- **Green (7-10)**: Verified as accurate
- **Yellow (4-7)**: Partially true or needs context
- **Red (0-4)**: False or misleading
- **Click timestamps**: Jump to that point in the video
- **Click claims**: Expand to see verification details

## Development Mode

For development with hot reload:

### Backend Development
```bash
# Run with auto-reload
uvicorn api_server:app --reload --host 127.0.0.1 --port 8000
```

### Extension Development
```bash
cd chrome-extension
npm run dev
```

The extension will auto-reload when you make changes. Just refresh the YouTube page.

## Troubleshooting

### "Server not available" Error
- Make sure `api_server.py` is running
- Check that the server is on port 8000
- Try visiting http://127.0.0.1:8000 directly

### No Claims Extracted
- Check the console for errors (F12 in Chrome)
- Ensure the video has English captions
- Verify your Anthropic API key is valid

### Slow Processing
- Claim extraction takes ~5-10 seconds per chunk
- Verification takes ~5-8 seconds per claim
- Longer videos will take more time

### WebSocket Connection Issues
- Check browser console for WebSocket errors
- Ensure no firewall is blocking local connections
- Try restarting both the server and extension

## API Endpoints

The backend provides:

- `POST /process-video` - Start processing a video
- `GET /session/{session_id}` - Get processing status
- `WS /ws/{session_id}` - WebSocket for real-time updates

## Environment Variables

Required:
- `ANTHROPIC_API_KEY` - Your Anthropic API key

Optional:
- `TAVILY_API_KEY` - For enhanced web search (falls back to DuckDuckGo)

## Performance Notes

- **Extraction**: ~30-60 seconds for a 10-minute video
- **Verification**: ~5-8 seconds per high-importance claim
- **Memory**: ~500MB for the Python backend
- **Network**: All communication is local (no external servers except API calls)

## Security Notes

- The extension only works on YouTube domains
- All processing happens locally on your machine
- API keys are never sent to the browser
- WebSocket connections are local only

## Next Steps

- Adjust importance thresholds in `claim_extraction/agent.py`
- Modify verification agents in `claim_verification/agents.py`
- Customize UI styling in `chrome-extension/src/sidepanel/`
- Add caching to speed up repeated verifications
