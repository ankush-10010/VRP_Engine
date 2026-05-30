import React, { useState } from 'react';
import { uploadSimulationCsv } from '../api/api';
interface Props {
    onUploadStart: () => void;
    onUploadSuccess: (taskId: string) => void;
    onUploadError: (error: string) => void;
}

const UploadZone: React.FC<Props> = ({ onUploadStart, onUploadSuccess, onUploadError }) => {
    const [file, setFile] = useState<File | null>(null);
    const [isUploading, setIsUploading] = useState(false);
    const [showSettings, setShowSettings] = useState(false);

    // Default Settings
    const [settings, setSettings] = useState({
        num_vehicles: 10,
        vehicle_capacity: 50,
        layer_2_interval: 60,
        alns_iterations: 5000,
        fixed_cost_per_truck: 5000,
        variable_cost_per_km: 15,
        alns_enabled: true,
        strategy: "benchmark"
    });

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setFile(e.target.files[0]);
        }
    };

    const handleSettingChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
        const { name, value, type } = e.target;
        const checked = type === 'checkbox' ? (e.target as HTMLInputElement).checked : false;
        setSettings(prev => ({
            ...prev,
            [name]: type === 'checkbox' ? checked : (name === 'strategy' ? value : Number(value))
        }));
    };

    const handleUpload = async () => {
        if (!file) return;

        setIsUploading(true);
        onUploadStart();

        try {
            const result = await uploadSimulationCsv(file, false, settings);
            onUploadSuccess(result.task_id);
        } catch (error: any) {
            console.error("Upload failed", error);
            onUploadError(error.message || "Upload failed");
        } finally {
            setIsUploading(false);
        }
    };

    return (
        <div className="max-w-xl mx-auto">
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-10 text-center hover:bg-gray-50 transition-colors">
                <input
                    type="file"
                    accept=".csv"
                    onChange={handleFileChange}
                    className="hidden"
                    id="file-upload"
                />
                <label htmlFor="file-upload" className="cursor-pointer flex flex-col items-center">
                    <svg className="w-12 h-12 text-gray-400 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                    <span className="text-lg font-medium text-gray-600">
                        {file ? file.name : "Click to select CSV file"}
                    </span>
                    <span className="text-sm text-gray-500 mt-1">Order History CSV</span>
                </label>
            </div>

            {/* Advanced Settings */}
            <div className="mt-6 border rounded-lg bg-white overflow-hidden shadow-sm">
                <button
                    onClick={() => setShowSettings(!showSettings)}
                    className="w-full text-left px-4 py-3 bg-gray-50 text-gray-700 font-medium flex justify-between items-center hover:bg-gray-100"
                >
                    <span>⚙️ Advanced Configuration</span>
                    <span>{showSettings ? '▲' : '▼'}</span>
                </button>

                {showSettings && (
                    <div className="p-4 grid grid-cols-2 gap-4 text-sm">
                        <div>
                            <label className="block text-gray-500 mb-1">Vehicles</label>
                            <input
                                type="number" name="num_vehicles" value={settings.num_vehicles} onChange={handleSettingChange}
                                className="w-full border rounded px-2 py-1"
                            />
                        </div>
                        <div>
                            <label className="block text-gray-500 mb-1">Capacity</label>
                            <input
                                type="number" name="vehicle_capacity" value={settings.vehicle_capacity} onChange={handleSettingChange}
                                className="w-full border rounded px-2 py-1"
                            />
                        </div>
                        <div>
                            <label className="block text-gray-500 mb-1">L2 Interval (sec)</label>
                            <input
                                type="number" name="layer_2_interval" value={settings.layer_2_interval} onChange={handleSettingChange}
                                className="w-full border rounded px-2 py-1"
                            />
                        </div>
                        <div>
                            <label className="block text-gray-500 mb-1">ALNS Iterations</label>
                            <input
                                type="number" name="alns_iterations" value={settings.alns_iterations} onChange={handleSettingChange}
                                className="w-full border rounded px-2 py-1"
                            />
                        </div>
                        <div>
                            <label className="block text-gray-500 mb-1">Fixed Cost / Truck</label>
                            <input
                                type="number" name="fixed_cost_per_truck" value={settings.fixed_cost_per_truck} onChange={handleSettingChange}
                                className="w-full border rounded px-2 py-1"
                            />
                        </div>
                        <div>
                            <label className="block text-gray-500 mb-1">Var Cost / km</label>
                            <input
                                type="number" name="variable_cost_per_km" value={settings.variable_cost_per_km} onChange={handleSettingChange}
                                className="w-full border rounded px-2 py-1"
                            />
                        </div>

                        <div className="col-span-2 flex items-center mt-2">
                            <input
                                type="checkbox" name="alns_enabled" checked={settings.alns_enabled} onChange={handleSettingChange}
                                className="mr-2"
                            />
                            <label>Enable Layer 3 (ALNS Competition)</label>
                        </div>
                    </div>
                )}
            </div>

            <button
                onClick={handleUpload}
                disabled={!file || isUploading}
                className={`mt-6 w-full py-3 rounded-lg font-bold text-white transition-all ${!file || isUploading
                    ? 'bg-gray-400 cursor-not-allowed'
                    : 'bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 shadow-lg transform hover:-translate-y-1'
                    }`}
            >
                {isUploading ? "Process Queued..." : "Run Hybrid Simulation"}
            </button>

            {isUploading && (
                <p className="text-center text-sm text-gray-500 mt-2 animate-pulse">
                    Request sent to queue. Waiting for worker...
                </p>
            )}
        </div>
    );
};

export default UploadZone;
