import { PlayCircle } from 'lucide-react';

import { Loader } from 'lucide-react';

interface StartMenuProps {
  onStart: () => void;
  error: string | null;
  isLoading: boolean;
}

export const StartMenu = ({ onStart, error, isLoading }: StartMenuProps) => {
  return (
    <div className="flex-1 flex flex-col items-center justify-center p-8">
    <div className="glowing-card bg-black p-6 py-12 rounded-lg text-center max-w-xs">
      {isLoading ? (
        <Loader className="h-12 w-12 text-custom-gold animate-spin" />
      ) : error ? (
        <>
          <h2 className="text-2xl font-serif font-bold mb-3 text-red-500">Not a YouTube Video</h2>
          <p className="text-base text-gray-400 mb-6">
            Please navigate to a YouTube video page to use this extension.
          </p>
          <button
            disabled
            className="flex items-center justify-center w-full px-6 py-3 bg-transparent border-2 border-gray-600 text-gray-600 font-semibold rounded-lg text-base cursor-not-allowed"
          >
            <PlayCircle className="h-5 w-5 mr-2" />
            Start Fact-Checking
          </button>
        </>
      ) : (
        <>
          <h2 className="text-4xl font-serif font-bold mb-3">Ready to Fact-Check?</h2>
          <p className="text-base text-gray-400 mb-6">
            Click the button below to start analyzing the video.
          </p>
          <button
            onClick={onStart}
            className="flex items-center justify-center w-full px-6 py-3 bg-transparent border-2 border-custom-gold text-custom-gold font-semibold rounded-lg transition-all duration-300 text-base hover:bg-custom-gold hover:text-black hover:shadow-[0_0_15px_rgba(215,181,140,0.5)]"
          >
            <PlayCircle className="h-5 w-5 mr-2" />
            Start Fact-Checking
          </button>
        </>
      )}
    </div>
  </div>
);
};
