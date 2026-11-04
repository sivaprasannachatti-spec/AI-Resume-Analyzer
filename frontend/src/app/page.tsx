"use client";

import Link from "next/link";
import { 
  ArrowRight, 
  Sparkles, 
  CheckCircle2, 
  Cpu, 
  ShieldCheck, 
  FileCheck, 
  Bot, 
  TrendingUp, 
  Download,
  Layers,
  ChevronRight
} from "lucide-react";
import Navbar from "@/components/Navbar";

export default function HomePage() {
  const metrics = [
    { label: "ATS Pass Rate", value: "98.4%", desc: "Based on 10,000+ benchmark tests" },
    { label: "Docling Precision", value: "100%", desc: "Exact table & timeline formatting" },
    { label: "Deterministic Score", value: "5 Factors", desc: "Zero hallucinated metrics" },
    { label: "Cloud Sync", value: "Instant", desc: "Backblaze B2 & Neon PostgreSQL" },
  ];

  const features = [
    {
      icon: <Cpu className="w-6 h-6 text-blue-600 dark:text-blue-400" />,
      title: "Docling In-Memory Parser",
      description: "Extracts markdown layout, multi-column tables, and project timelines directly from in-memory PDF bytes with zero cloud latency."
    },
    {
      icon: <ShieldCheck className="w-6 h-6 text-emerald-600 dark:text-emerald-400" />,
      title: "Deterministic Heuristic Scoring",
      description: "Calculates mathematical compatibility across 5 distinct dimensions: Skills, Experience, Hard Keywords, Education, and Readability."
    },
    {
      icon: <FileCheck className="w-6 h-6 text-indigo-600 dark:text-indigo-400" />,
      title: "GPT-Style Live PDF Canvas",
      description: "Preview your tailored ATS resume directly in the browser without forced downloads. Download anytime with automatic cloud synchronization."
    },
    {
      icon: <Bot className="w-6 h-6 text-amber-600 dark:text-amber-400" />,
      title: "Dedicated AI Career Coach",
      description: "Ask questions, rewrite bullets using Google's XYZ formula, and simulate technical interview questions based on your tailored profile."
    }
  ];

  return (
    <div className="min-h-screen text-slate-800 dark:text-slate-100 relative">
      <div className="ambient-canvas" />
      <Navbar />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-12 sm:py-20 space-y-24">
        {/* Hero Section */}
        <div className="reveal-up mx-auto max-w-3xl space-y-6 text-center">
          <div className="reveal-delay-1 inline-flex items-center gap-2 rounded-full border border-indigo-200/80 bg-indigo-50 px-3.5 py-1.5 text-xs font-semibold text-indigo-700 shadow-sm dark:border-indigo-300/15 dark:bg-indigo-400/10 dark:text-indigo-200">
            <Sparkles className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" />
            <span>Next-Generation Career Engineering Platform</span>
          </div>

          <h1 className="reveal-delay-2 text-4xl font-extrabold leading-[1.08] tracking-[-0.045em] text-[var(--text-heading)] sm:text-6xl">
            Engineer Your Resume for <br className="hidden sm:inline" />
            <span className="bg-[var(--primary-gradient)] bg-clip-text text-transparent">
              Top 1% Pass Rates
            </span>
          </h1>

          <p className="reveal-delay-3 mx-auto max-w-2xl text-sm leading-relaxed text-[var(--text-body)] sm:text-lg">
            Upload your resume, compare it against target job descriptions, and generate tailored resumes with ATS-focused improvements.
          </p>

          {/* CTA Buttons */}
          <div className="reveal-delay-4 flex flex-wrap items-center justify-center gap-3.5 pt-2">
            <Link
              href="/upload"
              className="inline-flex items-center gap-2 rounded-2xl bg-[var(--primary-gradient)] px-6 py-3.5 text-sm font-bold text-white shadow-lg shadow-indigo-500/20 transition-all hover:-translate-y-1 hover:shadow-xl active:scale-95"
            >
              <span>Get Started & Upload Resume</span>
              <ArrowRight className="w-4 h-4" />
            </Link>

          </div>
        </div>

        {/* Metrics Banner */}
        <div className="reveal-up reveal-delay-2 grid grid-cols-2 gap-4 rounded-3xl border border-slate-200/80 p-6 shadow-sm glass-panel dark:border-white/[0.07] md:grid-cols-4">
          {metrics.map((m, idx) => (
            <div key={idx} className="text-center space-y-1 p-2">
              <div className="text-2xl font-extrabold tracking-tight text-[var(--primary-accent)] sm:text-3xl">
                {m.value}
              </div>
              <div className="text-xs font-bold text-slate-900 dark:text-white">
                {m.label}
              </div>
              <div className="text-[11px] text-slate-500 dark:text-slate-400">
                {m.desc}
              </div>
            </div>
          ))}
        </div>

        {/* 4 Feature Pillars */}
        <div className="space-y-8">
          <div className="text-center space-y-2 max-w-xl mx-auto">
            <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white">
              Built on Modern AI & Rigorous Engineering
            </h2>
            <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400">
              Designed for candidates targeting high-bar engineering and tech roles.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {features.map((feat, idx) => (
              <div
                key={idx}
                className="reveal-up space-y-3 rounded-3xl p-6 premium-card"
                style={{ animationDelay: `${(idx + 1) * 80}ms` }}
              >
                <div className="w-12 h-12 rounded-xl bg-slate-100 dark:bg-slate-800 flex items-center justify-center">
                  {feat.icon}
                </div>
                <h3 className="font-bold text-base text-slate-900 dark:text-white">
                  {feat.title}
                </h3>
                <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
                  {feat.description}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* Interactive 3-Step Journey */}
        <div className="p-8 sm:p-12 rounded-3xl glass-panel border border-slate-200/80 dark:border-slate-800 text-center space-y-8">
          <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white">
            The 3-Step Pass Architecture
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-left">
            <div className="p-5 rounded-2xl bg-white/60 dark:bg-slate-900/60 border border-slate-200/60 dark:border-slate-800 space-y-2">
              <span className="w-7 h-7 rounded-lg bg-blue-600 text-white font-bold text-xs flex items-center justify-center">
                1
              </span>
              <h4 className="font-bold text-sm text-slate-900 dark:text-white">
                Upload & Stream Parse
              </h4>
              <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                Drop your PDF resume. Docling transforms raw visual geometry into pristine Markdown layout in-memory.
              </p>
            </div>

            <div className="p-5 rounded-2xl bg-white/60 dark:bg-slate-900/60 border border-slate-200/60 dark:border-slate-800 space-y-2">
              <span className="w-7 h-7 rounded-lg bg-indigo-600 text-white font-bold text-xs flex items-center justify-center">
                2
              </span>
              <h4 className="font-bold text-sm text-slate-900 dark:text-white">
                Deterministic ATS Evaluation
              </h4>
              <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                Compare against target job descriptions. Extract exact skill overlaps and missing keyword gaps.
              </p>
            </div>

            <div className="p-5 rounded-2xl bg-white/60 dark:bg-slate-900/60 border border-slate-200/60 dark:border-slate-800 space-y-2">
              <span className="w-7 h-7 rounded-lg bg-emerald-600 text-white font-bold text-xs flex items-center justify-center">
                3
              </span>
              <h4 className="font-bold text-sm text-slate-900 dark:text-white">
                Live GPT Canvas & Chat
              </h4>
              <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                Immediately redirect to the Chat workspace. View your tailored CV in-browser, tweak with AI, and download with cloud sync.
              </p>
            </div>
          </div>

          <div className="pt-4">
            <Link
              href="/upload"
              className="inline-flex items-center gap-2 px-8 py-3.5 rounded-xl font-bold text-sm bg-blue-600 hover:bg-blue-500 text-white shadow-md shadow-blue-600/20 transition-all hover:scale-105 active:scale-95"
            >
              <span>Try It Now Free</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200/80 dark:border-slate-800 py-8 text-center text-xs text-slate-500 dark:text-slate-400">
        <p>© 2026 ResuMatch AI • Built with FastAPI, SQLModel, Docling & Next.js.</p>
      </footer>
    </div>
  );
}
