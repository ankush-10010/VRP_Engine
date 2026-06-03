import { useState, useEffect } from 'react';
import { LandingPage } from './components/LandingPage';
import { LoadingScreen } from './components/LoadingScreen';
import { ResultsDashboard } from './components/ResultsDashboard';
import type { SimulationResult } from './api/api';

type AppState = 'IDLE' | 'POLLING' | 'STREAMING' | 'COMPLETED' | 'ERROR';

function App() {
  const [appState, setAppState] = useState<AppState>('IDLE');
  const [taskId, setTaskId] = useState<string | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [statusText, setStatusText] = useState<string>('');
  const [simulationResult, setSimulationResult] = useState<SimulationResult | null>(null);
  const [requestPayload, setRequestPayload] = useState<any>(null);

  const handleUploadStart = (newTaskId: string, payload?: any, newJobId?: string) => {
    setTaskId(newTaskId);
    if (newJobId) setJobId(newJobId);
    if (payload) setRequestPayload(payload);
    setAppState('POLLING');
    setStatusText('Initiating Modal cloud container...');
  };

  useEffect(() => {
    let socket: WebSocket | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    let isCompleted = false;

    if (taskId && jobId) {
      const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://ankushraj10010--vrp-optimizer-fastapi-modal-wrapper.modal.run/api/v1';
      const wsProtocol = API_BASE_URL.startsWith('https') ? 'wss' : 'ws';
      const wsBase = API_BASE_URL.replace(/^https?/, wsProtocol);
      const wsUrl = `${wsBase}/simulation/ws/${jobId}/${taskId}`;
      
      const connect = () => {
        socket = new WebSocket(wsUrl);
        
        socket.onopen = () => {
          setStatusText("Optimization running (Live Connection)...");
        };

        socket.onmessage = (event) => {
          const data = JSON.parse(event.data);
          
          if (data.type === 'ping') return;
          
          if (data.type === 'progress') {
            console.log("Progress update:", data.total_cost);
            setStatusText(`Optimizing... Current Cost: $${data.total_cost.toFixed(2)}`);
            
            // Stream directly to the dashboard
            setSimulationResult(prev => {
              if (prev) {
                return { 
                  ...prev, 
                  routes: data.routes, 
                  total_cost: data.total_cost,
                  unassigned: data.unassigned || prev.unassigned,
                  analytics: data.analytics || prev.analytics,
                  optimization_log: data.optimization_log || prev.optimization_log,
                  events: data.events || prev.events,
                  orders_processed: data.orders_processed || prev.orders_processed
                };
              }
              return {
                routes: data.routes,
                total_cost: data.total_cost,
                unassigned: data.unassigned || [],
                optimization_log: data.optimization_log || [],
                events: data.events || [],
                orders_processed: data.orders_processed || 0,
                analytics: data.analytics || {
                  total_orders: 0,
                  assigned_orders: 0,
                  success_rate: 0,
                  avg_wait_time_min: 0,
                  fleet_utilization_pct: 0,
                  total_distance_km: 0
                }
              } as unknown as SimulationResult;
            });
            
            // Move from POLLING (Loading Screen) to STREAMING (Dashboard)
            setAppState(prev => prev === 'POLLING' ? 'STREAMING' : prev);
          }
          
          if (data.type === 'complete') {
            console.log("Algorithm finished.");
            isCompleted = true;
            setSimulationResult(data.results || null);
            setAppState('COMPLETED');
            socket?.close();
          }
        };

        socket.onerror = (error) => {
          console.warn("WebSocket Error (Will attempt reconnect):", error);
        };

        socket.onclose = () => {
          if (!isCompleted) {
            console.log("WebSocket dropped. Attempting to reconnect in 2 seconds...");
            reconnectTimer = setTimeout(() => {
                connect();
            }, 2000);
          }
        };
      };
      
      connect();
    }

    return () => {
      isCompleted = true; // Prevent reconnect loops when component unmounts
      if (reconnectTimer) clearTimeout(reconnectTimer);
      if (socket) socket.close();
    };
  }, [taskId, jobId]);

  return (
    <div className="min-h-screen bg-background text-on-surface dark">
      {appState === 'IDLE' && <LandingPage onUploadStart={handleUploadStart} />}
      
      {appState === 'POLLING' && <LoadingScreen statusText={statusText} />}
      
      {(appState === 'COMPLETED' || appState === 'STREAMING') && simulationResult && (
        <ResultsDashboard 
          result={simulationResult} 
          requestPayload={requestPayload}
          onNewSimulation={() => {
            setSimulationResult(null);
            setTaskId(null);
            setJobId(null);
            setRequestPayload(null);
            setAppState('IDLE');
          }} 
        />
      )}

      {appState === 'ERROR' && (
        <div className="flex flex-col items-center justify-center min-h-screen">
          <div className="bg-error-container text-on-error-container p-8 rounded-xl max-w-lg text-center">
            <span className="material-symbols-outlined text-6xl mb-4">error</span>
            <h2 className="text-2xl font-bold mb-2">Simulation Failed</h2>
            <p className="mb-6">WebSocket connection failed. The backend might be unreachable.</p>
            <button 
              onClick={() => setAppState('IDLE')}
              className="bg-on-error-container text-error-container px-6 py-2 rounded font-bold"
            >
              Go Back
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;