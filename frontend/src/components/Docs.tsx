import React, { useState } from 'react';
import { Link } from 'react-router-dom';

export const Docs: React.FC = () => {
  const [activeTab, setActiveTab] = useState('quickstart');

  return (
    <div className="bg-level-0 text-on-surface font-body-md min-h-screen overflow-x-hidden selection:bg-primary-container selection:text-black">
      {/* TopNavBar */}
      <nav className="bg-background/80 backdrop-blur-xl fixed top-0 w-full z-50 border-b border-secondary-container flex justify-between items-center px-margin-page h-16 flat with-tonal-layering">
        <div className="flex items-center gap-4">
          <Link to="/" className="font-headline-md text-headline-md font-bold text-primary">VRP Engine Docs</Link>
        </div>
        <div className="hidden md:flex gap-6">
          <a className="text-xl font-semibold text-primary border-b-2 border-primary pb-1 scale-95 duration-100" href="#">API Reference</a>
        </div>
      </nav>

      {/* SideNavBar */}
      <aside className="bg-surface-container-low fixed left-0 top-16 h-[calc(100vh-64px)] w-64 border-r border-secondary-container flat flex flex-col py-unit gap-y-1 z-40 hidden md:flex">
        <nav className="flex-1 flex flex-col gap-1 px-2 mt-4">
          {[
            { id: 'quickstart', icon: 'rocket_launch', label: 'Quick Start' },
            { id: 'optmodels', icon: 'schema', label: 'Optimization Models' },
            { id: 'hyper', icon: 'tune', label: 'Hyperparameters' },
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-3 px-3 py-3 rounded-lg transition-all duration-200 ease-in-out text-lg font-medium ${
                activeTab === tab.id
                  ? 'bg-secondary-container/30 text-primary border-r-2 border-primary'
                  : 'text-on-surface-variant hover:bg-surface-container-highest hover:text-on-surface'
              }`}
            >
              <span className="material-symbols-outlined text-[24px]">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </nav>
      </aside>

      {/* Main Content Area */}
      <main className="md:ml-64 pt-16 min-h-screen flex flex-col">
        <div className="flex-1 p-margin-page max-w-5xl mx-auto w-full mt-8">
          {activeTab === 'quickstart' && (
            <div className="space-y-stack-lg active animate-[fadeIn_0.3s_ease-out]">
              <header>
                <h1 className="text-3xl font-bold text-on-surface mb-4">Getting Started (Data Source)</h1>
                <p className="text-xl text-on-surface-variant max-w-3xl leading-relaxed">Welcome to the Fleet Optimization VRP Engine. This tool uses advanced algorithms to solve complex Vehicle Routing Problems (VRP).</p>
              </header>
              <div className="glass-panel p-gutter rounded-lg border-l-4 border-l-primary-container hud-glow flex gap-4 items-start mt-8">
                <span className="material-symbols-outlined text-primary-container text-3xl mt-1">lightbulb</span>
                <div>
                  <h3 className="text-xl font-bold text-primary-container mb-2">QUICK START TIP</h3>
                  <p className="text-xl text-on-surface leading-relaxed">For the fastest testing of the website, we highly recommend using the Master Database (default Database CSV). Just click 'Run Demo Simulation' to instantly see the engine in action without needing to configure your own data!</p>
                </div>
              </div>
              
              <div className="mt-12 bg-level-1 p-6 rounded-xl border border-secondary-container shadow-lg">
                <h3 className="text-xl font-bold text-on-surface mb-6">How to configure the demo:</h3>
                <img src="/photo_2026-07-05_21-01-51.jpg" alt="Quick Start Guide Options" className="w-full max-w-4xl rounded-lg shadow-xl border border-[#003566] mb-6" />
                <p className="text-xl text-on-surface-variant font-medium border-l-4 border-secondary pl-4 py-3 bg-level-2 rounded-r-lg leading-relaxed">
                  ☝️ Please check the options as marked in the image above and click on <strong>'Run Demo Simulation'</strong> to start the engine.
                </p>
              </div>
            </div>
          )}

          {activeTab === 'optmodels' && (
            <div className="space-y-stack-lg active animate-[fadeIn_0.3s_ease-out]">
              <header>
                <h1 className="text-3xl font-bold text-on-surface mb-4">Algorithm Strategies</h1>
                <p className="text-xl text-on-surface-variant max-w-3xl leading-relaxed">Select the computational approach that best fits your operational constraints and timeline.</p>
              </header>
              <div className="grid grid-cols-1 gap-gutter mt-8">
                <div className="glass-panel p-8 rounded-xl relative overflow-hidden group">
                  <div className="absolute top-0 right-0 w-32 h-32 bg-primary-container/5 rounded-bl-full pointer-events-none group-hover:bg-primary-container/10 transition-colors"></div>
                  <div className="flex items-center gap-3 mb-4">
                    <span className="material-symbols-outlined text-primary-container text-3xl">compare_arrows</span>
                    <h3 className="text-3xl font-bold text-primary">ALNS + OR-Tools (Comparison)</h3>
                  </div>
                  <p className="text-xl text-on-surface-variant leading-relaxed">Runs both solvers side-by-side so you can compare their efficiency and cost on the dashboard. Ideal for benchmark testing and validating new hyperparameter configurations.</p>
                  <div className="mt-6 flex gap-3">
                    <span className="text-lg font-mono px-3 py-1.5 bg-surface-container-highest rounded border border-[#003566]">Compute: High</span>
                    <span className="text-lg font-mono px-3 py-1.5 bg-surface-container-highest rounded border border-[#003566]">Accuracy: Maximum</span>
                  </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-gutter">
                  <div className="bg-level-1 p-8 rounded-xl hover:border-[#003566] transition-colors border border-transparent">
                    <div className="flex items-center gap-3 mb-4">
                      <span className="material-symbols-outlined text-secondary text-3xl">memory</span>
                      <h3 className="text-xl font-bold text-on-surface">ALNS Only</h3>
                    </div>
                    <p className="text-xl text-on-surface-variant leading-relaxed">Uses our custom Adaptive Large Neighborhood Search heuristic. Highly flexible and handles complex constraints well.</p>
                  </div>
                  <div className="bg-level-1 p-8 rounded-xl hover:border-[#003566] transition-colors border border-transparent">
                    <div className="flex items-center gap-3 mb-4">
                      <span className="material-symbols-outlined text-secondary text-3xl">route</span>
                      <h3 className="text-xl font-bold text-on-surface">OR-Tools Only</h3>
                    </div>
                    <p className="text-xl text-on-surface-variant leading-relaxed">Uses Google's mathematical routing solver. Exceptionally fast for standard VRP structures without heavy custom constraints.</p>
                  </div>
                </div>
                <div className="bg-level-1 p-8 rounded-xl border border-error/30 bg-error-container/10">
                  <div className="flex items-center gap-3 mb-4">
                    <span className="material-symbols-outlined text-error text-3xl">bolt</span>
                    <h3 className="text-xl font-bold text-error">Greedy Only</h3>
                  </div>
                  <p className="text-xl text-on-surface-variant leading-relaxed">The absolute fastest method to calculate a route, but the least optimized. Great for instant testing! Not recommended for production dispatch.</p>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'hyper' && (
            <div className="space-y-stack-lg active animate-[fadeIn_0.3s_ease-out]">
              <header>
                <h1 className="text-3xl font-bold text-on-surface mb-4">Basic &amp; Advanced Configuration</h1>
                <p className="text-xl text-on-surface-variant max-w-3xl leading-relaxed">Fine-tune the engine's behavior. If you are unsure, leave the advanced settings at their default values—they are already highly optimized!</p>
              </header>
              <section className="space-y-6 mt-8">
                <h2 className="text-3xl font-bold text-primary border-b border-[#003566] pb-3">Basic Configuration</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="bg-level-1 p-6 rounded-lg flex flex-col justify-between">
                    <div>
                      <h4 className="text-xl font-mono font-bold text-on-surface mb-2 flex items-center justify-between">
                        Fleet Size
                        <span className="text-sm text-primary-container bg-primary-container/10 px-2 py-1 rounded">INT</span>
                      </h4>
                      <p className="text-xl text-on-surface-variant mb-6 leading-relaxed">The maximum number of trucks you have available to dispatch.</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <input className="bg-level-0 border border-[#003566] rounded px-4 py-2 text-on-surface text-lg font-mono w-32 focus:outline-none focus:border-primary-container focus:ring-1 focus:ring-primary-container" type="number" defaultValue="25" />
                    </div>
                  </div>
                  <div className="bg-level-1 p-6 rounded-lg flex flex-col justify-between">
                    <div>
                      <h4 className="text-xl font-mono font-bold text-on-surface mb-2 flex items-center justify-between">
                        Vehicle Capacity
                        <span className="text-sm text-primary-container bg-primary-container/10 px-2 py-1 rounded">INT/FLOAT</span>
                      </h4>
                      <p className="text-xl text-on-surface-variant mb-6 leading-relaxed">The maximum number of orders (or weight) a single truck can carry before returning to depot.</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <input className="bg-level-0 border border-[#003566] rounded px-4 py-2 text-on-surface text-lg font-mono w-32 focus:outline-none focus:border-primary-container focus:ring-1 focus:ring-primary-container" type="number" defaultValue="100" />
                    </div>
                  </div>
                </div>
              </section>
              <section className="space-y-6 pt-8">
                <h2 className="text-3xl font-bold text-primary border-b border-[#003566] pb-3 flex items-center gap-3">
                  <span className="material-symbols-outlined text-[28px]">warning</span>
                  Advanced Hyperparameters
                </h2>
                <div className="overflow-x-auto bg-level-1 rounded-xl shadow-lg border border-[#003566]">
                  <table className="w-full text-left border-collapse">
                    <thead>
                      <tr className="border-b-2 border-[#003566] bg-surface-container-lowest">
                        <th className="py-5 px-6 text-xl font-mono font-bold text-on-surface-variant w-1/4">Parameter</th>
                        <th className="py-5 px-6 text-xl font-bold text-on-surface-variant w-1/2">Description</th>
                        <th className="py-5 px-6 text-xl font-mono font-bold text-on-surface-variant text-right">Default Value</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#001D3D]">
                      {[
                        { name: 'Iterations', desc: 'How many times the algorithm will attempt to improve the route. Higher numbers yield better routes but take longer.', def: '10000' },
                        { name: 'Segment Length', desc: "Determines how many iterations it waits before updating its 'memory' of what successful routing strategies work best.", def: '100' },
                        { name: 'Reaction Factor', desc: 'How aggressively the algorithm adapts to new strategies. Higher value = faster learning from recent successes.', def: '0.1' },
                        { name: 'Destroy Bounds', desc: "Min/Max percentage of the route to 'destroy' and rebuild each time to find shortcuts.", def: '10% - 30%' },
                        { name: 'Opt. Interval', desc: 'How often the secondary background layer runs to strictly enforce time windows and constraints.', def: '5s' },
                        { name: 'Costs (Fix/KM)', desc: 'Base cost to dispatch a truck vs per KM cost. Used to decide between fewer long routes or more short ones.', def: '150 / 1.5' },
                      ].map(row => (
                        <tr key={row.name} className="hover:bg-[#001D3D]/50 transition-colors group">
                          <td className="py-6 px-6 text-xl font-mono font-bold text-on-surface group-hover:text-primary transition-colors">{row.name}</td>
                          <td className="py-6 px-6 text-xl text-on-surface-variant leading-relaxed">{row.desc}</td>
                          <td className="py-6 px-6 text-right text-xl font-mono font-bold text-primary-container">{row.def}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};
