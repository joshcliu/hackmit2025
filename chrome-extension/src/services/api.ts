/**
 * API service for communicating with the backend fact-checking server
 */

const API_BASE_URL = 'http://127.0.0.1:8000';
const WS_BASE_URL = 'ws://127.0.0.1:8000';

export interface Claim {
  video_id: string;
  start_s: number;
  end_s: number;
  claim_text: string;
  speaker: string;
  importance_score: number;
  verification_status?: string;
  verification_score?: number;
  verification_summary?: string;
}

export interface ProcessingStatus {
  type: 'status' | 'error' | 'complete' | 'connected';
  status: string;
  message: string;
  summary?: {
    total_claims: number;
    verified_claims: number;
    video_id: string;
  };
}

export interface ExtractionProgress {
  type: 'extraction_progress';
  chunk: number;
  total_chunks: number;
  claims_found: number;
}

export interface ClaimExtracted {
  type: 'claim_extracted';
  claim: Claim;
}

export interface ClaimVerified {
  type: 'claim_verified';
  claim: Claim;
}

export interface VerificationStart {
  type: 'verification_start';
  claim_index: number;
  total_claims: number;
  claim_text: string;
}

export type WebSocketMessage = 
  | ProcessingStatus 
  | ExtractionProgress 
  | ClaimExtracted 
  | ClaimVerified 
  | VerificationStart;

export class FactCheckAPI {
  private ws: WebSocket | null = null;
  private messageHandlers: Set<(message: WebSocketMessage) => void> = new Set();

  /**
   * Extract video ID from YouTube URL
   */
  extractVideoId(url: string): string | null {
    const match = url.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?#]+)/);
    return match ? match[1] : null;
  }

  /**
   * Start processing a YouTube video
   */
  async startProcessing(videoId: string): Promise<string> {
    try {
      console.log('[API] Starting processing for video:', videoId);
      const requestBody = {
        video_id: videoId,
      };
      console.log('[API] Request body:', requestBody);
      
      const response = await fetch(`${API_BASE_URL}/process-video`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      console.log('[API] Process response status:', response.status);
      
      if (!response.ok) {
        const error = await response.json();
        console.error('[API] Process error response:', error);
        throw new Error(error.detail || 'Failed to start processing');
      }

      const data = await response.json();
      console.log('[API] Process success response:', data);
      return data.session_id;
    } catch (error) {
      console.error('[API] Error starting video processing:', error);
      throw error;
    }
  }

  /**
   * Connect to WebSocket for real-time updates
   */
  connectWebSocket(sessionId: string, onMessage: (message: WebSocketMessage) => void): void {
    // Store the message handler
    this.messageHandlers.add(onMessage);

    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      return; // Already connected
    }

    this.ws = new WebSocket(`${WS_BASE_URL}/ws/${sessionId}`);

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      // Send ping every 30 seconds to keep connection alive
      const pingInterval = setInterval(() => {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
          this.ws.send('ping');
        } else {
          clearInterval(pingInterval);
        }
      }, 30000);
    };

    this.ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data) as WebSocketMessage;
        // Call all registered handlers
        this.messageHandlers.forEach(handler => handler(message));
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
      this.ws = null;
    };
  }

  /**
   * Disconnect WebSocket
   */
  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.messageHandlers.clear();
  }

  /**
   * Get session status
   */
  async getSessionStatus(sessionId: string): Promise<any> {
    try {
      const response = await fetch(`${API_BASE_URL}/session/${sessionId}`);
      
      if (!response.ok) {
        throw new Error('Failed to get session status');
      }

      return await response.json();
    } catch (error) {
      console.error('Error getting session status:', error);
      throw error;
    }
  }

  /**
   * Check if API server is running
   */
  async checkHealth(): Promise<boolean> {
    try {
      console.log('[API] Checking health at:', `${API_BASE_URL}/`);
      const response = await fetch(`${API_BASE_URL}/`);
      console.log('[API] Health check response:', response.status, response.ok);
      if (response.ok) {
        const data = await response.json();
        console.log('[API] Health check data:', data);
      }
      return response.ok;
    } catch (error) {
      console.error('[API] Health check error:', error);
      return false;
    }
  }
}

// Export singleton instance
export const api = new FactCheckAPI();
