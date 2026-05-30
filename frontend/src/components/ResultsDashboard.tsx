import React, { useState } from 'react';
import type { SimulationResult } from '../api/api';
import ResultsMap from './ResultsMap';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

interface ResultsDashboardProps {
  result: SimulationResult;
  requestPayload?: any;
  onNewSimulation: () => void;
}

export const ResultsDashboard: React.FC<ResultsDashboardProps> = ({ result, requestPayload, onNewSimulation }) => {
  const [activeVehicleIds, setActiveVehicleIds] = useState<number[]>([]);

  const analytics = result.analytics;
  const unassignedCount = result.unassigned ? result.unassigned.length : 0;
  
  // Format optimization log for Recharts
  const chartData = result.optimization_log?.map((log) => ({
    iteration: log.iteration,
    time: log.timestamp,
    L1: log.l1_cost !== 0 ? log.l1_cost : null,
    ORTools: log.l2_cost !== 0 ? log.l2_cost : null,
    ALNS: log.l3_cost !== 0 ? log.l3_cost : null,
  })) || [];

  const handleVehicleToggle = (vId: number) => {
    setActiveVehicleIds(prev => {
      if (prev.length === 0) {
        return [vId];
      }
      if (prev.includes(vId)) {
        return prev.filter(id => id !== vId);
      } else {
        return [...prev, vId];
      }
    });
  };

  const handleExportJSON = () => {
    const exportData = {
      simulation_config: requestPayload,
      summary: {
        total_orders: result.analytics?.total_orders || 0,
        assigned_orders: result.analytics?.assigned_orders || 0,
        unassigned_orders: result.unassigned ? result.unassigned.length : 0,
        success_rate: result.analytics?.success_rate || 0,
        fleet_utilization_pct: result.analytics?.fleet_utilization_pct || 0,
        total_distance_km: result.analytics?.total_distance_km || 0,
        total_cost: result.total_cost || 0
      },
      detailed_result: result
    };
    const jsonString = JSON.stringify(exportData, null, 2);
    const blob = new Blob([jsonString], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = "simulation_result.json";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="bg-background text-on-surface font-body-md antialiased min-h-screen overflow-x-hidden selection:bg-primary-container selection:text-on-primary-container pb-12">
      {/* TopNavBar */}
      <nav className="bg-surface/70 backdrop-blur-xl flex justify-between items-center px-margin-desktop h-20 w-full fixed top-0 z-50 border-b border-white/10 shadow-2xl">
        <div className="flex items-center gap-8">
          <h1 className="font-headline-lg text-headline-lg font-bold text-primary tracking-tighter hidden md:block">VRP Engine</h1>
          <h1 className="font-headline-lg-mobile text-headline-lg-mobile font-bold text-primary tracking-tighter md:hidden">VRP Engine</h1>
        </div>
        <div className="flex items-center gap-6">
          <button 
            onClick={onNewSimulation}
            className="flex bg-gradient-to-r from-primary-container to-secondary-container text-on-primary-container font-label-caps text-label-caps px-6 py-3 rounded-full shadow-[inset_0_1px_0_rgba(255,255,255,0.2)] hover:opacity-90 transition-opacity items-center gap-2"
          >
            <span className="material-symbols-outlined text-[18px]">add</span>
            New Simulation
          </button>
        </div>
      </nav>

      {/* Main Content Canvas */}
      <main className="pt-[104px] px-margin-mobile md:px-margin-desktop max-w-container-max mx-auto space-y-gutter">
        
        {/* Header */}
        <header className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-8">
          <div>
            <h2 className="font-headline-xl text-headline-xl text-on-surface mb-2">Simulation Results</h2>
            <p className="font-body-md text-body-md text-on-surface-variant">Processed: {result.orders_processed} Orders</p>
          </div>
          <div className="flex gap-3">
            <button 
              onClick={handleExportJSON}
              className="bg-surface-container-low/70 backdrop-blur-md border border-white/10 px-4 py-2 rounded-lg font-label-caps text-label-caps text-on-surface hover:bg-surface-bright transition-colors flex items-center gap-2"
            >
              <span className="material-symbols-outlined text-[16px]">download</span> Export JSON
            </button>
          </div>
        </header>

        {/* KPI Ribbon (Top) */}
        <section className="grid grid-cols-2 md:grid-cols-5 gap-unit md:gap-gutter">
          <div className="bg-surface-container-low/70 backdrop-blur-md border border-white/10 p-6 rounded-xl flex flex-col justify-between h-full">
            <p className="font-label-caps text-label-caps text-on-surface-variant mb-4">Total Orders Processed</p>
            <div className="flex items-end justify-between">
              <p className="font-data-display text-data-display text-3xl font-bold text-on-surface">{analytics?.total_orders || 0}</p>
              <span className="material-symbols-outlined text-primary opacity-50 text-3xl">list_alt</span>
            </div>
          </div>

          <div className="bg-surface-container-low/70 backdrop-blur-md border border-white/10 p-6 rounded-xl flex flex-col justify-between h-full border-t-2 border-t-[#34d399]">
            <p className="font-label-caps text-label-caps text-on-surface-variant mb-4">Success Rate</p>
            <div className="flex items-end justify-between">
              <p className="font-data-display text-data-display text-3xl font-bold text-[#34d399]">
                {analytics?.success_rate ? analytics.success_rate.toFixed(1) : 0}%
              </p>
              <span className="material-symbols-outlined text-[#34d399] opacity-50 text-3xl">check_circle</span>
            </div>
          </div>

          <div className="bg-surface-container-low/70 backdrop-blur-md border border-white/10 p-6 rounded-xl flex flex-col justify-between h-full">
            <p className="font-label-caps text-label-caps text-on-surface-variant mb-4">Fleet Utilization</p>
            <div>
              <div className="flex items-end justify-between mb-2">
                <p className="font-data-display text-data-display text-3xl font-bold text-on-surface">
                  {analytics?.fleet_utilization_pct ? analytics.fleet_utilization_pct.toFixed(0) : 0}%
                </p>
                <span className="material-symbols-outlined text-primary opacity-50 text-3xl">local_shipping</span>
              </div>
              <div className="w-full bg-surface-container-highest rounded-full h-1.5">
                <div className="bg-primary h-1.5 rounded-full" style={{ width: `${analytics?.fleet_utilization_pct || 0}%` }}></div>
              </div>
            </div>
          </div>

          <div className="bg-surface-container-low/70 backdrop-blur-md border border-white/10 p-6 rounded-xl flex flex-col justify-between h-full">
            <p className="font-label-caps text-label-caps text-on-surface-variant mb-4">Total Fleet Cost</p>
            <div className="flex items-end justify-between">
              <p className="font-data-display text-data-display text-3xl font-bold text-on-surface">
                ${result.total_cost?.toLocaleString(undefined, { maximumFractionDigits: 0 })}
              </p>
              <span className="material-symbols-outlined text-primary opacity-50 text-3xl">payments</span>
            </div>
          </div>

          <div className={`bg-surface-container-low/70 backdrop-blur-md border border-white/10 p-6 rounded-xl flex flex-col justify-between h-full ${unassignedCount > 0 ? 'border-t-2 border-t-error' : ''}`}>
            <p className="font-label-caps text-label-caps text-on-surface-variant mb-4">Unassigned Orders</p>
            <div className="flex items-end justify-between">
              <p className={`font-data-display text-data-display text-3xl font-bold ${unassignedCount > 0 ? 'text-error' : 'text-[#34d399]'}`}>
                {unassignedCount}
              </p>
              <span className={`material-symbols-outlined opacity-50 text-3xl ${unassignedCount > 0 ? 'text-error' : 'text-[#34d399]'}`}>
                {unassignedCount > 0 ? 'warning' : 'check_circle'}
              </span>
            </div>
          </div>
        </section>

        {/* Middle Row (60/40 Split) */}
        <section className="grid grid-cols-1 lg:grid-cols-12 gap-gutter min-h-[400px]">
          {/* Left (60%): Interactive Route Map Placeholder */}
          <div className="lg:col-span-7 bg-[#0f172a]/70 backdrop-blur-md rounded-xl overflow-hidden flex flex-col relative border border-white/5 shadow-lg">
            <div className="p-6 border-b border-white/10 flex justify-between items-center bg-surface-container-low/50 z-10 flex-wrap gap-4">
              <h3 className="font-headline-lg-mobile text-headline-lg-mobile text-on-surface">Interactive Route Map</h3>
              <div className="flex gap-2 flex-wrap max-w-[60%]">
                <button 
                  onClick={() => setActiveVehicleIds([])}
                  className={`px-3 py-1 rounded-full font-label-caps text-label-caps text-[10px] transition-colors border ${
                    activeVehicleIds.length === 0 
                      ? 'bg-primary/20 text-primary border-primary/50' 
                      : 'bg-surface-container-highest text-on-surface-variant border-white/10 hover:bg-surface-bright'
                  }`}
                >
                  ALL
                </button>
                {result.routes?.map((route) => (
                  <button 
                    key={route.vehicle_id}
                    onClick={() => handleVehicleToggle(route.vehicle_id)}
                    className={`px-3 py-1 rounded-full font-label-caps text-label-caps text-[10px] transition-colors border ${
                      activeVehicleIds.includes(route.vehicle_id) 
                        ? 'bg-primary/20 text-primary border-primary/50' 
                        : 'bg-surface-container-highest text-on-surface-variant border-white/10 hover:bg-surface-bright'
                    }`}
                  >
                    V{route.vehicle_id}
                  </button>
                ))}
              </div>
            </div>
            
            <div className="flex-grow relative flex items-center justify-center bg-[#080c17] w-full">
              <ResultsMap 
                routes={activeVehicleIds.length > 0 && result.routes 
                  ? result.routes.filter(r => activeVehicleIds.includes(r.vehicle_id))
                  : (result.routes || [])} 
              />
            </div>
          </div>

          {/* Right (40%): Algorithm Convergence */}
          <div className="lg:col-span-5 bg-[#0f172a]/70 backdrop-blur-md rounded-xl p-6 flex flex-col relative border border-white/5 shadow-lg">   
            <h3 className="font-headline-lg-mobile text-headline-lg-mobile text-on-surface mb-2">Algorithm Convergence</h3>
            <p className="font-body-sm text-body-sm text-on-surface-variant mb-6">ALNS vs OR-Tools Cost Reduction</p>
            
            <div className="flex-grow w-full h-full min-h-[250px]">
              {chartData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                    <XAxis 
                      dataKey="iteration" 
                      stroke="#8c909f" 
                      tick={{ fill: '#8c909f', fontSize: 12, fontFamily: 'JetBrains Mono' }} 
                      tickFormatter={(value) => `#${value}`}
                    />
                    <YAxis 
                      stroke="#8c909f" 
                      tick={{ fill: '#8c909f', fontSize: 12, fontFamily: 'JetBrains Mono' }}
                      domain={['auto', 'auto']}
                    />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#131b2e', borderColor: '#424754', borderRadius: '8px', color: '#dae2fd' }}
                      itemStyle={{ fontFamily: 'JetBrains Mono', fontSize: '14px' }}
                      labelStyle={{ marginBottom: '8px', color: '#8c909f' }}
                    />
                    <Legend 
                      wrapperStyle={{ paddingTop: '20px' }}
                      iconType="circle"
                    />
                    <Line type="monotone" dataKey="L1" name="L1 (Greedy)" stroke="#ffb4a2" strokeWidth={3} dot={{ r: 3, fill: '#ffb4a2', strokeWidth: 0 }} activeDot={{ r: 6 }} connectNulls />
                    <Line type="monotone" dataKey="ORTools" name="OR-Tools" stroke="#4d8eff" strokeWidth={3} dot={{ r: 3, fill: '#4d8eff', strokeWidth: 0 }} activeDot={{ r: 6 }} connectNulls />
                    <Line type="monotone" dataKey="ALNS" name="ALNS" stroke="#d0bcff" strokeWidth={3} dot={{ r: 3, fill: '#d0bcff', strokeWidth: 0 }} activeDot={{ r: 6 }} connectNulls />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="w-full h-full flex items-center justify-center border border-white/5 rounded-lg bg-surface-container-highest/20">
                  <p className="text-on-surface-variant italic">No optimization convergence data logged.</p>
                </div>
              )}
            </div>
          </div>
        </section>

        {/* Bottom Row (50/50 Split) */}
        <section className="grid grid-cols-1 lg:grid-cols-2 gap-gutter">
          {/* Left: Fleet Manifest */}
          <div className="bg-[#0f172a]/70 backdrop-blur-md rounded-xl p-6 flex flex-col border border-white/5 shadow-lg max-h-[600px] overflow-hidden">
            <h3 className="font-headline-lg-mobile text-headline-lg-mobile text-on-surface mb-6">Fleet Manifest</h3>
            <div className="space-y-4 overflow-y-auto pr-2 custom-scrollbar">
              
              {result.routes?.map((route) => {
                 // Calculate unique stops (excluding depot)
                 const uniqueStops = new Set(route.steps.filter(s => s.stop_index !== 0).map(s => s.stop_index)).size;
                 const isActive = activeVehicleIds.length === 0 || activeVehicleIds.includes(route.vehicle_id);

                 return (
                  <div 
                    key={route.vehicle_id}
                    onClick={() => handleVehicleToggle(route.vehicle_id)}
                    className={`bg-surface-container-low border border-white/5 rounded-lg p-4 transition-all cursor-pointer group ${isActive ? 'ring-1 ring-primary bg-surface-bright/20' : 'hover:bg-surface-bright/30'}`}
                  >
                    <div className="flex justify-between items-center mb-3">
                      <div className="flex items-center gap-3">
                          <span className="material-symbols-outlined text-[20px]">local_shipping</span>
                        <div className={`${isActive ? 'bg-primary/20 text-primary' : 'bg-surface-container-highest text-on-surface-variant'} p-2 rounded-md transition-colors`}>
                        </div>
                        <h4 className="font-data-display text-data-display text-on-surface font-bold text-base">Vehicle {route.vehicle_id}</h4>
                      </div>
                      <span className={`material-symbols-outlined transition-colors ${isActive ? 'text-primary' : 'text-on-surface-variant group-hover:text-primary'}`}>
                        {isActive ? 'visibility' : 'visibility_off'}
                      </span>
                    </div>
                    <div className={`grid grid-cols-3 gap-2 text-center transition-opacity ${isActive ? 'opacity-100' : 'opacity-70'}`}>
                      <div className="bg-background rounded px-2 py-3">
                        <p className="font-label-caps text-label-caps text-on-surface-variant text-[10px] mb-1">Stops</p>
                        <p className="font-data-display text-data-display text-on-surface text-sm">{uniqueStops}</p>
                      </div>
                      <div className="bg-background rounded px-2 py-3">
                        <p className="font-label-caps text-label-caps text-on-surface-variant text-[10px] mb-1">Cost</p>
                        <p className="font-data-display text-data-display text-on-surface text-sm">${route.total_cost.toFixed(0)}</p>
                      </div>
                      <div className="bg-background rounded px-2 py-3">
                        <p className="font-label-caps text-label-caps text-on-surface-variant text-[10px] mb-1">Duration</p>
                        <p className="font-data-display text-data-display text-on-surface text-sm">{route.total_time_min.toFixed(0)} mins</p>
                      </div>
                    </div>
                  </div>
                 );
              })}

            </div>
          </div>

          {/* Right: Simulation Event Log */}
          <div className="bg-[#0f172a]/70 backdrop-blur-md rounded-xl p-6 flex flex-col border border-white/5 shadow-lg max-h-[600px] overflow-hidden">
            <h3 className="font-headline-lg-mobile text-headline-lg-mobile text-on-surface mb-6">Simulation Event Log</h3>
            <div className="relative pl-6 border-l-2 border-surface-container-highest space-y-8 flex-grow overflow-y-auto pr-4 custom-scrollbar pb-8">
              
              {result.events?.map((event, idx) => {
                let dotColor = 'bg-on-surface-variant';
                let textColor = 'text-on-surface-variant';
                let iconGlow = '';
                
                if (event.type === 'new_order') {
                   dotColor = 'bg-[#ffd93d]';
                   textColor = 'text-[#ffd93d]';
                } else if (event.type === 'assignment') {
                   dotColor = event.success ? 'bg-[#34d399]' : 'bg-error';
                   textColor = event.success ? 'text-[#34d399]' : 'text-error';
                } else if (event.type === 'optimization') {
                   dotColor = 'bg-secondary';
                   textColor = 'text-secondary';
                   iconGlow = 'shadow-[0_0_10px_rgba(208,188,255,0.5)] bg-secondary-container';
                } else if (event.type === 'premium') {
                   dotColor = 'bg-[#ffc107]';
                   textColor = 'text-[#ffc107]';
                }

                return (
                  <div key={idx} className="relative">
                    <div className={`absolute -left-[31px] top-1 w-4 h-4 rounded-full border-2 border-background flex items-center justify-center ${iconGlow ? iconGlow : 'bg-surface-container-highest'}`}>
                      <div className={`w-1.5 h-1.5 rounded-full ${dotColor}`}></div>
                    </div>
                    <p className={`font-data-display text-data-display text-[12px] mb-1 ${textColor}`}>[{event.time}]</p>
                    <p className="font-body-sm text-body-sm text-on-surface" dangerouslySetInnerHTML={{ __html: event.description }}></p>
                  </div>
                );
              })}
              
              {(!result.events || result.events.length === 0) && (
                <div className="text-on-surface-variant italic pt-4">No events logged.</div>
              )}

            </div>
          </div>
        </section>
      </main>
      
      <style dangerouslySetInnerHTML={{__html: `
        .custom-scrollbar::-webkit-scrollbar {
          width: 6px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: rgba(255, 255, 255, 0.02);
          border-radius: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(255, 255, 255, 0.1);
          border-radius: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(255, 255, 255, 0.2);
        }
      `}} />
    </div>
  );
};