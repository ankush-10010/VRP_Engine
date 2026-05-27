import React, { useRef, useEffect } from 'react';
import type { SimulationEvent } from '../api/api';

interface Props {
    events: SimulationEvent[];
}

const SimulationTimeline: React.FC<Props> = ({ events }) => {
    const bottomRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (bottomRef.current) {
            bottomRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [events]);

    const getEventColor = (type: string) => {
        switch (type) {
            case 'new_order': return 'bg-yellow-100 border-yellow-400 text-yellow-800';
            case 'assignment': return 'bg-green-100 border-green-400 text-green-800';
            case 'optimization': return 'bg-blue-100 border-blue-400 text-blue-800';
            case 'rejected': return 'bg-red-100 border-red-400 text-red-800';
            case 'premium': return 'bg-orange-100 border-orange-400 text-orange-800';
            default: return 'bg-gray-100 border-gray-400 text-gray-800';
        }
    };

    const getIcon = (type: string) => {
        switch (type) {
            case 'new_order': return '📦';
            case 'assignment': return '✅';
            case 'optimization': return '🧠';
            case 'rejected': return '⏳';
            case 'premium': return '🚚';
            default: return 'ℹ️';
        }
    };

    return (
        <div className="h-96 overflow-y-auto p-4 bg-gray-50 rounded-lg shadow-inner border border-gray-200">
            <h3 className="text-lg font-bold mb-4 sticky top-0 bg-gray-50 pb-2 border-b">Simulation Event Log</h3>
            <div className="space-y-3">
                {events.map((event, index) => (
                    <div
                        key={index}
                        className={`p-3 rounded-md border-l-4 text-sm ${getEventColor(event.type)} transition-all duration-300 animate-fade-in`}
                    >
                        <div className="flex justify-between items-start">
                            <span className="font-mono text-xs font-bold opacity-70">{event.time}</span>
                            <span className="text-lg">{getIcon(event.type)}</span>
                        </div>
                        <p className="mt-1 font-medium">{event.description}</p>
                    </div>
                ))}
                <div ref={bottomRef} />
            </div>
        </div>
    );
};

export default React.memo(SimulationTimeline);
