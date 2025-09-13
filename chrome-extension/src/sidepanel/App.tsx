import { useState, useEffect, useCallback } from 'react';
import { Claim } from './types';
import { ClaimFeed } from './components/ClaimFeed';
import { VideoInfo } from './components/VideoInfo';
import { StartMenu } from './components/StartMenu';
import { Footer } from './components/Footer';

// Placeholder data

const claims: Claim[] = [
  {
    timestamp: '00:06',
    text: 'Our tax plan will create one million new jobs.',
    type: 'Opinion',
    score: 5.6,
    synthesis: 'The Tax Cuts & Jobs Act projected to add 800,000 jobs, not 1 million. - New York Times, 2018; WSJ, 2019',
  },
  {
    timestamp: '00:24',
    text: 'This is a factual statement.',
    type: 'Fact',
    score: 7.5,
    synthesis: 'This is a breakdown of the fact.',
  },
  {
    timestamp: '01:15',
    text: 'The sky is blue because of Rayleigh scattering.',
    type: 'Fact',
    score: 9.2,
    synthesis: 'This is a well-established scientific fact.',
  },
  {
    timestamp: '02:30',
    text: 'The new policy will solve all our problems.',
    type: 'Opinion',
    score: 3.1,
    synthesis: 'This is an exaggeration; the policy addresses specific issues but is not a comprehensive solution.',
  },
  {
    timestamp: '03:45',
    text: 'Water boils at 100 degrees Celsius at sea level.',
    type: 'Fact',
    score: 10.0,
    synthesis: 'This is a fundamental principle of chemistry and physics.',
  },
  {
    timestamp: '04:12',
    text: 'This is the best product on the market.',
    type: 'Opinion',
    score: 4.5,
    synthesis: 'This is a subjective claim and not a verifiable fact.',
  },
];

export default function App() {
  const [isStarted, setIsStarted] = useState(false);
  const [videoTitle, setVideoTitle] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchMetadata = useCallback(() => {
    setIsLoading(true);
    chrome.runtime.sendMessage({ type: 'get-video-metadata' }, (response) => {
      setIsLoading(false);
      if (response.error) {
        setError(response.error);
        setVideoTitle('');
      } else if (response.title) {
        setVideoTitle(response.title);
        setError(null);
      }
    });
  }, []);

  useEffect(() => {
    // When the sidepanel opens, it will always be on a valid page,
    // so we just need to fetch the metadata.
    fetchMetadata();
  }, [fetchMetadata]);

  const handleStart = () => {
    setIsStarted(true);
  };

  const handleCancel = () => {
    setIsStarted(false);
  };

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
        <StartMenu onStart={handleStart} error={error} isLoading={isLoading} />
      </div>

      {/* Fact-Checking View */}
      <div
        className={`absolute inset-0 flex flex-col transition-opacity duration-500 ${isStarted ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}>
        <VideoInfo 
          claims={claims}
          videoTitle={videoTitle}
        />
        <ClaimFeed claims={claims} onTimestampClick={handleTimestampClick} />
        <Footer onCancel={handleCancel} />
      </div>
    </div>
  );
}
