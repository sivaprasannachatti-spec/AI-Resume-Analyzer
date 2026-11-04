"use client";

import { Check, FileText, Sparkles } from "lucide-react";
import { TEMPLATE_SETTINGS, ResumeTemplateId } from "@/components/resume/template-settings";

interface ResumeTemplateGalleryProps {
  selectedTemplate: ResumeTemplateId;
  onSelect: (template: ResumeTemplateId) => void;
}

export default function ResumeTemplateGallery({ selectedTemplate, onSelect }: ResumeTemplateGalleryProps) {
  return (
    <section aria-labelledby="template-heading" className="space-y-4">
      <div className="flex items-end justify-between gap-4">
        <div>
          <p className="mb-1 text-[11px] font-bold uppercase tracking-[0.18em] text-[var(--primary-accent)]">Step 01</p>
          <h2 id="template-heading" className="text-xl font-bold tracking-tight text-[var(--text-heading)]">Choose your resume template</h2>
        </div>
        <span className="hidden items-center gap-1 text-xs text-[var(--text-muted)] sm:flex"><Sparkles className="h-3.5 w-3.5 text-[var(--warm-accent)]" /> Browser and PDF use the same renderer</span>
      </div>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
        {TEMPLATE_SETTINGS.map((template) => {
          const selected = selectedTemplate === template.id;
          return (
            <button key={template.id} type="button" onClick={() => onSelect(template.id)} aria-pressed={selected} className={`group rounded-2xl border p-2 text-left transition-all duration-300 hover:-translate-y-1 sm:p-3 ${selected ? "border-indigo-400 bg-indigo-50/70 shadow-lg shadow-indigo-500/10 dark:border-indigo-300/60 dark:bg-indigo-400/10" : "border-[var(--border-subtle)] bg-[var(--bg-card)] hover:border-indigo-300/60"}`}>
              <div className="relative aspect-[0.72] overflow-hidden rounded-xl border border-slate-200 bg-white p-3 shadow-sm dark:border-slate-700 dark:bg-slate-100">
                {selected && <span className="absolute right-2 top-2 z-10 flex h-5 w-5 items-center justify-center rounded-full bg-indigo-600 text-white"><Check className="h-3 w-3" /></span>}
                <div className="mb-3 h-2 w-2/5 rounded-full" style={{ backgroundColor: template.accent }} />
                <div className="mb-3 h-1.5 w-3/4 rounded-full bg-slate-800" />
                <div className="mb-4 space-y-1.5"><div className="h-1 w-full rounded-full bg-slate-300" /><div className="h-1 w-5/6 rounded-full bg-slate-300" /><div className="h-1 w-2/3 rounded-full bg-slate-300" /></div>
                <div className="grid grid-cols-2 gap-2"><div className="space-y-1.5"><div className="h-1 w-2/3 rounded-full bg-slate-500" /><div className="h-1 w-full rounded-full bg-slate-200" /><div className="h-1 w-5/6 rounded-full bg-slate-200" /></div><div className="space-y-1.5"><div className="h-1 w-2/3 rounded-full bg-slate-500" /><div className="h-1 w-full rounded-full bg-slate-200" /></div></div>
              </div>
              <div className="mt-2 flex items-center gap-1.5"><FileText className="h-3.5 w-3.5" style={{ color: template.accent }} /><span className="text-xs font-bold text-[var(--text-heading)]">{template.name}</span></div>
              <p className="mt-1 text-[10px] leading-relaxed text-[var(--text-muted)]">{template.description}</p>
            </button>
          );
        })}
      </div>
    </section>
  );
}
