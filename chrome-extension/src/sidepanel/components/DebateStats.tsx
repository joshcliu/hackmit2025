import { PieChart, Map } from 'lucide-react';

export const DebateStats = () => (
    <div className="p-4 border-t border-gray-200">
        <div className="grid grid-cols-2 gap-4 text-center">
            <div>
                <h3 className="font-semibold">Speaking %</h3>
                <PieChart className="h-24 w-24 mx-auto mt-2 text-gray-400" />
            </div>
            <div>
                <h3 className="font-semibold">Topic Coverage</h3>
                <Map className="h-24 w-24 mx-auto mt-2 text-gray-400" />
            </div>
        </div>
    </div>
);
