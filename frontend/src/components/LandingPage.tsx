import React, { useState } from 'react';
import { uploadSimulationCsv } from '../api/api';

export const LandingPage: React.FC<{ onUploadStart: (taskId: string) => void }> = ({ onUploadStart }) => {
  const [strategy, setStrategy] = useState('benchmark');
  const [numVehicles, setNumVehicles] = useState(10);
  const [vehicleCapacity, setVehicleCapacity] = useState(20);
  
  // ALNS Hyperparameters
  const [alnsIterations, setAlnsIterations] = useState(5000);
  const [alnsSegmentLength, setAlnsSegmentLength] = useState(50);
  const [alnsReactionFactor, setAlnsReactionFactor] = useState(0.7);
  const [alnsDestroyMin, setAlnsDestroyMin] = useState(0.15);
  const [alnsDestroyMax, setAlnsDestroyMax] = useState(0.40);
  
  // Other Hyperparameters
  const [layer2Interval, setLayer2Interval] = useState(600);
  const [fixedCost, setFixedCost] = useState(5000);
  const [variableCost, setVariableCost] = useState(15);
  
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [matrixMode, setMatrixMode] = useState('scratch');
  const [matrixFile, setMatrixFile] = useState<File | null>(null);
  const [useDefaultCsv, setUseDefaultCsv] = useState(false);



  const handleStartSimulation = async () => {
    try {
      const settings = {
        strategy,
        num_vehicles: numVehicles,
        vehicle_capacity: vehicleCapacity,
        alns_iterations: alnsIterations,
        alns_segment_length: alnsSegmentLength,
        alns_reaction_factor: alnsReactionFactor,
        alns_destroy_min_pct: alnsDestroyMin,
        alns_destroy_max_pct: alnsDestroyMax,
        layer_2_interval: layer2Interval,
        fixed_cost_per_truck: fixedCost,
        variable_cost_per_km: variableCost,
        alns_enabled: strategy === 'benchmark' || strategy === 'alns',
      };
      const response = await uploadSimulationCsv(file, useDefaultCsv, settings, matrixMode, matrixFile);
      onUploadStart(response.task_id);
    } catch (error) {
      console.error("Failed to start simulation", error);
      alert("Failed to start simulation. Please check backend connection.");
    }
  };

  return (
    <div className="bg-background text-on-surface font-body-md min-h-screen overflow-x-hidden selection:bg-primary-container selection:text-on-primary-container">
      {/* TopNavBar: Dashboard is Active by intent (Config is a dashboard action) */}
      <nav className="bg-surface/70 backdrop-blur-xl flex justify-between items-center px-margin-desktop h-20 w-full fixed top-0 z-50 border-b border-white/10 shadow-2xl">
        <div className="flex items-center gap-gutter">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-primary text-3xl" style={{ fontVariationSettings: "'FILL' 1" }}>hub</span>
            <span className="font-headline-lg text-headline-lg font-bold text-primary tracking-tighter">VRP Engine</span>
          </div>
        </div>
      </nav>

      {/* Main Canvas */}
      <main className="pt-32 pb-24 px-margin-mobile md:px-margin-desktop max-w-container-max mx-auto relative z-10 flex flex-col gap-16">
        
        {/* Ambient Glow Elements */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-primary/20 blur-[120px] rounded-full pointer-events-none -z-10"></div>
        <div className="absolute bottom-0 right-0 w-[500px] h-[500px] bg-secondary-container/10 blur-[100px] rounded-full pointer-events-none -z-10"></div>
        
        {/* Hero Section */}
        <section className="flex flex-col items-center text-center gap-6 max-w-4xl mx-auto">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-surface-container-highest border border-outline-variant text-primary font-label-caps text-label-caps">
            <span className="w-2 h-2 rounded-full bg-primary animate-pulse"></span>
            Engine Status: Online
          </div>
          <h1 className="font-headline-xl text-headline-xl text-on-surface">
            Fleet Optimization via <br className="hidden md:block" />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-secondary">Advanced Heuristics</span>
          </h1>
          <p className="font-body-md text-body-md text-on-surface-variant max-w-2xl">
            Leverage Adaptive Large Neighborhood Search (ALNS) and Tabu strategies to rapidly solve NP-Hard Vehicle Routing Problems. Configure your parameters below to initialize the solver.
          </p>
        </section>

        {/* Main Configuration Card (Glassmorphism Level 2) */}
        <section className="bg-surface-container/70 backdrop-blur-xl border border-white/10 rounded-xl p-8 md:p-gutter shadow-[0_20px_40px_rgba(0,0,0,0.4)] relative overflow-hidden">
          {/* Subtle Top Glow */}
          <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-primary/50 to-transparent"></div>       
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-gutter">
            
            {/* Left Column: Configuration */}
            <div className="flex flex-col gap-8">
              <div>
                <h2 className="font-headline-lg text-headline-lg-mobile md:text-headline-lg text-on-surface flex items-center gap-3 mb-2">       
                  <span className="material-symbols-outlined text-primary">tune</span>
                  Algorithm Strategy
                </h2>
                <p className="text-on-surface-variant font-body-sm text-body-sm">Define solver constraints and selection logic.</p>
              </div>

              <div className="flex flex-col gap-6">
                {/* Strategy Dropdown */}
                <div className="flex flex-col gap-2">
                  <label className="font-label-caps text-label-caps text-on-surface-variant">SOLVER BENCHMARK</label>
                  <div className="relative">
                    <select 
                      value={strategy}
                      onChange={(e) => setStrategy(e.target.value)}
                      className="w-full bg-surface-container-lowest border border-outline-variant text-on-surface rounded-lg px-4 py-3 appearance-none focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-colors font-body-md text-body-md cursor-pointer">
                      <option value="benchmark">Benchmark (ALNS vs OR-Tools)</option>
                      <option value="alns">ALNS Only</option>
                      <option value="ortools">OR-Tools Only</option>
                    </select>
                    <span className="material-symbols-outlined absolute right-4 top-1/2 -translate-y-1/2 text-on-surface-variant pointer-events-none">expand_more</span>
                  </div>
                </div>

                {/* Numeric Inputs (Monospaced) */}
                <div className="grid grid-cols-2 gap-6">
                  <div className="flex flex-col gap-2 group">
                    <label className="font-label-caps text-label-caps text-on-surface-variant">FLEET SIZE</label>
                    <div className="relative">
                      <input 
                        type="number" 
                        value={numVehicles}
                        onChange={(e) => setNumVehicles(parseInt(e.target.value))}
                        className="w-full bg-surface-container-lowest border border-outline-variant text-primary rounded-lg px-4 py-3 font-data-display text-data-display focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-colors" 
                      />
                    </div>
                  </div>
                  <div className="flex flex-col gap-2 group">
                    <label className="font-label-caps text-label-caps text-on-surface-variant">VEHICLE CAPACITY</label>
                    <div className="relative">
                      <input 
                        type="number" 
                        value={vehicleCapacity}
                        onChange={(e) => setVehicleCapacity(parseInt(e.target.value))}
                        className="w-full bg-surface-container-lowest border border-outline-variant text-primary rounded-lg px-4 py-3 font-data-display text-data-display focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-colors" 
                      />
                    </div>
                  </div>
                </div>

                <div className="mt-6">
                  <button 
                    onClick={() => setShowAdvanced(!showAdvanced)}
                    className="w-full flex items-center justify-between text-on-surface-variant hover:text-primary transition-colors group mb-4"
                  >
                    <div className="flex items-center gap-2">
                      <span className="material-symbols-outlined text-[20px]">settings</span>
                      <span className="font-label-caps text-label-caps">ADVANCED HYPERPARAMETERS</span>
                    </div>
                    <span className={`material-symbols-outlined transition-transform ${showAdvanced ? 'rotate-180' : ''}`}>expand_more</span>
                  </button>

                  {showAdvanced && (
                    <div className="flex flex-col gap-6 p-4 bg-surface-container-lowest/30 rounded-lg border border-outline-variant/50">      
                      <div className="grid grid-cols-2 gap-4">
                        <div className="flex flex-col gap-2">
                          <label className="font-label-caps text-label-caps text-on-surface-variant">ITERATIONS</label>
                          <input 
                            type="number" 
                            value={alnsIterations}
                            onChange={(e) => setAlnsIterations(parseInt(e.target.value))}
                            className="w-full bg-surface-container-lowest border border-outline-variant text-primary rounded-lg px-3 py-2 font-data-display text-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-colors" 
                          />
                        </div>
                        <div className="flex flex-col gap-2">
                          <label className="font-label-caps text-label-caps text-on-surface-variant">SEGMENT LENGTH</label>
                          <input 
                            type="number" 
                            value={alnsSegmentLength}
                            onChange={(e) => setAlnsSegmentLength(parseInt(e.target.value))}
                            className="w-full bg-surface-container-lowest border border-outline-variant text-primary rounded-lg px-3 py-2 font-data-display text-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-colors" 
                          />
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <div className="flex flex-col gap-2">
                          <label className="font-label-caps text-label-caps text-on-surface-variant">REACTION FACTOR</label>
                          <input 
                            type="number" step="0.1" 
                            value={alnsReactionFactor}
                            onChange={(e) => setAlnsReactionFactor(parseFloat(e.target.value))}
                            className="w-full bg-surface-container-lowest border border-outline-variant text-primary rounded-lg px-3 py-2 font-data-display text-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-colors" 
                          />
                        </div>
                        <div className="flex flex-col gap-2">
                          <label className="font-label-caps text-label-caps text-on-surface-variant">DESTROY BOUNDS (%)</label>
                          <div className="grid grid-cols-2 gap-2">
                            <input 
                              type="number" 
                              value={alnsDestroyMin * 100}
                              onChange={(e) => setAlnsDestroyMin(parseFloat(e.target.value) / 100)}
                              className="w-full bg-surface-container-lowest border border-outline-variant text-primary rounded-lg px-2 py-2 font-data-display text-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-colors text-center" 
                            />
                            <input 
                              type="number" 
                              value={alnsDestroyMax * 100}
                              onChange={(e) => setAlnsDestroyMax(parseFloat(e.target.value) / 100)}
                              className="w-full bg-surface-container-lowest border border-outline-variant text-primary rounded-lg px-2 py-2 font-data-display text-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-colors text-center" 
                            />
                          </div>
                        </div>
                      </div>
                      
                      {/* Divider */}
                      <div className="h-px bg-outline-variant/30 my-2"></div>
                      
                      <div className="grid grid-cols-2 gap-4">
                        <div className="flex flex-col gap-2">
                          <label className="font-label-caps text-label-caps text-on-surface-variant">OPTIMIZATION INTERVAL (SEC)</label>
                          <input 
                            type="number" 
                            value={layer2Interval}
                            onChange={(e) => setLayer2Interval(parseInt(e.target.value))}
                            className="w-full bg-surface-container-lowest border border-outline-variant text-primary rounded-lg px-3 py-2 font-data-display text-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-colors" 
                          />
                        </div>
                        <div className="flex flex-col gap-2">
                          <label className="font-label-caps text-label-caps text-on-surface-variant">COSTS (FIXED / KM)</label>
                          <div className="grid grid-cols-2 gap-2">
                            <input 
                              type="number" 
                              value={fixedCost}
                              onChange={(e) => setFixedCost(parseInt(e.target.value))}
                              className="w-full bg-surface-container-lowest border border-outline-variant text-primary rounded-lg px-2 py-2 font-data-display text-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-colors text-center" 
                              title="Fixed Cost Per Truck"
                            />
                            <input 
                              type="number" 
                              value={variableCost}
                              onChange={(e) => setVariableCost(parseInt(e.target.value))}
                              className="w-full bg-surface-container-lowest border border-outline-variant text-primary rounded-lg px-2 py-2 font-data-display text-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-colors text-center" 
                              title="Variable Cost Per KM"
                            />
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
            
            {/* Right Column: Upload Zone */}
            <div className="flex flex-col gap-8">
              <div className="flex justify-between items-end mb-2">
                <h2 className="font-headline-lg text-headline-lg-mobile md:text-headline-lg text-on-surface flex items-center gap-3">
                  <span className="material-symbols-outlined text-secondary">settings_input_component</span> Simulation Setup
                </h2>
              </div>

              {/* Routing Engine Mode Selector */}
              <div className="flex flex-col gap-4 mt-2">
                <label className="font-label-caps text-label-caps text-on-surface-variant">ROUTING ENGINE MODE</label>
                <div className="flex flex-col gap-3">
                  <label className={`relative flex items-center p-4 rounded-xl border ${matrixMode === 'scratch' ? 'border-primary' : 'border-outline-variant'} bg-surface-container-low hover:border-primary transition-all cursor-pointer group`}>
                    <input type="radio" name="routing_mode" value="scratch" className="sr-only peer" checked={matrixMode === 'scratch'} onChange={() => setMatrixMode('scratch')} />
                    <div className={`w-5 h-5 rounded-full border-2 ${matrixMode === 'scratch' ? 'border-primary' : 'border-outline-variant'} flex items-center justify-center mr-4 transition-colors`}>
                      <div className={`w-2.5 h-2.5 rounded-full bg-primary transition-opacity ${matrixMode === 'scratch' ? 'opacity-100' : 'opacity-0'}`}></div>
                    </div>
                    <div className="flex flex-col">
                      <span className="font-body-md text-on-surface group-hover:text-primary transition-colors">Calculate from Scratch</span>
                      <span className="font-data-display text-[12px] text-on-surface-variant">Slower. Geocodes all locations and queries live traffic data.</span>
                    </div>
                  </label>
                  <label className={`relative flex items-center p-4 rounded-xl border ${matrixMode === 'database' ? 'border-primary' : 'border-outline-variant'} bg-surface-container-low hover:border-primary transition-all cursor-pointer group`}>
                    <input type="radio" name="routing_mode" value="database" className="sr-only peer" checked={matrixMode === 'database'} onChange={() => setMatrixMode('database')} />
                    <div className={`w-5 h-5 rounded-full border-2 ${matrixMode === 'database' ? 'border-primary' : 'border-outline-variant'} flex items-center justify-center mr-4 transition-colors`}>
                      <div className={`w-2.5 h-2.5 rounded-full bg-primary transition-opacity ${matrixMode === 'database' ? 'opacity-100' : 'opacity-0'}`}></div>
                    </div>
                    <div className="flex flex-col">
                      <span className="font-body-md text-on-surface group-hover:text-primary transition-colors">Use Master Database Matrix</span>
                      <span className="font-data-display text-[12px] text-on-surface-variant">Fastest. Uses pre-computed travel times for known locations.</span>
                    </div>
                  </label>
                  <label className={`relative flex items-center p-4 rounded-xl border ${matrixMode === 'upload' ? 'border-primary' : 'border-outline-variant'} bg-surface-container-low hover:border-primary transition-all cursor-pointer group`}>
                    <input type="radio" name="routing_mode" value="upload" className="sr-only peer" checked={matrixMode === 'upload'} onChange={() => setMatrixMode('upload')} />
                    <div className={`w-5 h-5 rounded-full border-2 ${matrixMode === 'upload' ? 'border-primary' : 'border-outline-variant'} flex items-center justify-center mr-4 transition-colors`}>
                      <div className={`w-2.5 h-2.5 rounded-full bg-primary transition-opacity ${matrixMode === 'upload' ? 'opacity-100' : 'opacity-0'}`}></div>
                    </div>
                    <div className="flex flex-col">
                      <span className="font-body-md text-on-surface group-hover:text-primary transition-colors">Upload Custom Matrix</span>
                      <span className="font-data-display text-[12px] text-on-surface-variant">Provide your own JSON matrix.</span>
                    </div>
                  </label>
                </div>
              </div>

              {/* Dynamic Upload Dialog Area */}
              <div className="bg-surface-container-high/50 backdrop-blur-md rounded-xl p-6 border border-outline-variant flex flex-col gap-4">
                
                {matrixMode === 'scratch' && (
                  <div className="flex flex-col gap-2">
                    <label className="font-label-caps text-label-caps text-on-surface-variant">ORDERS DATA</label>
                    <div className="relative border border-dashed border-outline-variant rounded-lg flex flex-col items-center justify-center p-4 bg-surface-container-lowest/50 hover:bg-surface-container-lowest hover:border-primary transition-all group cursor-pointer overflow-hidden">
                      <input type="file" accept=".csv" className="absolute inset-0 w-full h-full opacity-0 cursor-pointer" onChange={(e) => setFile(e.target.files ? e.target.files[0] : null)} />
                      <span className="material-symbols-outlined text-outline-variant group-hover:text-primary mb-1 transition-colors">upload_file</span>
                      <p className="font-body-sm text-body-sm text-on-surface mb-1">{file ? file.name : "Upload Orders CSV"}</p>
                      <p className="font-label-caps text-[10px] text-on-surface-variant">Max 50MB &bull; .csv</p>
                    </div>
                  </div>
                )}

                {matrixMode === 'database' && (
                  <div className="flex flex-col gap-4">
                    <div className="flex flex-col gap-2">
                      <label className="font-label-caps text-label-caps text-on-surface-variant">ORDERS DATA</label>
                      <div className="relative border border-dashed border-outline-variant rounded-lg flex flex-col items-center justify-center p-4 bg-surface-container-lowest/50 hover:bg-surface-container-lowest hover:border-primary transition-all group cursor-pointer overflow-hidden">
                        <input type="file" accept=".csv" className="absolute inset-0 w-full h-full opacity-0 cursor-pointer" onChange={(e) => setFile(e.target.files ? e.target.files[0] : null)} />
                        <span className="material-symbols-outlined text-outline-variant group-hover:text-primary mb-1 transition-colors">upload_file</span>
                        <p className="font-body-sm text-body-sm text-on-surface mb-1">{file ? file.name : "Upload Orders CSV"}</p>
                        <p className="font-label-caps text-[10px] text-on-surface-variant">Max 50MB &bull; .csv</p>
                      </div>
                    </div>
                    <div className="flex items-start gap-2 p-3 rounded bg-surface-container-highest border border-outline-variant/50">
                      <span className="material-symbols-outlined text-secondary text-sm mt-0.5">info</span>
                      <p className="font-body-sm text-body-sm text-on-surface-variant">Distance matrix will be taken from the database.</p>
                    </div>
                  </div>
                )}

                {matrixMode === 'upload' && (
                  <div className="grid grid-cols-2 gap-4">
                    <div className="flex flex-col gap-2">
                      <label className="font-label-caps text-label-caps text-on-surface-variant">ORDERS DATA</label>
                      <div className="relative border border-dashed border-outline-variant rounded-lg flex flex-col items-center justify-center p-4 bg-surface-container-lowest/50 hover:bg-surface-container-lowest hover:border-primary transition-all group cursor-pointer h-full overflow-hidden">
                        <input type="file" accept=".csv" className="absolute inset-0 w-full h-full opacity-0 cursor-pointer" onChange={(e) => setFile(e.target.files ? e.target.files[0] : null)} />
                        <span className="material-symbols-outlined text-outline-variant group-hover:text-primary mb-1 transition-colors">upload_file</span>
                        <p className="font-body-sm text-body-sm text-on-surface mb-1 text-center">{file ? file.name : "Orders CSV"}</p>
                        <p className="font-label-caps text-[10px] text-on-surface-variant">Max 50MB</p>
                      </div>
                    </div>
                    <div className="flex flex-col gap-2">
                      <label className="font-label-caps text-label-caps text-on-surface-variant">DISTANCE MATRIX</label>
                      <div className="relative border border-dashed border-outline-variant rounded-lg flex flex-col items-center justify-center p-4 bg-surface-container-lowest/50 hover:bg-surface-container-lowest hover:border-secondary transition-all group cursor-pointer h-full overflow-hidden">
                        <input type="file" accept=".json" className="absolute inset-0 w-full h-full opacity-0 cursor-pointer" onChange={(e) => setMatrixFile(e.target.files ? e.target.files[0] : null)} />
                        <span className="material-symbols-outlined text-outline-variant group-hover:text-secondary mb-1 transition-colors">upload_file</span>
                        <p className="font-body-sm text-body-sm text-on-surface mb-1 text-center">{matrixFile ? matrixFile.name : "Matrix JSON"}</p>
                        <p className="font-label-caps text-[10px] text-on-surface-variant">Max 100MB</p>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              <div className="flex justify-between items-center mt-2">
                <label className="flex items-center gap-2 cursor-pointer group">
                  <div className="relative flex items-center">
                    <input 
                      type="checkbox" 
                      className="peer sr-only" 
                      checked={useDefaultCsv} 
                      onChange={(e) => {
                        setUseDefaultCsv(e.target.checked);
                        if (e.target.checked) setFile(null);
                      }} 
                    />
                    <div className="w-5 h-5 border-2 border-outline-variant rounded peer-checked:bg-primary peer-checked:border-primary flex items-center justify-center transition-colors">
                      <span className="material-symbols-outlined text-[14px] text-white opacity-0 peer-checked:opacity-100 transition-opacity">check</span>
                    </div>
                  </div>
                  <span className="font-body-sm text-on-surface-variant group-hover:text-on-surface transition-colors">Use Default Database CSV (Skip Upload)</span>
                </label>
                <a href="#" className="text-primary hover:text-primary-fixed flex items-center gap-1 font-body-sm text-body-sm transition-colors">
                  <span className="material-symbols-outlined text-sm">download</span>
                  Download Template CSV
                </a>
              </div>

              {/* Primary Action Button */}
              <button 
                onClick={handleStartSimulation}
                disabled={(!file && !useDefaultCsv) || (matrixMode === 'upload' && !matrixFile)}
                className={`w-full mt-auto relative group overflow-hidden rounded-xl p-[1px] focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 focus:ring-offset-background ${((!file && !useDefaultCsv) || (matrixMode === 'upload' && !matrixFile)) ? 'opacity-50 cursor-not-allowed grayscale' : ''}`}
              >
                <span className={`absolute inset-0 bg-gradient-to-r from-primary via-secondary to-primary bg-[length:200%_auto] animate-[gradient_2s_linear_infinite] opacity-70 transition-opacity ${((!file && !useDefaultCsv) || (matrixMode === 'upload' && !matrixFile)) ? '' : 'group-hover:opacity-100'}`}></span>
                <div className="relative bg-gradient-to-b from-[#1E293B] to-[#0F172A] px-8 py-5 rounded-[11px] flex items-center justify-center gap-3 transition-transform group-active:scale-[0.98]">
                  <div className="absolute top-0 left-0 right-0 h-[1px] bg-white/20 rounded-t-[11px]"></div>
                  <span className="font-label-caps text-label-caps text-white tracking-widest text-lg">
                    {useDefaultCsv ? 'Run Simulation (Default Data)' : file ? 'Run Simulation' : 'Upload Data to Start'}
                  </span>
                  <span className="material-symbols-outlined text-white" style={{ fontVariationSettings: "'FILL' 1" }}>play_arrow</span>
                </div>
              </button>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
};