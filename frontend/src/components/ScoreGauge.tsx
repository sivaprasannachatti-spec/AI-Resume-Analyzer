"use client";

import { useEffect, useState } from "react";
import { Award } from "lucide-react";

interface ScoreGaugeProps {
  score: number;
  label?: string;
}

export default function ScoreGauge({ score, label = "ATS Match Score" }: ScoreGaugeProps) {
  const [animatedScore, setAnimatedScore] = useState(0);

  useEffect(() => {
    const duration = 1000;
    const steps = 50;
    const increment = score / steps;
    let current = 0;
    const timer = setInterval(() => {
      current += increment;
      if (current >= score) {
        setAnimatedScore(score);
        clearInterval(timer);
      } else {
        setAnimatedScore(Math.round(current));
      }
    }, duration / steps);

    return () => clearInterval(timer);
  }, [score]);

  const radius = 62;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (animatedScore / 100) * circumference;

  // Refined Executive Palette (no harsh neons)
  const getScheme = (val: number) => {
    if (val >= 80) return { stroke: "#059669", text: "text-emerald-700 dark:text-emerald-400", badge: "bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800/60", desc: "Top Tier Candidate" };
    if (val >= 60) return { stroke: "#d97706", text: "text-amber-700 dark:text-amber-400", badge: "bg-amber-50 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300 border-amber-200 dark:border-amber-800/60", desc: "Competitive Match" };
    return { stroke: "#e11d48", text: "text-rose-700 dark:text-rose-400", badge: "bg-rose-50 dark:bg-rose-950/60 text-rose-700 dark:text-rose-300 border-rose-200 dark:border-rose-800/60", desc: "Action Required" };
  };

  const scheme = getScheme(score);

  return (
    <div className="flex flex-col items-center justify-center p-6 rounded-2xl premium-card border border-slate-200/80 dark:border-slate-800">
      <div className="relative w-36 h-36 flex items-center justify-center">
        <svg className="w-full h-full transform -rotate-90" viewBox="0 0 160 160">
          <circle
            cx="80"
            cy="80"
            r={radius}
            strokeWidth="10"
            fill="transparent"
            className="stroke-slate-100 dark:stroke-slate-800/80"
          />
          <circle
            cx="80"
            cy="80"
            r={radius}
            strokeWidth="10"
            stroke={scheme.stroke}
            strokeLinecap="round"
            fill="transparent"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            style={{ transition: "stroke-dashoffset 0.8s ease-out" }}
          />
        </svg>

        <div className="absolute flex flex-col items-center justify-center text-center">
          <span className={`text-3xl font-extrabold tracking-tight ${scheme.text}`}>
            {animatedScore}%
          </span>
          <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400 dark:text-slate-500 mt-0.5">
            Compatibility
          </span>
        </div>
      </div>

      <div className="mt-4 text-center space-y-1">
        <span className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-semibold border ${scheme.badge}`}>
          {scheme.desc}
        </span>
        <div className="flex items-center justify-center gap-1.5 text-xs font-medium text-slate-500 dark:text-slate-400 pt-1">
          <Award className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" />
          <span>{label}</span>
        </div>
      </div>
    </div>
  );
}
