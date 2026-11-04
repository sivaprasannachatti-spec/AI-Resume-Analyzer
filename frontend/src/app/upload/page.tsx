"use client";

import { useState } from "react";
import { 
  Sparkles, 
  ArrowRight, 
  Loader2, 
  CheckCircle2, 
  AlertCircle
} from "lucide-react";
import Navbar from "@/components/Navbar";
import ResumeDropzone from "@/components/ResumeDropzone";
import { apiFetch, getApiBase } from "@/lib/api";
import ResumeTemplateGallery from "@/components/ResumeTemplateGallery";
import { useRouter } from "next/navigation";
import { DEFAULT_TEMPLATE_ID, DEFAULT_TEMPLATE_SETTINGS, ResumeTemplateId } from "@/components/resume/template-settings";

export default function UploadPage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [jdText, setJdText] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingStatus, setProcessingStatus] = useState<string>("");
  const [processingStage, setProcessingStage] = useState<"upload" | "tailor" | "prepare" | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [, setTailoringResult] = useState<any>(null);
  const [selectedTemplate, setSelectedTemplate] = useState<ResumeTemplateId>(DEFAULT_TEMPLATE_ID);
  const router = useRouter();

  const sampleJDs = [
    {
      title: "Senior Backend Engineer",
      text: "We are seeking a Senior Backend Engineer to architect and build high-performance REST APIs. Required skills: Python, FastAPI, PostgreSQL, Docker, AWS. Preferred: Redis, Microservices, CI/CD pipelines, and System Design.",
    },
    {
      title: "Full Stack Developer",
      text: "Looking for a Full Stack Developer proficient in React, Next.js, and Node.js with TypeScript. Must have experience building modern user interfaces, integrating RESTful APIs, and using PostgreSQL and Docker.",
    },
    {
      title: "AI / ML Platform Engineer",
      text: "Seeking an AI/ML Engineer experienced in LangChain, Python, LLM orchestration, model serving, and vector embeddings. Solid knowledge of Docker, FastAPI, and cloud deployment required.",
    },
  ];

  const handleGenerateAndRedirect = async () => {
    if (!selectedFile) {
      setErrorMsg("Please select your PDF resume first.");
      return;
    }
    if (!jdText.trim()) {
      setErrorMsg("Please provide or select a target job description.");
      return;
    }

    setIsProcessing(true);
    setProcessingStage("upload");
    setErrorMsg(null);

    try {
      // 1. Process uploaded resume file with Docling AI
      setProcessingStatus("Uploading your PDF and extracting its structure...");
      const formData = new FormData();
      formData.append("file", selectedFile);

      const API_BASE = getApiBase();
      const uploadRes = await fetch(`${API_BASE}/api/resume/upload`, {
        method: "POST",
        body: formData,
      });

      if (!uploadRes.ok) {
        const errData = await uploadRes.json().catch(() => ({ detail: `Upload failed (${uploadRes.status})` }));
        throw new Error(errData.detail || errData.error || `Upload failed with status ${uploadRes.status}`);
      }

      const uploadData = await uploadRes.json();
      const resumeId = uploadData.resume_id;
      // 2. Generate tailored resume payload based on target JD and evaluate ATS score
      setProcessingStage("tailor");
      setProcessingStatus("Matching the job description and refining your resume...");
      const tailoringData = await apiFetch("/api/cv/tailor", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          resume_id: resumeId,
          raw_jd: jdText,
        }),
      });
      setProcessingStage("prepare");
      setProcessingStatus("Preparing your content review and formatted preview...");
      const resultWithTemplate = {
        ...tailoringData,
        template: selectedTemplate,
        templateSettings: { ...DEFAULT_TEMPLATE_SETTINGS, template: selectedTemplate },
      };
      setTailoringResult(resultWithTemplate);
      sessionStorage.setItem("resumatch_tailoring_preview", JSON.stringify(resultWithTemplate));
      setProcessingStatus(`Tailored resume ready for resume ${resumeId}.`);
      setIsProcessing(false);
      setProcessingStage(null);
      router.push("/tailored-resume");
    } catch (err: any) {
      console.error(err);
      setErrorMsg(err.message || "An error occurred while generating tailored resume.");
      setIsProcessing(false);
      setProcessingStatus("");
      setProcessingStage(null);
    }
  };

  return (
    <div className="min-h-screen text-slate-800 dark:text-slate-100 relative">
      <div className="ambient-canvas" />
      <Navbar />

      <main className="max-w-6xl mx-auto px-4 sm:px-6 py-10 sm:py-16 space-y-10">
        <div className="mx-auto max-w-3xl space-y-3 text-center">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-blue-50 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 border border-blue-200/80 dark:border-blue-800/60">
            <Sparkles className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" />
            <span>Resume studio · built for your next opportunity</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-slate-900 dark:text-white">
            Build a resume that gets read
          </h1>
          <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400">
            Pick a visual direction, upload your source resume, and tailor it to the role you want next.
          </p>
        </div>

        {errorMsg && (
          <div className="max-w-xl mx-auto p-3.5 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900/60 text-rose-700 dark:text-rose-400 text-xs flex items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{errorMsg}</span>
            </div>
            <button onClick={() => setErrorMsg(null)} className="text-xs font-bold underline">
              Dismiss
            </button>
          </div>
        )}

        <div className="space-y-8">
          <ResumeTemplateGallery
            selectedTemplate={selectedTemplate}
            onSelect={setSelectedTemplate}
          />
          <div className="grid grid-cols-1 items-start gap-8 lg:grid-cols-2">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="flex h-7 w-7 items-center justify-center rounded-xl bg-[var(--primary-gradient)] text-xs font-bold text-white">
                  2
                </span>
                <h2 className="font-bold text-base text-slate-900 dark:text-white">
                  Upload PDF Resume
                </h2>
              </div>
              {selectedFile && (
                <span className="text-xs font-semibold text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
                  <CheckCircle2 className="w-4 h-4" /> Selected
                </span>
              )}
            </div>

            <ResumeDropzone
              onFileSelected={setSelectedFile}
              selectedFile={selectedFile}
              isLoading={isProcessing}
            />
          </div>

          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="flex h-7 w-7 items-center justify-center rounded-xl bg-teal-600 text-xs font-bold text-white">
                  3
                </span>
                <h2 className="font-bold text-base text-slate-900 dark:text-white">
                  Target Job Description
                </h2>
              </div>
              <span className="text-xs text-slate-400">Select preset or paste</span>
            </div>

            {/* Preset JD Quick Pills */}
            <div className="flex flex-wrap gap-1.5">
              {sampleJDs.map((s, idx) => (
                <button
                  key={idx}
                  onClick={() => setJdText(s.text)}
                  className="px-3 py-1.5 rounded-xl text-xs font-medium bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 border border-slate-200/80 dark:border-slate-700 transition-all hover:scale-105 active:scale-95"
                >
                  {s.title}
                </button>
              ))}
            </div>

            <textarea
              rows={8}
              value={jdText}
              onChange={(e) => setJdText(e.target.value)}
              placeholder="Paste job description requirements, responsibilities, and qualifications here..."
              className="w-full p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 text-xs sm:text-sm text-slate-800 dark:text-slate-200 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all resize-none shadow-sm"
            />

            {/* Submit / Tailor Action Button */}
            <button
              onClick={handleGenerateAndRedirect}
              disabled={isProcessing || !selectedFile || !jdText.trim()}
              className="w-full py-4 rounded-2xl font-bold text-sm bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-600/25 transition-all hover:scale-[1.01] active:scale-[0.98] disabled:opacity-40 disabled:hover:scale-100 flex items-center justify-center gap-2.5"
            >
              {isProcessing ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span>{processingStatus || "Tailoring resume..."}</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-5 h-5 text-amber-300" />
                  <span>Generate Tailored Resume</span>
                  <ArrowRight className="w-4 h-4 ml-1" />
                </>
              )}
            </button>
            {isProcessing && processingStage && (
              <section
                role="status"
                aria-live="polite"
                className="overflow-hidden rounded-2xl border border-blue-200/80 bg-white/90 p-4 shadow-lg shadow-blue-900/5 dark:border-blue-400/20 dark:bg-slate-900/90"
              >
                <div className="flex items-start gap-3">
                  <div className="relative mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-blue-100 text-blue-700 dark:bg-blue-400/10 dark:text-blue-300">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span className="absolute inset-0 rounded-xl ring-2 ring-blue-400/30 animate-ping" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-bold text-slate-900 dark:text-white">{processingStatus}</p>
                    <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                      This can take a little while. Your progress is still active.
                    </p>
                  </div>
                </div>
                <div className="mt-4 h-1.5 overflow-hidden rounded-full bg-blue-100 dark:bg-slate-700">
                  <div className="resume-progress-sweep h-full w-1/3 rounded-full bg-gradient-to-r from-blue-500 via-indigo-500 to-teal-400" />
                </div>
                <ol className="mt-4 grid grid-cols-3 gap-2 text-[10px] font-semibold sm:text-xs">
                  {[
                    { id: "upload", label: "Read resume" },
                    { id: "tailor", label: "Tailor content" },
                    { id: "prepare", label: "Prepare preview" },
                  ].map((step, index) => {
                    const stages = ["upload", "tailor", "prepare"];
                    const currentIndex = stages.indexOf(processingStage);
                    const complete = index < currentIndex;
                    const active = step.id === processingStage;
                    return (
                      <li
                        key={step.id}
                        className={`flex items-center gap-1.5 ${active ? "text-blue-700 dark:text-blue-300" : complete ? "text-teal-700 dark:text-teal-300" : "text-slate-400 dark:text-slate-500"}`}
                      >
                        <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${active ? "animate-pulse bg-blue-500" : complete ? "bg-teal-500" : "bg-slate-300 dark:bg-slate-600"}`} />
                        {step.label}
                      </li>
                    );
                  })}
                </ol>
              </section>
            )}
          </div>
          </div>
        </div>
      </main>
    </div>
  );
}
