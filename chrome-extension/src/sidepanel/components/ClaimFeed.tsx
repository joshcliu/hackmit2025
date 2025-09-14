import { useEffect, useRef } from 'react';
import { Claim } from '../types';
import { ClaimItem } from './ClaimItem';

interface ClaimFeedProps {
  claims: Claim[];
  onTimestampClick?: (seconds: number) => void;
  autoScroll?: boolean;
  scrollToClaimText?: string | null;
  onScrollComplete?: () => void;
}

export const ClaimFeed = ({ claims, onTimestampClick, autoScroll, scrollToClaimText, onScrollComplete }: ClaimFeedProps) => {
  const scrollRef = useRef<HTMLDivElement>(null);

  // Sort claims: verified first, then by timestamp within each group
  const sortedClaims = [...claims].sort((a, b) => {
    // First sort by verification status (verified claims first)
    if (a.isVerified && !b.isVerified) return -1;
    if (!a.isVerified && b.isVerified) return 1;
    
    // Within same verification status, sort by timestamp
    const aSeconds = a.startSeconds || 0;
    const bSeconds = b.startSeconds || 0;
    return aSeconds - bSeconds;
  });

  // Auto-scroll to bottom when new claims are added
  useEffect(() => {
    if (autoScroll && scrollRef.current) {
      scrollRef.current.scrollTo({
        top: scrollRef.current.scrollHeight,
        behavior: 'smooth'
      });
    }
    }, [claims.length, autoScroll]);

  // Scroll to a specific claim when requested
  useEffect(() => {
    if (scrollToClaimText && scrollRef.current) {
      // Find the element with the matching data attribute
      const claimElement = Array.from(
        scrollRef.current.querySelectorAll('[data-claim-text]')
      ).find(
        (el) => (el as HTMLElement).dataset.claimText === scrollToClaimText
      );

      if (claimElement) {
        claimElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
        // Reset the scroll trigger once we've scrolled
        onScrollComplete?.();
      }
    }
  }, [scrollToClaimText, onScrollComplete]);

  // Group claims by verification status for visual separation
  const verifiedClaims = sortedClaims.filter(c => c.isVerified);
  const unverifiedClaims = sortedClaims.filter(c => !c.isVerified);

  return (
  <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-4 bg-black">
    {verifiedClaims.length > 0 && (
      <>
        <div className="text-xs uppercase tracking-wider text-custom-gold mb-2">Verified Claims</div>
        {verifiedClaims.map((claim, index) => (
                    <div key={`verified-${index}`} data-claim-text={claim.text}>
            <ClaimItem claim={claim} onTimestampClick={onTimestampClick} />
          </div>
        ))}
      </>
    )}
    
    {unverifiedClaims.length > 0 && (
      <>
        {verifiedClaims.length > 0 && <div className="mt-6" />}
        <div className="text-xs uppercase tracking-wider text-gray-500 mb-2">Unverified Claims</div>
        {unverifiedClaims.map((claim, index) => (
                    <div key={`unverified-${index}`} data-claim-text={claim.text}>
            <ClaimItem claim={claim} onTimestampClick={onTimestampClick} />
          </div>
        ))}
      </>
    )}
  </div>
  );
};
