"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  CheckCircle2,
  FileCheck2,
  Loader2,
  Sparkles,
  WandSparkles,
} from "lucide-react";
import Navbar from "@/components/Navbar";
import ResumeViewer from "@/components/ResumeViewer";
import AtsSpeedometer from "@/components/AtsSpeedometer";
import { apiFetch } from "@/lib/api";
import { AtsScorePair, ResumeSchema } from "@/types/resume";
import { TemplateSettings } from "@/components/resume/template-settings";

interface TailoringPreview {
  resume_id: string;
  tailored_resume_id: string;
  tailored_resume_payload: ResumeSchema;
  original_resume_payload?: ResumeSchema;
  raw_jd: string;
  ats_scores: AtsScorePair;
  refinement?: {
    final_match_percentage?: number;
    ai_phrases_removed?: string[];
    invented_skills?: string[];
  };
  diff_result?: {
    applied_changes?: unknown[];
    rejected_changes?: unknown[];
  };
  writing_checks?: string[];
  template?: string;
  templateSettings?: TemplateSettings;
}

function ChangeList({
  title,
  items,
  tone,
}: {
  title: string;
  items: unknown[];
  tone: "positive" | "negative";
}) {
  return (
    <div>
      <h3 className={`mb-2 text-xs font-bold uppercase tracking-[0.14em] ${tone === "positive" ? "text-emerald-600" : "text-rose-600"}`}>
        {title} ({items.length})
      </h3>
      {items.length ? (
        <ul className="space-y-2">
          {items.map((item, index) => {
            const change = item as { path?: string; action?: string; value?: unknown; reason?: string };
            return (
              <li key={`${change.path || "change"}-${index}`} className="rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-elevated)] p-3 text-xs text-[var(--text-body)]">
                <p className="font-semibold">{change.path || change.action || "Resume change"}</p>
                {change.reason && <p className="mt-1 text-[var(--text-muted)]">{change.reason}</p>}
                {change.value !== undefined && <p className="mt-1 break-words text-[var(--text-muted)]">{String(change.value)}</p>}
              </li>
            );
          })}
        </ul>
      ) : (
        <p className="text-xs text-[var(--text-muted)]">No changes in this category.</p>
      )}
    </div>
  );
}

export default function TailoredResumePage() {
  const router = useRouter();
  const [preview, setPreview] = useState<TailoringPreview | null>(null);
  const [isApplying, setIsApplying] = useState(false);
  const [applied, setApplied] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    try {
      const stored = sessionStorage.getItem("resumatch_tailoring_preview");
      if (stored) {
        setPreview(JSON.parse(stored) as TailoringPreview);
      } else {
        router.replace("/upload");
      }
    } catch (reason) {
      console.error("Unable to load tailoring preview", reason);
      setError("This preview is no longer available. Please upload your resume again.");
    }
  }, [router]);

  const handleApply = async () => {
    if (!preview || isApplying) return;
    setIsApplying(true);
    setError(null);
    try {
      const result = await apiFetch("/api/cv/tailored-resume/confirm", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          resume_id: preview.resume_id,
          tailored_resume_payload: preview.tailored_resume_payload,
          raw_jd: preview.raw_jd,
          template_settings: preview.templateSettings,
        }),
      });
      setPreview((current) => {
        if (!current) return current;
        const next = { ...current, ats_scores: result.ats_scores ?? current.ats_scores };
        sessionStorage.setItem("resumatch_tailoring_preview", JSON.stringify(next));
        return next;
      });
      setApplied(true);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to apply this resume.");
    } finally {
      setIsApplying(false);
    }
  };

  const handleTemplateSettingsChange = async (settings: TemplateSettings) => {
    setPreview((current) => {
      if (!current) return current;
      const next = { ...current, template: settings.template, templateSettings: settings };
      sessionStorage.setItem("resumatch_tailoring_preview", JSON.stringify(next));
      return next;
    });
    if (applied && preview) {
      try {
        const result = await apiFetch("/api/cv/tailored-resume", {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            resume_id: preview.resume_id,
            tailored_resume_payload: preview.tailored_resume_payload,
            raw_jd: preview.raw_jd,
            template_settings: settings,
          }),
        });
        if (result.ats_scores) {
          setPreview((current) => {
            if (!current) return current;
            const next = { ...current, ats_scores: result.ats_scores };
            sessionStorage.setItem("resumatch_tailoring_preview", JSON.stringify(next));
            return next;
          });
        }
      } catch (reason) {
        setError(reason instanceof Error ? reason.message : "Unable to save formatting settings.");
      }
    }
  };

  if (!preview) {
    return (
      <div className="min-h-screen">
        <div className="ambient-canvas" />
        <Navbar />
        <main className="mx-auto flex max-w-xl flex-col items-center px-6 py-24 text-center">
          {error ? (
            <p className="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700 dark:border-rose-400/20 dark:bg-rose-400/10 dark:text-rose-200">
              {error}
            </p>
          ) : (
            <Loader2 className="h-8 w-8 animate-spin text-[var(--primary-accent)]" />
          )}
        </main>
      </div>
    );
  }

  const originalScore = preview.ats_scores?.original?.overall_score ?? 0;
  const tailoredScore = preview.ats_scores?.tailored?.overall_score ?? 0;
  const appliedChanges = preview.diff_result?.applied_changes?.length ?? 0;
  const rejectedChanges = preview.diff_result?.rejected_changes?.length ?? 0;
  const templateSettings = preview.templateSettings;
  const appliedChangeItems = preview.diff_result?.applied_changes ?? [];
  const rejectedChangeItems = preview.diff_result?.rejected_changes ?? [];

  return (
    <div className="min-h-screen">
      <div className="ambient-canvas" />
      <Navbar />
      <main className="mx-auto max-w-7xl space-y-8 px-4 py-8 sm:px-6 sm:py-12">
        <div className="flex flex-wrap items-start justify-between gap-5 print:hidden">
          <div className="space-y-3">
            <button
              type="button"
              onClick={() => router.push("/upload")}
              className="inline-flex items-center gap-2 text-xs font-bold text-[var(--text-muted)] transition hover:text-[var(--primary-accent)]"
            >
              <ArrowLeft className="h-4 w-4" /> Back to resume studio
            </button>
            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-[0.18em] text-[var(--primary-accent)]">
              <WandSparkles className="h-4 w-4" /> Tailoring complete
            </div>
            <h1 className="text-3xl font-extrabold tracking-[-0.04em] text-[var(--text-heading)] sm:text-5xl">
              Your resume, tuned for the role.
            </h1>
            <p className="max-w-2xl text-sm leading-relaxed text-[var(--text-body)] sm:text-base">
              Review the ATS-ready version below. Nothing is saved until you confirm the changes.
            </p>
          </div>
          <div className="flex items-center gap-2 rounded-2xl border border-emerald-200/80 bg-emerald-50/80 px-3 py-2 text-xs font-bold text-emerald-700 dark:border-emerald-300/15 dark:bg-emerald-400/10 dark:text-emerald-200">
            <FileCheck2 className="h-4 w-4" /> Preview mode
          </div>
        </div>

        {error && (
          <div role="alert" className="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700 dark:border-rose-400/20 dark:bg-rose-400/10 dark:text-rose-200">
            {error}
          </div>
        )}

        <section className="grid gap-5 lg:grid-cols-[280px_1fr]">
          <aside className="space-y-4 print:hidden">
            {templateSettings && (
              <div className="space-y-3 rounded-3xl p-4 glass-panel sm:p-5">
                <div>
                  <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[var(--primary-accent)]">Formatting</p>
                  <h2 className="mt-1 text-sm font-bold text-[var(--text-heading)]">Tune the document</h2>
                </div>
                <label className="block text-xs font-semibold text-[var(--text-body)]">
                  Template style
                  <select
                    value={templateSettings.template}
                    onChange={(event) =>
                      void handleTemplateSettingsChange({
                        ...templateSettings,
                        template: event.target.value as typeof templateSettings.template,
                      })
                    }
                    className="mt-1.5 w-full rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-elevated)] px-3 py-2 text-xs text-[var(--text-body)] font-medium"
                  >
                    <option value="swiss-single">Swiss Single (ATS Standard)</option>
                    <option value="swiss-two-column">Swiss Two Column</option>
                    <option value="modern">Modern Single Column</option>
                    <option value="modern-two-column">Modern Two Column</option>
                    <option value="latex">Academic LaTeX Serif</option>
                    <option value="clean">Clean Minimalist</option>
                    <option value="vivid">Vivid Editorial</option>
                    <option value="vivid-single">Vivid Single Column</option>
                    <option value="deedy">Deedy CV Classic</option>
                    <option value="modern-deedy">Modern Deedy</option>
                  </select>
                </label>
                <label className="block text-xs font-semibold text-[var(--text-body)]">
                  Accent color
                  <select
                    value={templateSettings.accentColor}
                    onChange={(event) =>
                      void handleTemplateSettingsChange({ ...templateSettings, accentColor: event.target.value as typeof templateSettings.accentColor })
                    }
                    className="mt-1.5 w-full rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-elevated)] px-3 py-2 text-xs text-[var(--text-body)]"
                  >
                    <option value="blue">Blue</option>
                    <option value="green">Green</option>
                    <option value="orange">Orange</option>
                    <option value="red">Red</option>
                  </select>
                </label>
                <label className="flex items-center justify-between gap-3 text-xs font-semibold text-[var(--text-body)]">
                  Compact mode
                  <input
                    type="checkbox"
                    checked={templateSettings.compactMode}
                    onChange={(event) =>
                      void handleTemplateSettingsChange({ ...templateSettings, compactMode: event.target.checked })
                    }
                    className="h-4 w-4 accent-indigo-600"
                  />
                </label>
                <label className="block text-xs font-semibold text-[var(--text-body)]">
                  Page size
                  <select
                    value={templateSettings.pageSize}
                    onChange={(event) =>
                      void handleTemplateSettingsChange({ ...templateSettings, pageSize: event.target.value as typeof templateSettings.pageSize })
                    }
                    className="mt-1.5 w-full rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-elevated)] px-3 py-2 text-xs text-[var(--text-body)]"
                  >
                    <option value="A4">A4</option>
                    <option value="LETTER">US Letter</option>
                  </select>
                </label>
              </div>
            )}
            <div className="space-y-4 rounded-3xl p-4 glass-panel sm:p-6">
              <div className="flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-[var(--warm-accent)]" />
                <h2 className="text-sm font-bold text-[var(--text-heading)]">ATS score comparison</h2>
              </div>
              <div className="rounded-2xl border border-[var(--border-subtle)] bg-[var(--bg-elevated)] p-3">
                <p className="mb-1 text-center text-xs font-semibold text-[var(--text-muted)]">Uploaded resume</p>
                <AtsSpeedometer score={originalScore} size={210} label="Original ATS Score" />
              </div>
              <div className="rounded-2xl border border-indigo-500/20 bg-[var(--bg-elevated)] p-3">
                <p className="mb-1 text-center text-xs font-semibold text-indigo-600 dark:text-indigo-300">Tailored preview</p>
                <AtsSpeedometer score={tailoredScore} size={210} label="Tailored ATS Score" />
              </div>
              <p className="mt-4 text-center text-xs leading-relaxed text-[var(--text-muted)]">
                Both scores use the same job description. The tailored score updates when you save resume edits.
              </p>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-2xl p-4 glass-panel">
                <p className="text-2xl font-extrabold text-[var(--text-heading)]">{appliedChanges}</p>
                <p className="mt-1 text-[11px] text-[var(--text-muted)]">Changes applied</p>
              </div>
              <div className="rounded-2xl p-4 glass-panel">
                <p className="text-2xl font-extrabold text-[var(--text-heading)]">{rejectedChanges}</p>
                <p className="mt-1 text-[11px] text-[var(--text-muted)]">Changes rejected</p>
              </div>
            </div>
            <button
              type="button"
              onClick={handleApply}
              disabled={isApplying || applied}
              className="flex w-full items-center justify-center gap-2 rounded-2xl bg-[var(--primary-gradient)] px-4 py-3.5 text-sm font-bold text-white shadow-lg shadow-indigo-500/20 transition hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {applied ? <CheckCircle2 className="h-4 w-4" /> : <CheckCircle2 className="h-4 w-4" />}
              {applied ? "Resume applied" : isApplying ? "Applying..." : "Confirm & apply"}
            </button>
          </aside>

          <div className="min-w-0">
            <section className="mb-5 rounded-3xl p-5 glass-panel print:hidden">
              <div className="mb-4 flex items-center justify-between gap-3">
                <div>
                  <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[var(--primary-accent)]">Content review</p>
                  <h2 className="mt-1 text-lg font-bold text-[var(--text-heading)]">Deterministic changes</h2>
                </div>
                <span className="text-xs font-semibold text-[var(--text-muted)]">Formatted resume preview below</span>
              </div>
              <div className="grid gap-4 md:grid-cols-2">
                <ChangeList title="Applied" items={appliedChangeItems} tone="positive" />
                <ChangeList title="Rejected" items={rejectedChangeItems} tone="negative" />
              </div>
            </section>
            <ResumeViewer
              resumeId={preview.resume_id}
              tailoredResumePayload={preview.tailored_resume_payload}
              rawJobDescription={preview.raw_jd}
              templateId={preview.template}
              templateSettings={preview.templateSettings}
              onSettingsChange={handleTemplateSettingsChange}
              onUpdateSuccess={(payload, atsScores) => {
                setPreview((current) => {
                  if (!current) return current;
                  const next = {
                    ...current,
                    tailored_resume_payload: payload,
                    ats_scores: atsScores ?? current.ats_scores,
                  };
                  sessionStorage.setItem("resumatch_tailoring_preview", JSON.stringify(next));
                  return next;
                });
              }}
            />
          </div>
        </section>
      </main>
    </div>
  );
}
