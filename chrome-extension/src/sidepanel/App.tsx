import { Claim, Speaker } from './types';
import { Header } from './components/Header';
import { ClaimFeed } from './components/ClaimFeed';
import { SpeakerAnalysis } from './components/SpeakerAnalysis';
import { DebateStats } from './components/DebateStats';

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
];

const speakers: Speaker[] = [
    { name: 'Biden', party: 'Democratic', truthRate: 'Truth Rate: ...' },
    { name: 'Trump', party: 'Republican', truthRate: 'Truth Rate: ...' },
];

export default function App() {
  return (
    <div className="w-[350px] h-full flex flex-col bg-white text-gray-800">
      <Header />
      <ClaimFeed claims={claims} />
      <SpeakerAnalysis speakers={speakers} />
      <DebateStats />
    </div>
  )
}
