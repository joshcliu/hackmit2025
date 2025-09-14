interface GaugeComponentProps {
  score: number;
}

const getScoreColor = (score: number) => {
  if (score >= 7) return '#22c55e'; // green-500
  if (score >= 4) return '#f59e0b'; // yellow-500
  return '#ef4444'; // red-500
};

export const GaugeComponent = ({ score }: GaugeComponentProps) => {
  if (score === -1) {
    return (
      <div style={{ width: '100px', height: '50px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div className="animate-spin w-6 h-6 border-2 border-gray-400 border-t-transparent rounded-full"></div>
      </div>
    );
  }
  const normalizedScore = Math.max(0, Math.min(10, score));
  const rotation = (normalizedScore / 10) * 180 - 90;
  const color = getScoreColor(score);

  return (
    <div style={{ position: 'relative', width: '100px', height: '50px', overflow: 'hidden' }}>
      <svg viewBox="0 0 100 50" style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%' }}>
        <defs>
          <linearGradient id="gaugeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" style={{ stopColor: '#ef4444' }} />
            <stop offset="50%" style={{ stopColor: '#f59e0b' }} />
            <stop offset="100%" style={{ stopColor: '#22c55e' }} />
          </linearGradient>
        </defs>
        <path
          d="M 10 50 A 40 40 0 0 1 90 50"
          fill="none"
          stroke="url(#gaugeGradient)"
          strokeWidth="10"
          strokeLinecap="round"
        />
      </svg>
      <div
        style={{
          position: 'absolute',
          bottom: '0px',
          left: '50%',
          width: '2px',
          height: '40px',
          background: color,
          transformOrigin: 'bottom center',
          transform: `translateX(-50%) rotate(${rotation}deg)`,
          transition: 'transform 0.5s ease-in-out, background 0.5s ease-in-out',
        }}
      ></div>
       <div
        style={{
          position: 'absolute',
          bottom: '-5px',
          left: '50%',
          width: '10px',
          height: '10px',
          borderRadius: '50%',
          background: color,
          transform: 'translateX(-50%)',
          transition: 'background 0.5s ease-in-out',
        }}
      />
    </div>
  );
};
