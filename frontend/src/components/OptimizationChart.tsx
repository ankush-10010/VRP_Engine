import React from 'react';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import type { OptimizationLogEntry } from '../api/api';

ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend
);

interface Props {
    log: OptimizationLogEntry[];
}

const OptimizationChart: React.FC<Props> = ({ log }) => {

    // Filter out initial empty state if needed
    const validLog = log.filter(l => l.l2_cost > 0 && l.l3_cost > 0 && l.l2_cost !== Infinity && l.l3_cost !== Infinity);

    const labels = validLog.map(entry => entry.timestamp);

    const data = {
        labels,
        datasets: [
            {
                label: 'Layer 2 (OR-Tools) Cost',
                data: validLog.map(e => e.l2_cost),
                borderColor: 'rgb(53, 162, 235)',
                backgroundColor: 'rgba(53, 162, 235, 0.5)',
                tension: 0.1,
            },
            {
                label: 'Layer 3 (ALNS) Cost',
                data: validLog.map(e => e.l3_cost),
                borderColor: 'rgb(255, 99, 132)',
                backgroundColor: 'rgba(255, 99, 132, 0.5)',
                tension: 0.1,
            },
        ],
    };

    const options = {
        responsive: true,
        plugins: {
            legend: {
                position: 'top' as const,
            },
            title: {
                display: true,
                text: 'Hybrid Solver Performance: L2 vs L3',
            },
            tooltip: {
                callbacks: {
                    afterBody: (context: any) => {
                        const index = context[0].dataIndex;
                        const item = validLog[index];
                        return `Winner: ${item.winner}\nImprovement: ${item.improvement_pct.toFixed(2)}%`;
                    }
                }
            }
        },
        scales: {
            y: {
                beginAtZero: false,
                title: {
                    display: true,
                    text: 'Total Fleet Cost ($)'
                }
            }
        }
    };

    return (
        <div className="bg-white p-4 rounded-lg shadow-md">
            <Line options={options} data={data} height={100} />
            <div className="mt-4 text-xs text-gray-500 text-center">
                Comparing Batch Optimization (OR-Tools) vs Metaheuristic (ALNS) over time.
            </div>
        </div>
    );
};

export default React.memo(OptimizationChart);
