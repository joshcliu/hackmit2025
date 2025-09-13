import { Claim } from '../types';

interface ClaimItemProps {
  claim: Claim;
}

export const ClaimItem = ({ claim }: ClaimItemProps) => (
  <div className="mb-4">
    <div className="flex items-start">
      <span className="text-xs text-gray-500 mr-2">{claim.timestamp}</span>
      <div className="flex-1">
        <p className="text-sm">"{claim.text}"</p>
        {claim.type === 'Opinion' && (
          <div className="text-right">
            <span className="text-xs font-semibold text-red-500">Opinion</span>
            <span className="text-lg font-bold text-red-500 ml-2">{claim.score}</span>
          </div>
        )}
      </div>
    </div>
    <div className="ml-12 mt-1 p-2 bg-gray-100 border border-gray-300 rounded">
        <p className="text-xs">{claim.synthesis}</p>
    </div>
     {claim.type === 'Fact' && (
        <div className="ml-12 mt-2 flex items-center justify-between p-2 bg-green-100 border border-green-300 rounded">
            <div>
                <span className="text-xs font-semibold text-green-700">Fact</span>
            </div>
            <span className="text-lg font-bold text-green-700">{claim.score}</span>
        </div>
    )}
  </div>
);
