import React, { useState, useEffect } from 'react';
import { uploadSimulationCsv, getMatrixStatus } from '../api/api';
import type { SimulationResult } from '../api/api';

interface LoadingScreenProps {
  statusText: string;
}

export const LoadingScreen: React.FC<LoadingScreenProps> = ({ statusText }) => {
  return (
    <div className="bg-background text-on-surface min-h-screen flex flex-col items-center justify-center overflow-hidden relative w-full h-full">
      {/* Decorative ambient background glow */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-primary/10 via-background to-background pointer-events-none"></div>

      {/* Main Processing Card */}
      <div className="relative z-10 flex flex-col items-center justify-center p-[40px] md:p-[64px] max-w-3xl w-full mx-margin-mobile md:mx-margin-desktop bg-surface-container-low/40 backdrop-blur-2xl rounded-2xl border border-white/5 shadow-2xl">
        
        {/* Pulsing/Spinning Icon Assembly */}
        <div className="relative flex items-center justify-center mb-[48px] w-32 h-32">
          {/* Outer spinning rings */}
          <div className="absolute inset-0 rounded-full border-2 border-primary/20 border-t-primary/80 animate-spin" style={{ animationDuration: '3s' }}></div>
          <div className="absolute inset-4 rounded-full border border-secondary/20 border-b-secondary/60 animate-spin" style={{ animationDuration: '2s', animationDirection: 'reverse' }}></div>
          {/* Core glowing pulse */}
          <div className="absolute inset-8 bg-primary/20 rounded-full animate-pulse blur-xl"></div>
          {/* Primary Icon */}
          <span className="material-symbols-outlined text-[64px] text-primary relative z-10" style={{ fontVariationSettings: "'FILL' 1" }}>
            hub
          </span>
        </div>

        {/* Main Text */}
        <h1 className="font-headline-lg-mobile text-headline-lg-mobile md:font-headline-lg md:text-headline-lg text-on-surface mb-[32px] text-center tracking-tight">
          Analyzing network topology...
        </h1>

        {/* Terminal/Progression Subtext */}
        <div className="w-full bg-surface-container-highest/50 rounded-lg p-[24px] border border-white/5 font-data-display text-data-display flex flex-col gap-[12px] overflow-hidden">
          {/* Completed Step 1 */}
          <div className="flex items-center gap-[16px] text-on-surface-variant opacity-60">
            <span className="material-symbols-outlined text-[20px]">check_circle</span>
            <span className="truncate">&gt; Geocoding addresses...</span>
            <span className="ml-auto text-primary opacity-50">[100%]</span>
          </div>

          {/* Completed Step 2 */}
          <div className="flex items-center gap-[16px] text-on-surface-variant opacity-60">
            <span className="material-symbols-outlined text-[20px]">check_circle</span>
            <span className="truncate">&gt; Computing distance matrix...</span>
            <span className="ml-auto text-primary opacity-50">[100%]</span>
          </div>

          {/* Active Step */}
          <div className="flex items-center gap-[16px] text-primary animate-pulse">
            <span className="material-symbols-outlined text-[20px] animate-spin">sync</span>
            <span className="truncate">&gt; {statusText || 'Executing ALNS Heuristics...'}</span>
            <span className="ml-auto">_</span>
          </div>
        </div>
      </div>
    </div>
  );
};