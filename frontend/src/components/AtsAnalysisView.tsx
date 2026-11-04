"use client";

import { AtsAnalysisResult } from "@/types/resume";
import ScoreGauge from "./ScoreGauge";
import { Check, Plus, Lightbulb, Target, Shield, Layers, Calendar, Briefcase, Sparkles, ArrowRight } from "lucide-react";

interface AtsAnalysisViewProps {
  analysis: AtsAnalysisResult;
  onTailorClick?: () => void;
  isTailoring?: boolean;
}

export default function AtsAnalysisView({ analysis, onTailorClick, isTailoring }: AtsAnalysisViewProps) {
  const subScoreMeta = [
    {
      key: "keyword_match",
      title: "Keyword Density",
      weight: "40%",
      score: analysis.sub_scores.keyword_match ?? 0,
      icon: Target,
      tag: "Keywords"
    },
    {
      key: "skills_coverage",
      title: "Required Skills",
      weight: "20%",
      score: analysis.sub_scores.skills_coverage ?? 0,
      icon: Shield,
      tag: "Technical Stack"
    },
    {
      key: "title_match",
      title: "Title & Headline",
      weight: "15%",
      score: analysis.sub_scores.title_match ?? 0,
      icon: Briefcase,
      tag: "Role Alignment"
    },
    {
      key: "section_completeness",
      title: "Section Quality",
      weight: "15%",
      score: analysis.sub_scores.section_completeness ?? 0,
      icon: Layers,
      tag: "Architecture"
    },
    {
      key: "date_consistency",
      title: "Date Formatting",
      weight: "10%",
      score: analysis.sub_scores.date_consistency ?? 100,
      icon: Calendar,
      tag: "ATS Parsing"
    },
  ];

  return (
    <div className="space-y-6">
      {/* Top Banner: Score Gauge & Executive Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1">
          <ScoreGauge score={analysis.overall_score} label="Overall Match Score" />
        </div>

        <div className="lg:col-span-2 p-7 rounded-2xl premium-card flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-xl font-bold text-slate-900 dark:text-white">
                Deterministic ATS Evaluation
              </h3>
              <span className="text-[11px] px-2.5 py-1 rounded-full font-semibold bg-blue-50 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 border border-blue-200/80 dark:border-blue-800/60">
                5-Factor Heuristic Engine
              </span>
            </div>
            <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed mb-4">
              Scored deterministically using real applicant tracking system criteria. The engine cross-references required skills, role title hierarchy, technical keywords, and layout formatting without stochastic LLM scoring.
            </p>
          </div>

          {onTailorClick && (
            <div className="pt-4 border-t border-slate-200/70 dark:border-slate-800 flex flex-wrap items-center justify-between gap-3">
              <span className="text-xs text-slate-500 dark:text-slate-400 font-medium">
                Want to automatically bridge missing skills and elevate bullet verbs?
              </span>
              <button
                onClick={onTailorClick}
                disabled={isTailoring}
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white shadow-md shadow-blue-600/20 transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50"
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>{isTailoring ? "Tailoring with AI..." : "Tailor Resume for this Job"}</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          )}
        </div>
      </div>

      {/* 5 Sub-Score Metrics Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3.5">
        {subScoreMeta.map((item) => {
          const Icon = item.icon;
          const scoreVal = Math.round(item.score);
          return (
            <div
              key={item.key}
              className="p-4 rounded-xl premium-card flex flex-col justify-between space-y-3"
            >
              <div className="flex items-center justify-between">
                <Icon className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                <span className="text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase">
                  {item.weight}
                </span>
              </div>
              <div>
                <span className="text-2xl font-black text-slate-900 dark:text-white">
                  {scoreVal}%
                </span>
                <p className="text-xs font-semibold text-slate-700 dark:text-slate-300 mt-0.5">
                  {item.title}
                </p>
              </div>
              <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-1.5 overflow-hidden">
                <div
                  className="bg-blue-600 dark:bg-blue-500 h-1.5 rounded-full transition-all duration-700"
                  style={{ width: `${scoreVal}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>

      {/* Matched vs Missing Skills Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Matched Skills */}
        <div className="p-6 rounded-2xl premium-card">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <span className="w-6 h-6 rounded-lg bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-400 flex items-center justify-center font-bold text-xs">
                ✓
              </span>
              <h4 className="font-bold text-slate-900 dark:text-white text-sm">
                Matched Target Skills ({analysis.key_skills.length})
              </h4>
            </div>
            <span className="text-xs text-slate-400 font-medium">Found in Resume</span>
          </div>
          {analysis.key_skills.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {analysis.key_skills.map((skill, i) => (
                <span
                  key={i}
                  className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-medium bg-emerald-50 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-300 border border-emerald-200/80 dark:border-emerald-800/60"
                >
                  <Check className="w-3 h-3 text-emerald-600" />
                  {skill}
                </span>
              ))}
            </div>
          ) : (
            <p className="text-xs text-slate-500 italic">No direct skill matches detected.</p>
          )}
        </div>

        {/* Missing Skills */}
        <div className="p-6 rounded-2xl premium-card">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <span className="w-6 h-6 rounded-lg bg-rose-50 dark:bg-rose-950/60 text-rose-700 dark:text-rose-400 flex items-center justify-center font-bold text-xs">
                +
              </span>
              <h4 className="font-bold text-slate-900 dark:text-white text-sm">
                Missing Target Skills ({analysis.missing_skills.length})
              </h4>
            </div>
            <span className="text-xs text-slate-400 font-medium">In Job Description</span>
          </div>
          {analysis.missing_skills.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {analysis.missing_skills.map((skill, i) => (
                <span
                  key={i}
                  className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-medium bg-rose-50 dark:bg-rose-950/50 text-rose-700 dark:text-rose-300 border border-rose-200/80 dark:border-rose-800/60"
                >
                  <Plus className="w-3 h-3 text-rose-600" />
                  {skill}
                </span>
              ))}
            </div>
          ) : (
            <p className="text-xs text-emerald-600 dark:text-emerald-400 font-medium">
              Exceptional! All target skills matched.
            </p>
          )}
        </div>
      </div>

      {/* Strategic Improvement Tips */}
      <div className="p-6 rounded-2xl premium-card">
        <div className="flex items-center gap-2 mb-4">
          <Lightbulb className="w-5 h-5 text-amber-600 dark:text-amber-400" />
          <h4 className="font-bold text-slate-900 dark:text-white text-sm">
            Actionable Optimization Recommendations
          </h4>
        </div>
        <div className="space-y-3">
          {analysis.recommendations.map((rec, i) => (
            <div
              key={i}
              className="p-4 rounded-xl bg-slate-50/70 dark:bg-slate-900/60 border border-slate-200/60 dark:border-slate-800 flex items-start gap-3.5"
            >
              <span className="w-5 h-5 rounded-full bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 text-xs font-bold flex items-center justify-center shrink-0 mt-0.5">
                {i + 1}
              </span>
              <p className="text-xs sm:text-sm text-slate-700 dark:text-slate-300 leading-relaxed">
                {rec}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
