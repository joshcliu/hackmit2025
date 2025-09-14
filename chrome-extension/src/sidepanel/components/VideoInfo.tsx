import { GaugeComponent } from './GaugeComponent';
import { Claim } from '../types';

interface VideoInfoProps {
  claims: Claim[];
  videoTitle: string;
}


export const VideoInfo = ({ claims, videoTitle }: VideoInfoProps) => {
  // Only calculate average for verified claims (score >= 0)
  const verifiedClaims = claims.filter(claim => claim.score >= 0);
  const averageScore = verifiedClaims.length > 0
    ? verifiedClaims.reduce((acc, claim) => acc + claim.score, 0) / verifiedClaims.length
    : -1; // -1 indicates no verified claims yet

  // Categorize only verified claims based on score
  const validClaims = verifiedClaims.filter(claim => claim.score >= 7).length;
  const flaggedClaims = verifiedClaims.filter(claim => claim.score >= 4 && claim.score < 7).length;
  const wrongClaims = verifiedClaims.filter(claim => claim.score >= 0 && claim.score < 4).length;

  return (
    <div className="p-4 bg-black border-b border-custom-gold">
      {/* Video Title */}
      <h2 className="text-lg font-bold text-white mb-4 truncate">{videoTitle}</h2>
      
      <div className="flex items-start justify-between gap-6">
        {/* Left side: Claims Tally */}
        <div className="flex-1">
          <h3 className="text-sm font-semibold text-custom-gold uppercase tracking-wider mb-3">Claims Analysis</h3>
          <div className="grid grid-cols-3 gap-3 text-center">
            <div className="bg-black rounded-lg p-3 border border-custom-gold">
              <div className="text-2xl font-bold text-green-500">{validClaims}</div>
              <div className="text-xs text-gray-400 uppercase tracking-wide">Valid</div>
            </div>
            <div className="bg-black rounded-lg p-3 border border-custom-gold">
              <div className="text-2xl font-bold text-yellow-500">{flaggedClaims}</div>
              <div className="text-xs text-gray-400 uppercase tracking-wide">Flagged</div>
            </div>
            <div className="bg-black rounded-lg p-3 border border-custom-gold">
              <div className="text-2xl font-bold text-red-500">{wrongClaims}</div>
              <div className="text-xs text-gray-400 uppercase tracking-wide">Wrong</div>
            </div>
          </div>
        </div>

        {/* Right side: Overall Score */}
        <div className="text-center flex-shrink-0">
          <h3 className="text-sm font-semibold text-custom-gold uppercase tracking-wider">Overall Score</h3>
          <div className="flex flex-col items-center mt-2">
            {averageScore >= 0 ? (
              <>
                <GaugeComponent score={averageScore} />
                <span className="text-xl font-bold text-white mt-1">{averageScore.toFixed(1)}</span>
              </>
            ) : (
              <>
                <div className="w-20 h-20 flex items-center justify-center">
                  <span className="text-gray-500 text-sm">Pending</span>
                </div>
                <span className="text-xl font-bold text-gray-500 mt-1">--</span>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
