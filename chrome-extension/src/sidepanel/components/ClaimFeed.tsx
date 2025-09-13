import { Claim } from '../types';
import { ClaimItem } from './ClaimItem';

interface ClaimFeedProps {
  claims: Claim[];
  onTimestampClick?: (seconds: number) => void;
}

export const ClaimFeed = ({ claims, onTimestampClick }: ClaimFeedProps) => (
  <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-black">
        {claims.map((claim, index) => (
      <ClaimItem key={index} claim={claim} onTimestampClick={onTimestampClick} />
    ))}
  </div>
);
