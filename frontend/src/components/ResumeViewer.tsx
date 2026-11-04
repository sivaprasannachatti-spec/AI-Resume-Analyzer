"use client";

import { useState } from "react";
import { CheckCircle2, Download, FileCode2, Sparkles } from "lucide-react";
import ResumeComponent from "@/components/resume/resume-component";
import {
  DEFAULT_TEMPLATE_SETTINGS,
  DEFAULT_TEMPLATE_ID,
  isResumeTemplateId,
  ResumeTemplateId,
} from "@/components/resume/template-settings";
import { TemplateSettings } from "@/components/resume/template-settings";
import { generateLatexResume } from "@/components/resume/latex-resume";
import { getApiBase } from "@/lib/api";
import { AtsScorePair, ResumeSchema } from "@/types/resume";

interface ResumeViewerProps {
  resumeId: string;
  tailoredResumePayload: ResumeSchema;
  rawJobDescription: string;
  templateId?: string;
  templateSettings?: TemplateSettings;
  onSettingsChange?: (settings: TemplateSettings) => void;
  onUpdateSuccess: (newPayload: ResumeSchema, atsScores?: AtsScorePair) => void;
}

export default function ResumeViewer({
  resumeId,
  tailoredResumePayload,
  rawJobDescription,
  templateId,
  templateSettings,
  onSettingsChange,
  onUpdateSuccess,
}: ResumeViewerProps) {
  const [isUpdating, setIsUpdating] = useState(false);
  const [updateQuery, setUpdateQuery] = useState("");
  const [showUpdateModal, setShowUpdateModal] = useState(false);
  const [downloadSuccess, setDownloadSuccess] = useState(false);
  const selectedTemplate: ResumeTemplateId = isResumeTemplateId(templateSettings?.template)
    ? templateSettings.template
    : isResumeTemplateId(templateId)
    ? templateId
    : DEFAULT_TEMPLATE_ID;
  const settings: TemplateSettings = {
    ...DEFAULT_TEMPLATE_SETTINGS,
    ...templateSettings,
    template: selectedTemplate,
  };

  const handleUpdate = async () => {
    if (!updateQuery.trim() || isUpdating) return;
    setIsUpdating(true);
    try {
      const res = await fetch(`${getApiBase()}/api/cv/tailored-resume`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          resume_id: resumeId,
          user_query: updateQuery,
          tailored_resume_payload: tailoredResumePayload,
          raw_jd: rawJobDescription,
          template_settings: settings,
        }),
      });
      if (!res.ok) {
        const error = await res.json().catch(() => null);
        throw new Error(error?.detail || "Update failed");
      }
      const data = await res.json();
      onUpdateSuccess(data.tailored_resume_payload, data.ats_scores);
      if (data.template_settings && onSettingsChange) onSettingsChange(data.template_settings);
      setShowUpdateModal(false);
      setUpdateQuery("");
    } catch (error) {
      console.error("Failed to update resume", error);
      alert("Failed to update resume. Please check backend connection.");
    } finally {
      setIsUpdating(false);
    }
  };

  const handleDownload = () => {
    window.print();
    setDownloadSuccess(true);
    window.setTimeout(() => setDownloadSuccess(false), 3000);
  };

  const handleDownloadLatex = () => {
    const source = generateLatexResume(tailoredResumePayload, settings);
    const file = new Blob([source], { type: "application/x-tex;charset=utf-8" });
    const url = URL.createObjectURL(file);
    const link = document.createElement("a");
    link.href = url;
    link.download = "tailored-resume.tex";
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl p-4 glass-panel print:hidden">
        <div className="flex items-center gap-2">
          <span className="h-2.5 w-2.5 animate-pulse rounded-full bg-emerald-500" />
          <span className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)]">
            {selectedTemplate.replaceAll("-", " ")} template
          </span>
        </div>
        <div className="flex items-center gap-2">
          {selectedTemplate === "latex" && (
            <button
              onClick={handleDownloadLatex}
              className="flex items-center gap-1.5 rounded-xl border border-slate-400/30 bg-slate-500/10 px-4 py-2 text-xs font-bold text-slate-700 transition-all hover:-translate-y-0.5 dark:text-slate-200"
              title="Download LaTeX source generated from this tailored resume"
            >
              <FileCode2 className="h-3.5 w-3.5" />
              Download .tex
            </button>
          )}
          <button
            onClick={() => setShowUpdateModal(true)}
            className="flex items-center gap-1.5 rounded-xl border border-indigo-500/20 bg-indigo-500/10 px-3.5 py-2 text-xs font-semibold text-indigo-600 transition-all hover:-translate-y-0.5 dark:text-indigo-300"
          >
            <Sparkles className="h-3.5 w-3.5" /> AI Edit / Tweak
          </button>
          <button
            onClick={handleDownload}
            className="flex items-center gap-1.5 rounded-xl bg-[var(--primary-gradient)] px-4 py-2 text-xs font-bold text-white shadow-md shadow-indigo-500/20 transition-all hover:-translate-y-0.5 active:scale-95"
          >
            {downloadSuccess ? <CheckCircle2 className="h-3.5 w-3.5 text-emerald-200" /> : <Download className="h-3.5 w-3.5" />}
            {downloadSuccess ? "Downloaded!" : "Download PDF"}
          </button>
        </div>
      </div>

      <div id="resume-document-sheet" className="overflow-hidden rounded-2xl shadow-xl print:rounded-none print:shadow-none">
        <ResumeComponent
          resumeData={tailoredResumePayload}
          templateSettings={settings}
        />
      </div>

      {showUpdateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 p-4 backdrop-blur-sm print:hidden">
          <div className="w-full max-w-lg space-y-4 rounded-3xl p-6 glass-panel">
            <div className="flex items-center justify-between">
              <h3 className="flex items-center gap-2 font-bold text-[var(--text-heading)]"><Sparkles className="h-5 w-5 text-indigo-500" /> Update resume with AI</h3>
              <button onClick={() => setShowUpdateModal(false)} aria-label="Close edit dialog" className="text-[var(--text-muted)]">✕</button>
            </div>
            <p className="text-xs leading-relaxed text-[var(--text-muted)]">Describe the edit you want. Existing facts remain the source of truth.</p>
            <textarea rows={4} value={updateQuery} onChange={(event) => setUpdateQuery(event.target.value)} placeholder="e.g. Rewrite my summary for a backend engineering role." className="w-full rounded-2xl border border-[var(--border-subtle)] bg-[var(--bg-elevated)] p-3 text-sm text-[var(--text-body)] outline-none focus:ring-2 focus:ring-[var(--ring)]" />
            <div className="flex justify-end gap-2">
              <button onClick={() => setShowUpdateModal(false)} className="rounded-xl px-4 py-2 text-xs font-semibold text-[var(--text-muted)]">Cancel</button>
              <button onClick={handleUpdate} disabled={isUpdating || !updateQuery.trim()} className="rounded-xl bg-[var(--primary-gradient)] px-4 py-2 text-xs font-bold text-white disabled:opacity-50">{isUpdating ? "Applying..." : "Apply changes"}</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
