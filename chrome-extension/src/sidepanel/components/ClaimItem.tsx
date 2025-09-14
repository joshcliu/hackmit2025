import { useState } from 'react';
import { Claim } from '../types';
import { CheckCircle, AlertCircle } from 'lucide-react';
import { MarkdownRenderer } from './MarkdownRenderer';

// Helper function to convert timestamp string (e.g., "01:23") to seconds
const timestampToSeconds = (timestamp: string): number => {
  const parts = timestamp.split(':').map(Number);
  if (parts.length === 2) {
    return parts[0] * 60 + parts[1]; // mm:ss
  } else if (parts.length === 3) {
    return parts[0] * 3600 + parts[1] * 60 + parts[2]; // hh:mm:ss
  }
  return 0;
};

interface ClaimItemProps {
  claim: Claim;
  onTimestampClick?: (seconds: number) => void;
}

const getScoreColor = (score: number) => {
  if (score >= 7) return 'text-green-500';
  if (score >= 4) return 'text-yellow-500';
  return 'text-red-500';
};

export const ClaimItem = ({ claim, onTimestampClick }: ClaimItemProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const hasScore = claim.score >= 0; // Check if we have a valid score to display

  return (
  <div className="glowing-card bg-black p-4 rounded-lg cursor-pointer" onClick={() => setIsOpen(!isOpen)} >
    <div className="flex items-center justify-between mb-2">
      <div className="flex items-center space-x-2" onClick={(e) => e.stopPropagation()}>
        <span 
          className="text-xs font-mono bg-transparent text-custom-gold px-2 py-1 rounded border border-custom-gold cursor-pointer hover:bg-custom-gold hover:text-black transition-colors duration-200"
          onClick={() => {
            const seconds = timestampToSeconds(claim.timestamp);
            onTimestampClick?.(seconds);
          }}
          title="Click to jump to this time in the video"
        >
          {claim.timestamp}
        </span>
      </div>
      {hasScore ? (
        <div className={`flex items-center font-bold text-base ${getScoreColor(claim.score)}`}>
          {claim.isVerified ? (
            <CheckCircle className="h-5 w-5 mr-1" />
          ) : (
            <AlertCircle className="h-5 w-5 mr-1" />
          )}
          {claim.score.toFixed(1)}
        </div>
      ) : (
        <div className="flex items-center text-gray-500 text-sm">
          <AlertCircle className="h-4 w-4 mr-1" />
          <span>Pending</span>
        </div>
      )}
    </div>
    <div className="mb-3">
      <p className="text-gray-100 mb-2 tracking-wide">{claim.text}</p>
      <p className="text-gray-500" style={{ fontSize: '10px' }}>"{claim.exactQuote}"</p>
    </div>
      <div className={`synthesis-container ${isOpen ? 'open' : ''}`}>
        <div className="synthesis-content">
          {claim.synthesis && (
            <div className="pt-2 mt-2 border-t border-gray-700 space-y-3 max-h-80 overflow-y-auto">
              {claim.verdict && (
                <div className="flex items-center space-x-2">
                  <span className="text-xs uppercase tracking-wider text-gray-500">Verdict:</span>
                  <span className={`text-xs font-semibold uppercase ${
                    claim.verdict === 'TRUE' ? 'text-green-500' :
                    claim.verdict === 'FALSE' ? 'text-red-500' :
                    claim.verdict === 'MISLEADING' ? 'text-orange-500' :
                    claim.verdict === 'PARTIALLY TRUE' ? 'text-yellow-500' :
                    'text-gray-400'
                  }`}>
                    {claim.verdict}
                  </span>
                </div>
              )}
              
              <MarkdownRenderer content={claim.synthesis} className="text-sm" />
              
              {claim.sources && claim.sources.length > 0 && (
                <div className="mt-2">
                  <p className="text-xs uppercase tracking-wider text-gray-500 mb-1">Sources:</p>
                  <ul className="text-xs text-gray-400 space-y-1">
                    {claim.sources.map((source, idx) => (
                      <li key={idx} className="pl-2 border-l border-gray-700">
                        <MarkdownRenderer content={source} className="text-xs" />
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
  </div>
  );
};
