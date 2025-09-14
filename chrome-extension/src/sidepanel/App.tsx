import { useState, useEffect, useCallback, useRef } from 'react';
import { Claim } from './types';
import { ClaimFeed } from './components/ClaimFeed';
import { VideoInfo } from './components/VideoInfo';
import { StartMenu } from './components/StartMenu';
import { Footer } from './components/Footer';
import { api, WebSocketMessage, Claim as APIClaim } from '../services/api';

export default function App() {
  const [isStarted, setIsStarted] = useState(false);
  const [videoTitle, setVideoTitle] = useState('');
  const [videoId, setVideoId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingStatus, setProcessingStatus] = useState<string>('');
  const [currentVideoTime, setCurrentVideoTime] = useState<number>(0);
  const [scrollToClaimText, setScrollToClaimText] = useState<string | null>(null);
  const [claims, setClaims] = useState<Claim[]>([]);
  const [serverAvailable, setServerAvailable] = useState(true);
  const sessionIdRef = useRef<string | null>(null);

  // Convert API claim to UI claim format
  const convertClaim = (apiClaim: APIClaim): Claim => {
    // Convert seconds to MM:SS format
    const formatTime = (seconds: number): string => {
      const mins = Math.floor(seconds / 60);
      const secs = Math.floor(seconds % 60);
      return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    };

    // Determine type based on verification status
    const type = apiClaim.verification_status ? 'Fact' : 'Opinion';

    // Only use verification score if available, otherwise don't show a score
    const score = apiClaim.verification_score !== undefined 
      ? apiClaim.verification_score 
      : -1; // -1 indicates no score to display

    return {
      timestamp: formatTime(apiClaim.start_s),
      text: apiClaim.claim_text,
      type,
      score,
      synthesis: apiClaim.verification_summary || `Speaker: ${apiClaim.speaker}`,
      isVerified: apiClaim.verification_status !== undefined && apiClaim.verification_status !== 'pending',
      startSeconds: apiClaim.start_s, // Keep raw seconds for sorting
      verdict: apiClaim.verification_verdict,
      sources: apiClaim.verification_sources,
    };
  };

  // Handle WebSocket messages
  const handleWebSocketMessage = useCallback((message: WebSocketMessage) => {
    console.log('WebSocket message:', message);

    switch (message.type) {
      case 'status':
        setProcessingStatus(message.message);
        if (message.status === 'error') {
          setError(message.message);
          setIsProcessing(false);
        }
        break;

      case 'claim_extracted':
        setClaims(prev => [...prev, convertClaim(message.claim)]);
        break;

      case 'claim_verified':
        setClaims(prev => {
          const updated = [...prev];
          const index = updated.findIndex(c => c.text === message.claim.claim_text);
          if (index !== -1) {
            updated[index] = convertClaim(message.claim);
          } else {
            updated.push(convertClaim(message.claim));
          }
          return updated;
        });
        break;

      case 'extraction_progress':
        setProcessingStatus(`Processing chunk ${message.chunk}/${message.total_chunks} (${message.claims_found} claims found)`);
        break;

      case 'verification_start':
        setProcessingStatus(`Verifying claim ${message.claim_index}/${message.total_claims}`);
        break;

      case 'complete':
        setProcessingStatus('Processing complete!');
        setIsProcessing(false);
        if (message.summary) {
          console.log('Processing summary:', message.summary);
        }
        break;

      case 'error':
        setError(message.message);
        setIsProcessing(false);
        break;
    }
  }, []);

  const fetchMetadata = useCallback(async () => {
    console.log('[DEBUG] Starting fetchMetadata');
    setIsLoading(true);
    
    try {
      // Check if API server is available
      console.log('[DEBUG] Checking API health...');
      const isHealthy = await api.checkHealth();
      console.log('[DEBUG] API health check result:', isHealthy);
      setServerAvailable(isHealthy);
      
      // Get video metadata and URL from background script
      chrome.runtime.sendMessage({ type: 'get-video-metadata' }, (response) => {
        console.log('[DEBUG] Received response from background:', response);
        setIsLoading(false);
        
        if (chrome.runtime.lastError) {
          console.error('[DEBUG] Chrome runtime error:', chrome.runtime.lastError);
          setError('Extension error: ' + chrome.runtime.lastError.message);
          return;
        }
        
        if (response && response.error) {
          console.error('[DEBUG] Response error:', response.error);
          setError(response.error);
          setVideoTitle('');
          setVideoId(null);
        } else if (response && response.title) {
          console.log('[DEBUG] Got video title:', response.title);
          setVideoTitle(response.title);
          setError(null);
          
          // Get the video URL from the background script
          chrome.runtime.sendMessage({ type: 'get-video-url' }, (urlResponse) => {
            console.log('[DEBUG] Got video URL response:', urlResponse);
            if (urlResponse && urlResponse.url) {
              const extractedId = api.extractVideoId(urlResponse.url);
              console.log('[DEBUG] Extracted video ID:', extractedId);
              setVideoId(extractedId);
            } else {
              console.error('[DEBUG] Failed to get video URL');
            }
          });
        } else {
          console.error('[DEBUG] Unexpected response format:', response);
          setError('Failed to get video information');
        }
      });
    } catch (error) {
      console.error('[DEBUG] Error in fetchMetadata:', error);
      setError('Failed to connect to services');
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    // When the sidepanel opens, it will always be on a valid page,
    // so we just need to fetch the metadata.
    fetchMetadata();
    
    // Cleanup on unmount
    return () => {
      api.disconnect();
    };
  }, [fetchMetadata]);

  // Separate effect for video timestamp updates when processing is active
  useEffect(() => {
    if (!isStarted || !isProcessing) return;

    const updateVideoTime = () => {
      chrome.runtime.sendMessage({ type: 'get-video-timestamp' }, (response) => {
        if (response && typeof response.timestamp === 'number') {
          setCurrentVideoTime(response.timestamp);
        }
      });
    };

    // Update video time immediately and then every second
    updateVideoTime();
    const interval = setInterval(updateVideoTime, 1000);
    
    return () => clearInterval(interval);
  }, [isStarted, isProcessing]);

  const handleStart = async () => {
    console.log('[DEBUG] handleStart called');
    console.log('[DEBUG] serverAvailable:', serverAvailable);
    console.log('[DEBUG] videoId:', videoId);
    
    if (!serverAvailable) {
      setError('Fact-check server is not running. Please start the server first (python api_server.py)');
      return;
    }

    if (!videoId) {
      setError('Could not extract video ID from URL');
      return;
    }

    setIsStarted(true);
    setIsProcessing(true);
    setProcessingStatus('Starting fact-check process...');
    setClaims([]); // Clear any existing claims
    setError(null);

    try {
      // Start processing the video
      console.log('[DEBUG] Starting video processing for ID:', videoId);
      const sessionId = await api.startProcessing(videoId);
      console.log('[DEBUG] Got session ID:', sessionId);
      sessionIdRef.current = sessionId;
      
      // Connect to WebSocket for real-time updates
      console.log('[DEBUG] Connecting WebSocket...');
      api.connectWebSocket(sessionId, handleWebSocketMessage);
    } catch (err) {
      console.error('[DEBUG] Error starting processing:', err);
      setError(err instanceof Error ? err.message : 'Failed to start processing');
      setIsProcessing(false);
      setIsStarted(false);
    }
  };

  const handleCancel = () => {
    setIsStarted(false);
    setIsProcessing(false);
    setProcessingStatus('');
    api.disconnect();
    sessionIdRef.current = null;
  };

    const handleScrollComplete = () => {
    setScrollToClaimText(null);
  };

  // Find the most recent claim that has already been said (start time <= current video time)
  const getCurrentClaim = useCallback(() => {
    if (claims.length === 0) return null;
    
    // Filter claims that have already started (start time <= current time)
    const pastClaims = claims.filter(claim => (claim.startSeconds || 0) <= currentVideoTime);
    
    if (pastClaims.length === 0) return null;
    
    // Find the most recent one (highest start time)
    return pastClaims.reduce((latest, claim) => {
      const claimStartTime = claim.startSeconds || 0;
      const latestStartTime = latest?.startSeconds || 0;
      
      return claimStartTime > latestStartTime ? claim : latest;
    });
  }, [claims, currentVideoTime]);

  const handleTimestampClick = useCallback((seconds: number) => {
    chrome.runtime.sendMessage(
      { type: 'seek-video', seconds },
      (response) => {
        if (response.error) {
          console.error('Error seeking video:', response.error);
          // You could add user feedback here if needed
        }
      }
    );
  }, []);

  return (
    <div className="relative w-full h-full bg-black text-gray-100" style={{ height: '100%' }}>
      {/* Start Menu View */}
      <div
        className={`absolute inset-0 flex flex-col transition-opacity duration-500 ${isStarted ? 'opacity-0 pointer-events-none' : 'opacity-100'}`}>
        <StartMenu 
          onStart={handleStart} 
          error={error || (!serverAvailable ? 'Server not available. Please start the API server.' : null)} 
          isLoading={isLoading} 
        />
      </div>

      {/* Fact-Checking View */}
      <div
        className={`absolute inset-0 flex flex-col transition-opacity duration-500 ${isStarted ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}>
        <VideoInfo 
          claims={claims}
          videoTitle={videoTitle}
        />
        
        {/* Current Claim Bar */}
        {(() => {
          const currentClaim = getCurrentClaim();
          return (
            <div className="px-4 py-2 bg-custom-gold/10 border-b border-custom-gold/30">
              <div className="flex items-center space-x-2">
                <div className="animate-pulse w-2 h-2 bg-custom-gold rounded-full"></div>
                {currentClaim ? (
                  <button 
                    onClick={() => setScrollToClaimText(currentClaim.text)}
                    className="text-sm text-custom-gold hover:text-white transition-colors duration-200 text-left truncate"
                    title={currentClaim.text}
                  >
                    "{currentClaim.text}"
                  </button>
                ) : (
                  <div className="text-sm text-gray-500">
                    No recent claims
                  </div>
                )}
              </div>
            </div>
          );
        })()}
        
        {/* Claims Feed or Loading Message */}
        {claims.length > 0 ? (
          <ClaimFeed 
            claims={claims} 
            onTimestampClick={handleTimestampClick} 
            scrollToClaimText={scrollToClaimText}
            onScrollComplete={handleScrollComplete}
          />
        ) : (
          <div className="flex-1 flex items-center justify-center p-8">
            <div className="text-center">
              {isProcessing ? (
                <>
                  <div className="animate-spin w-12 h-12 border-4 border-custom-gold border-t-transparent rounded-full mx-auto mb-4"></div>
                  <p className="text-gray-400">Processing video transcript...</p>
                  <p className="text-sm text-gray-500 mt-2">This may take a few minutes</p>
                </>
              ) : (
                <p className="text-gray-500">No claims extracted yet</p>
              )}
            </div>
          </div>
        )}
        
        <Footer onCancel={handleCancel} />
      </div>
    </div>
  );
}
