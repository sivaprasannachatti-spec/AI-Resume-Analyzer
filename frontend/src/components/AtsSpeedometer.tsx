"use client";

import { useMemo } from "react";

interface AtsSpeedometerProps {
  score: number; // 0 to 100
  size?: number;
  label?: string;
}

export default function AtsSpeedometer({
  score,
  size = 200,
  label = "ATS Score",
}: AtsSpeedometerProps) {
  const clampedScore = Math.max(0, Math.min(100, Math.round(score)));

  // Angle ranges from -90 deg (score = 0) to +90 deg (score = 100)
  const needleRotation = -90 + (clampedScore / 100) * 180;

  const { tier, label: statusLabel, colorClass, badgeClass, trackGradient } = useMemo(() => {
    if (clampedScore >= 85) {
      return {
        tier: "Interview Ready",
        label: "Excellent ATS Match",
        colorClass: "text-emerald-600 dark:text-emerald-400",
        badgeClass: "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800",
        trackGradient: "from-emerald-500 to-teal-400"
      };
    }
    if (clampedScore >= 70) {
      return {
        tier: "Competitive",
        label: "Good ATS Match",
        colorClass: "text-blue-600 dark:text-blue-400",
        badgeClass: "bg-blue-50 text-blue-700 dark:bg-blue-950/60 dark:text-blue-300 border-blue-200 dark:border-blue-800",
        trackGradient: "from-blue-500 to-indigo-400"
      };
    }
    if (clampedScore >= 50) {
      return {
        tier: "Moderate",
        label: "Average Alignment",
        colorClass: "text-amber-600 dark:text-amber-400",
        badgeClass: "bg-amber-50 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300 border-amber-200 dark:border-amber-800",
        trackGradient: "from-amber-500 to-orange-400"
      };
    }
    return {
      tier: "Low Fit",
      label: "Needs Optimization",
      colorClass: "text-rose-600 dark:text-rose-400",
      badgeClass: "bg-rose-50 text-rose-700 dark:bg-rose-950/60 dark:text-rose-300 border-rose-200 dark:border-rose-800",
      trackGradient: "from-rose-500 to-rose-600"
    };
  }, [clampedScore]);

  // Radius = 70, Center = (100, 95)
  // Arc path: starts at (30, 95) -> curves up to (100, 25) -> curves down to (170, 95)
  const arcPath = "M 30 95 A 70 70 0 0 1 170 95";

  return (
    <div className="flex flex-col items-center select-none">
      {/* SVG Speedometer Gauge */}
      <div className="relative flex justify-center" style={{ width: size, height: size * 0.52 }}>
        <svg
          viewBox="0 0 200 108"
          className="w-full h-full overflow-visible"
        >
          <defs>
            {/* Speedometer multi-color gradient arc */}
            <linearGradient id="speedometerGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#ef4444" />
              <stop offset="35%" stopColor="#f59e0b" />
              <stop offset="70%" stopColor="#3b82f6" />
              <stop offset="100%" stopColor="#10b981" />
            </linearGradient>

            {/* Needle drop shadow */}
            <filter id="needleShadow" x="-20%" y="-20%" width="140%" height="140%">
              <feDropShadow dx="0" dy="2" stdDeviation="2" floodOpacity="0.25" />
            </filter>
          </defs>

          {/* Background Track (Muted Grey) */}
          <path
            d={arcPath}
            fill="none"
            stroke="currentColor"
            strokeWidth="14"
            strokeLinecap="round"
            className="text-slate-200 dark:text-slate-800"
          />

          {/* Color Gradient Track */}
          <path
            d={arcPath}
            fill="none"
            stroke="url(#speedometerGradient)"
            strokeWidth="12"
            strokeLinecap="round"
            strokeDasharray="220"
            strokeDashoffset="0"
            opacity="0.85"
          />

          {/* Tick Marks */}
          {/* 0% Tick */}
          <text x="20" y="106" fontSize="9" fontWeight="700" textAnchor="middle" className="fill-slate-400">
            0%
          </text>
          {/* 50% Tick */}
          <text x="100" y="16" fontSize="9" fontWeight="700" textAnchor="middle" className="fill-slate-400">
            50%
          </text>
          {/* 100% Tick */}
          <text x="180" y="106" fontSize="9" fontWeight="700" textAnchor="middle" className="fill-slate-400">
            100%
          </text>

          {/* Speedometer Needle */}
          <g
            transform={`rotate(${needleRotation}, 100, 95)`}
            className="transition-transform duration-700 ease-out"
            filter="url(#needleShadow)"
          >
            {/* Needle Pointer */}
            <polygon
              points="97.5,95 102.5,95 100.8,32 99.2,32"
              className="fill-slate-800 dark:fill-white"
            />
            {/* Center Pivot Hub */}
            <circle cx="100" cy="95" r="7" className="fill-slate-900 dark:fill-slate-100" />
            <circle cx="100" cy="95" r="3.5" className="fill-blue-600" />
          </g>
        </svg>
      </div>

      {/* Digital Score & Status with dedicated spacing to prevent overlap */}
      <div className="mt-4 flex flex-col items-center text-center space-y-1">
        <div className={`text-3xl font-extrabold tracking-tight ${colorClass}`}>
          {clampedScore}%
        </div>
        <div className="text-[11px] font-bold uppercase tracking-widest text-slate-400 dark:text-slate-500">
          {label}
        </div>
        <div className="pt-1.5">
          <span className={`inline-block px-3 py-0.5 rounded-full text-xs font-bold border ${badgeClass}`}>
            {statusLabel}
          </span>
        </div>
      </div>
    </div>
  );
}
