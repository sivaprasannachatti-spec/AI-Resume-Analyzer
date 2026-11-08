"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ExternalLink, FileText, Loader2 } from "lucide-react";
import Navbar from "@/components/Navbar";
import { apiFetch } from "@/lib/api";

interface ResumeHistoryItem {
  resume_id: string;
  candidate_name: string;
  resume_url: string;
  uploaded_at: string;
  tailored_resume_id: string | null;
  tailored_updated_at: string | null;
  tailored_file_url: string | null;
}

export default function ResumesPage() {
  const [resumes, setResumes] = useState<ResumeHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadHistory = async () => {
      try {
        const storedUser = localStorage.getItem("resumatch_user");
        const userId = storedUser
          ? (JSON.parse(storedUser) as { user_id?: string }).user_id
          : undefined;
        const query = userId ? `?user_id=${encodeURIComponent(userId)}` : "";
        const result = await apiFetch(`/api/resume/history${query}`);
        setResumes(result.resumes);
      } catch (reason) {
        setError(reason instanceof Error ? reason.message : "Unable to load resume history.");
      } finally {
        setLoading(false);
      }
    };

    void loadHistory();
  }, []);

  return (
    <div className="min-h-screen">
      <div className="ambient-canvas" />
      <Navbar />
      <main className="mx-auto max-w-5xl space-y-6 px-4 py-10 sm:px-6 sm:py-14">
        <header className="space-y-2">
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-[var(--primary-accent)]">Library</p>
          <h1 className="text-3xl font-extrabold tracking-tight text-[var(--text-heading)]">Past resumes</h1>
          <p className="text-sm text-[var(--text-muted)]">Your uploaded resumes and their latest tailored-resume status.</p>
        </header>

        {error && (
          <p role="alert" className="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700 dark:border-rose-400/20 dark:bg-rose-400/10 dark:text-rose-200">
            {error}
          </p>
        )}

        {loading ? (
          <div className="flex justify-center rounded-3xl p-12 glass-panel">
            <Loader2 className="h-7 w-7 animate-spin text-[var(--primary-accent)]" />
          </div>
        ) : !error && resumes.length === 0 ? (
          <div className="space-y-4 rounded-3xl p-8 text-center glass-panel">
            <FileText className="mx-auto h-8 w-8 text-[var(--primary-accent)]" />
            <p className="text-sm text-[var(--text-muted)]">No resumes uploaded yet.</p>
            <Link href="/upload" className="inline-flex rounded-xl bg-[var(--primary-gradient)] px-4 py-2.5 text-xs font-bold text-white">
              Upload a resume
            </Link>
          </div>
        ) : (
          <ul className="space-y-3">
            {resumes.map((resume) => (
              <li key={resume.resume_id} className="flex flex-col gap-4 rounded-3xl p-5 glass-panel sm:flex-row sm:items-center sm:justify-between">
                <div className="min-w-0">
                  <h2 className="truncate text-base font-bold text-[var(--text-heading)]">{resume.candidate_name}</h2>
                  <p className="mt-1 text-xs text-[var(--text-muted)]">
                    Uploaded {new Date(resume.uploaded_at).toLocaleString()}
                  </p>
                  <p className="mt-2 text-xs text-[var(--text-body)]">
                    {resume.tailored_resume_id
                      ? `Tailored resume confirmed${resume.tailored_updated_at ? ` · updated ${new Date(resume.tailored_updated_at).toLocaleDateString()}` : ""}`
                      : "Not tailored yet"}
                  </p>
                </div>
                <div className="flex shrink-0 flex-wrap gap-2">
                  {resume.resume_url && (
                    <a
                      href={resume.resume_url}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-2 rounded-xl border border-[var(--border-subtle)] px-3 py-2 text-xs font-semibold text-[var(--text-body)] hover:border-[var(--primary-accent)]"
                    >
                      <ExternalLink className="h-3.5 w-3.5" /> Source PDF
                    </a>
                  )}
                  {resume.tailored_file_url && (
                    <a
                      href={resume.tailored_file_url}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-2 rounded-xl bg-[var(--primary-gradient)] px-3 py-2 text-xs font-semibold text-white"
                    >
                      <ExternalLink className="h-3.5 w-3.5" /> Tailored PDF
                    </a>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}
      </main>
    </div>
  );
}
