import { Speaker } from '../types';

interface SpeakerAnalysisProps {
    speakers: Speaker[];
}

export const SpeakerAnalysis = ({ speakers }: SpeakerAnalysisProps) => (
    <div className="p-4 border-t border-gray-200">
        {speakers.map((speaker, index) => (
            <div key={index} className="flex justify-between items-center text-sm mb-2">
                <span>{speaker.party} Party - <strong>{speaker.name}</strong></span>
                <span className="text-gray-500">{speaker.truthRate}</span>
            </div>
        ))}
    </div>
);
