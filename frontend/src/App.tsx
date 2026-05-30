import { useState, useEffect } from 'react';
import { LandingPage } from './components/LandingPage';
import { LoadingScreen } from './components/LoadingScreen';
import { ResultsDashboard } from './components/ResultsDashboard';
import { getMatrixStatus } from './api/api';
import type { SimulationResult } from './api/api';

type AppState = 'IDLE' | 'POLLING' | 'COMPLETED' | 'ERROR';

function App() {
  const [appState, setAppState] = useState<AppState>('IDLE');
  const [taskId, setTaskId] = useState<string | null>(null);
  const [statusText, setStatusText] = useState<string>('');
  const [simulationResult, setSimulationResult] = useState<SimulationResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [requestPayload, setRequestPayload] = useState<any>(null);

  const handleUploadStart = (newTaskId: string, payload?: any) => {
    setTaskId(newTaskId);
    if (payload) setRequestPayload(payload);
    setAppState('POLLING');
    setStatusText('Initiating Modal cloud container...');
  };

  useEffect(() => {
    let intervalId: ReturnType<typeof setInterval>;

    if (appState === 'POLLING' && taskId) {
      let pollCount = 0;
      const MAX_POLLS = 450; // 15 minutes timeout at 2s intervals

      intervalId = setInterval(async () => {
        pollCount++;
        if (pollCount > MAX_POLLS) {
          clearInterval(intervalId);
          setAppState('ERROR');
          setError('Task timed out. The cloud worker may have failed.');
          return;
        }

        try {
          const data = await getMatrixStatus(taskId);
          
          if (data.status === 'Completed' || data.status === 'Success') {
            setSimulationResult(data.result || null);
            setAppState('COMPLETED');
            clearInterval(intervalId);
          } else if (data.status === 'Failure') {
            setError(data.error || 'Unknown error occurred during simulation.');
            setAppState('ERROR');
            clearInterval(intervalId);
          } else {
            // Update loading text if backend provides it
            if (data.meta?.message) {
              setStatusText(data.meta.message);
            } else if (data.status === 'Progress') {
               setStatusText('Executing routing heuristics...');
            }
          }
        } catch (err) {
          console.error('Polling error', err);
          // Don't immediately fail on network blips, keep trying until timeout
          setStatusText('Reconnecting to cloud...');
        }
      }, 2000);
    }

    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [appState, taskId]);

  return (
    <div className="min-h-screen bg-background text-on-surface dark">
      {appState === 'IDLE' && <LandingPage onUploadStart={handleUploadStart} />}
      
      {appState === 'POLLING' && <LoadingScreen statusText={statusText} />}
      
      {appState === 'COMPLETED' && simulationResult && (
        <ResultsDashboard 
          result={simulationResult} 
          requestPayload={requestPayload}
          onNewSimulation={() => {
            setSimulationResult(null);
            setTaskId(null);
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
            <p className="mb-6">{error}</p>
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