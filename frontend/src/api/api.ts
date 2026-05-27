import axios from 'axios';

// --- Types ---

export interface Location {
    original_address: string;
    latitude?: number;
    longitude?: number;
    formatted_address?: string;
}

export interface OptimizationLogEntry {
    iteration: number;
    timestamp: string;
    l1_cost: number;
    l2_cost: number;
    l3_cost: number;
    winner: string;
    improvement_pct: number;
}

export interface SimulationEvent {
    time: string;
    type: "new_order" | "assignment" | "optimization" | "rejected" | "premium";
    description: string;
    success?: boolean;
}

export interface AnalyticsMetrics {
    total_orders: number;
    assigned_orders: number;
    success_rate: number;
    avg_wait_time_min: number;
    fleet_utilization_pct: number;
    total_distance_km: number;
}

export interface RouteStep {
    stop_index: number;
    address: string;
    lat: number;
    lng: number;
    arrival_time_min: number;
    departure_time_min: number;
}

export interface VehicleRoute {
    vehicle_id: number;
    steps: RouteStep[];
    total_cost: number;
    total_time_min: number;
}

export interface SimulationResult {
    status: string;
    orders_processed?: number;
    unique_locations_found?: number;
    routes?: VehicleRoute[];
    total_cost?: number;
    unassigned?: string[];
    analytics?: AnalyticsMetrics;
    optimization_log?: OptimizationLogEntry[];
    events?: SimulationEvent[];
    error?: string;
}

export interface TaskResponse {
    task_id: string;
    status: string;
    filename?: string;
}

// --- API Client ---

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://ankushraj10010--vrp-optimizer-fastapi-modal-wrapper.modal.run/api/v1';

export const uploadSimulationCsv = async (file: File | null, settings: Record<string, any> | null): Promise<TaskResponse> => {
    const formData = new FormData();
    if (file) {
        formData.append('file', file);
    } else {
        // Create a dummy file for demo purposes if none provided
        const blob = new Blob(["dummy,csv\ndata,1"], { type: 'text/csv' });
        const dummyFile = new File([blob], "demo_data.csv", { type: "text/csv" });
        formData.append('file', dummyFile);
    }
    
    if (settings) {
        formData.append('settings', JSON.stringify(settings));
    }

    // Retry logic for Modal Cold Starts (up to 3 retries, 2s delay)
    let retries = 3;
    while (retries > 0) {
        try {
            const response = await axios.post<TaskResponse>(`${API_BASE_URL}/simulation/upload-csv`, formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });
            return response.data;
        } catch (error) {
            retries -= 1;
            if (retries === 0) throw error;
            // Wait 2 seconds before retrying
            await new Promise(resolve => setTimeout(resolve, 2000));
        }
    }
    throw new Error("Failed to upload after retries");
};

export const getMatrixStatus = async (taskId: string): Promise<{ status: string; result?: SimulationResult; meta?: any; error?: string }> => {
    const response = await axios.get(`${API_BASE_URL}/matrix-status/${taskId}`);
    return response.data;
};
