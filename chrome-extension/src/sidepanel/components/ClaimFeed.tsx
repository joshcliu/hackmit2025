import { useEffect, useRef } from 'react';
import { Claim } from '../types';
import { ClaimItem } from './ClaimItem';

interface ClaimFeedProps {
  claims: Claim[];
  onTimestampClick?: (seconds: number) => void;
  autoScroll?: boolean;
}

export const ClaimFeed = ({ claims, onTimestampClick, autoScroll }: ClaimFeedProps) => {
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new claims are added
  useEffect(() => {
    if (autoScroll && scrollRef.current) {
      scrollRef.current.scrollTo({
        top: scrollRef.current.scrollHeight,
        behavior: 'smooth'
      });
    }
  }, [claims.length, autoScroll]);

  return (
  <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-4 bg-black">
        {claims.map((claim, index) => (
      <ClaimItem key={index} claim={claim} onTimestampClick={onTimestampClick} />
    ))}
  </div>
  );
};
