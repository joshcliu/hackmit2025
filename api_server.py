"""
FastAPI server for claim extraction and verification.
Provides REST endpoints and WebSocket for real-time updates.
"""

import asyncio
import os
import sys
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import uuid

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from youtube_transcript_api import YouTubeTranscriptApi
from dotenv import load_dotenv

# Add project directories to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'agents', 'claim_extraction'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'agents', 'claim_verification'))

from agents.claim_extraction.agent import ClaimExtractionAgent, ClaimMinimal
from agents.claim_verification.orchestrator import ClaimVerificationOrchestrator

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Fact-Check API", version="1.0.0")

# Configure CORS for Chrome extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*",  # Allow all origins including Chrome extensions
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Store active WebSocket connections and processing sessions
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.processing_sessions: Dict[str, Dict] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        if session_id in self.processing_sessions:
            del self.processing_sessions[session_id]

    async def send_message(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].send_json(message)
            except:
                # Connection might be closed
                pass

    def create_session(self, session_id: str, video_id: str):
        self.processing_sessions[session_id] = {
            "video_id": video_id,
            "status": "initializing",
            "claims": [],
            "verified_claims": [],
            "start_time": datetime.now().isoformat()
        }

    def update_session(self, session_id: str, updates: dict):
        if session_id in self.processing_sessions:
            self.processing_sessions[session_id].update(updates)

    def get_session(self, session_id: str) -> Optional[Dict]:
        return self.processing_sessions.get(session_id)

manager = ConnectionManager()

# Request/Response models
class ProcessVideoRequest(BaseModel):
    video_id: str = Field(..., description="YouTube video ID")
    session_id: Optional[str] = Field(None, description="Session ID for WebSocket updates")

class ProcessVideoResponse(BaseModel):
    session_id: str
    status: str
    message: str

class ClaimWithVerification(BaseModel):
    # Original claim fields
    video_id: str
    start_s: float
    end_s: float
    claim_text: str
    speaker: str
    importance_score: float
    # Verification fields
    verification_status: Optional[str] = None
    verification_score: Optional[float] = None
    verification_summary: Optional[str] = None
    sources: Optional[List[str]] = None

# Helper functions
def fetch_transcript(video_id: str) -> List[Dict[str, Any]]:
    """Fetch transcript from YouTube."""
    try:
        # Create an instance of the API
        api = YouTubeTranscriptApi()
        # Fetch the transcript
        transcript_data = api.fetch(video_id)
        # Convert to raw data format (list of dicts)
        return transcript_data.to_raw_data()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch transcript: {str(e)}")

def chunk_transcript(transcript: List[Dict[str, Any]], chunk_size_seconds: float = 30.0) -> List[str]:
    """
    Chunk transcript into time-based segments for processing.
    """
    chunks = []
    current_chunk_items = []
    current_start = None
    line_number = 0
    
    for item in transcript:
        start = item.get("start", 0.0)
        duration = item.get("duration", 0.0)
        end = start + duration
        text = item.get("text", "").strip()
        
        if not text:
            continue
            
        line_number += 1
        
        # Initialize first chunk
        if current_start is None:
            current_start = start
            current_chunk_items = [(line_number, start, duration, text)]
            continue
        
        # Check if adding this item would exceed chunk size
        potential_duration = end - current_start
        
        if potential_duration > chunk_size_seconds and current_chunk_items:
            # Finalize current chunk
            chunk_lines = []
            for line_num, item_start, item_duration, item_text in current_chunk_items:
                chunk_lines.append(f"{line_num} [{item_start:.2f}s + {item_duration:.2f}s] {item_text}")
            chunks.append("\n".join(chunk_lines))
            
            # Start new chunk
            current_start = start
            current_chunk_items = [(line_number, start, duration, text)]
        else:
            # Add to current chunk
            current_chunk_items.append((line_number, start, duration, text))
    
    # Add final chunk
    if current_chunk_items:
        chunk_lines = []
        for line_num, item_start, item_duration, item_text in current_chunk_items:
            chunk_lines.append(f"{line_num} [{item_start:.2f}s + {item_duration:.2f}s] {item_text}")
        chunks.append("\n".join(chunk_lines))
    
    return chunks

async def verify_single_claim(claim, orchestrator, session_id: str, manager: ConnectionManager):
    """
    Verify a single claim asynchronously.
    """
    try:
        # Send verification start
        await manager.send_message(session_id, {
            "type": "verification_start",
            "claim_text": claim.claim_text[:100]
        })
        
        # Verify the claim
        verification_result = await orchestrator.verify_claim(claim.claim_text)
        
        # Parse verification result
        verification_score = 5.0  # Default middle score
        verification_status = "unverified"
        
        # Simple parsing of verdict
        if "TRUE" in verification_result.upper()[:100]:
            verification_score = 8.5
            verification_status = "verified"
        elif "FALSE" in verification_result.upper()[:100]:
            verification_score = 2.0
            verification_status = "false"
        elif "MISLEADING" in verification_result.upper()[:100]:
            verification_score = 4.0
            verification_status = "misleading"
        elif "PARTIALLY TRUE" in verification_result.upper()[:100]:
            verification_score = 6.0
            verification_status = "partial"
        
        # Send verification result
        await manager.send_message(session_id, {
            "type": "claim_verified",
            "claim": {
                "video_id": claim.video_id,
                "start_s": claim.start_s,
                "end_s": claim.end_s,
                "claim_text": claim.claim_text,
                "speaker": claim.speaker,
                "importance_score": claim.importance_score,
                "verification_status": verification_status,
                "verification_score": verification_score,
                "verification_summary": verification_result[:500]  # First 500 chars
            }
        })
        
    except Exception as e:
        print(f"Error verifying claim '{claim.claim_text[:50]}...': {e}")


async def process_video_pipeline(video_id: str, session_id: str):
    """
    Main pipeline for processing a video:
    1. Fetch transcript
    2. Extract claims
    3. Verify claims
    4. Send updates via WebSocket
    """
    try:
        # Update status: fetching transcript
        await manager.send_message(session_id, {
            "type": "status",
            "status": "fetching_transcript",
            "message": "Fetching video transcript..."
        })
        
        # Fetch transcript
        transcript = fetch_transcript(video_id)
        
        # Update status: chunking
        await manager.send_message(session_id, {
            "type": "status",
            "status": "chunking",
            "message": f"Processing {len(transcript)} transcript segments..."
        })
        
        # Chunk transcript
        chunks = chunk_transcript(transcript, chunk_size_seconds=60.0)
        
        # Initialize extraction agent and verification orchestrator
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not configured")
        
        extraction_agent = ClaimExtractionAgent()
        orchestrator = ClaimVerificationOrchestrator(anthropic_api_key=api_key)
        
        # Extract claims from chunks
        await manager.send_message(session_id, {
            "type": "status",
            "status": "extracting_claims",
            "message": f"Extracting claims from {len(chunks)} chunks..."
        })
        
        all_claims = []
        for i, chunk in enumerate(chunks):
            try:
                result = await extraction_agent.aextract(video_id=video_id, chunk=chunk)
                
                # Send progress update
                await manager.send_message(session_id, {
                    "type": "extraction_progress",
                    "chunk": i + 1,
                    "total_chunks": len(chunks),
                    "claims_found": len(result.claims)
                })
                
                # Send each claim as it's extracted and immediately verify if high importance
                for claim in result.claims:
                    claim_dict = {
                        "video_id": claim.video_id,
                        "start_s": claim.start_s,
                        "end_s": claim.end_s,
                        "claim_text": claim.claim_text,
                        "speaker": claim.speaker,
                        "importance_score": claim.importance_score,
                        "verification_status": "pending"
                    }
                    all_claims.append(claim)
                    
                    await manager.send_message(session_id, {
                        "type": "claim_extracted",
                        "claim": claim_dict
                    })
                    
                    # Immediately verify high-importance claims
                    if claim.importance_score >= 0.7:
                        # Start verification in background
                        asyncio.create_task(verify_single_claim(
                            claim, orchestrator, session_id, manager
                        ))
                    
            except Exception as e:
                print(f"Error processing chunk {i+1}: {e}")
                continue
        
        # Wait a bit for any ongoing verifications to complete
        await asyncio.sleep(2)
        
        # Count high-importance claims that were verified
        high_importance_count = len([c for c in all_claims if c.importance_score >= 0.7])
        
        # Send completion
        await manager.send_message(session_id, {
            "type": "complete",
            "status": "completed",
            "message": f"Processing complete. Extracted {len(all_claims)} claims, verified {high_importance_count} high-importance claims.",
            "summary": {
                "total_claims": len(all_claims),
                "verified_claims": high_importance_count,
                "video_id": video_id
            }
        })
        
    except Exception as e:
        await manager.send_message(session_id, {
            "type": "error",
            "status": "error",
            "message": f"Error processing video: {str(e)}"
        })
        raise

# REST Endpoints
@app.get("/")
async def root():
    return {"message": "Fact-Check API is running", "version": "1.0.0"}

@app.get("/test-video/{video_id}")
async def test_video(video_id: str):
    """Test endpoint to check if we can fetch transcript for a video."""
    try:
        transcript = fetch_transcript(video_id)
        return {
            "success": True,
            "video_id": video_id,
            "transcript_segments": len(transcript),
            "first_segment": transcript[0] if transcript else None
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "video_id": video_id
        }

@app.post("/process-video", response_model=ProcessVideoResponse)
async def process_video(request: ProcessVideoRequest, background_tasks: BackgroundTasks):
    """
    Start processing a YouTube video for claim extraction and verification.
    Returns a session ID that can be used to connect via WebSocket for real-time updates.
    """
    session_id = request.session_id or str(uuid.uuid4())
    
    # Create session
    manager.create_session(session_id, request.video_id)
    
    # Start processing in background
    background_tasks.add_task(process_video_pipeline, request.video_id, session_id)
    
    return ProcessVideoResponse(
        session_id=session_id,
        status="processing",
        message=f"Started processing video {request.video_id}. Connect to WebSocket with session_id for updates."
    )

@app.get("/session/{session_id}")
async def get_session(session_id: str):
    """Get the current status of a processing session."""
    session = manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

# WebSocket endpoint
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket connection for real-time updates during video processing.
    """
    await manager.connect(websocket, session_id)
    try:
        # Send initial connection message
        await manager.send_message(session_id, {
            "type": "connected",
            "message": f"Connected to session {session_id}"
        })
        
        # Keep connection alive
        while True:
            # Wait for any messages from client (like ping/pong)
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(session_id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
