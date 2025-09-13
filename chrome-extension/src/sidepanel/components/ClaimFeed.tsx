import { Claim } from '../types';
import { ClaimItem } from './ClaimItem';

interface ClaimFeedProps {
  claims: Claim[];
}

export const ClaimFeed = ({ claims }: ClaimFeedProps) => (
  <div className="p-4 flex-1 overflow-y-auto">
    <h2 className="text-lg font-bold mb-2">Title</h2>
    {claims.map((claim, index) => (
      <ClaimItem key={index} claim={claim} />
    ))}
  </div>
);
