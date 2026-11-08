"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Loader2, MessageSquareText, Save } from "lucide-react";
import Navbar from "@/components/Navbar";
import { apiFetch } from "@/lib/api";

interface OutreachHistoryItem {
  outreach_id: string;
  tailored_resume_id: string;
  resume_id: string;
  candidate_name: string;
  message: string;
  created_at: string;
  updated_at: string;
}

export default function OutreachMessagesPage() {
  const [messages, setMessages] = useState<OutreachHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [savingId, setSavingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    const loadHistory = async () => {
      try {
        const storedUser = localStorage.getItem("resumatch_user");
        const userId = storedUser
          ? (JSON.parse(storedUser) as { user_id?: string }).user_id
          : undefined;
        const query = userId ? `?user_id=${encodeURIComponent(userId)}` : "";
        const result = await apiFetch(`/api/cv/outreach-messages/history${query}`);
        setMessages(result.outreach_messages);
      } catch (reason) {
        setError(reason instanceof Error ? reason.message : "Unable to load outreach-message history.");
      } finally {
        setLoading(false);
      }
    };

    void loadHistory();
  }, []);

  const updateMessage = (outreachId: string, message: string) => {
    setMessages((current) =>
      current.map((item) =>
        item.outreach_id === outreachId ? { ...item, message } : item,
      ),
    );
    setNotice(null);
  };

  const saveMessage = async (item: OutreachHistoryItem) => {
    setSavingId(item.outreach_id);
    setError(null);
    setNotice(null);
    try {
      const result = await apiFetch(`/api/cv/outreach-messages/${item.outreach_id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: item.message }),
      });
      setMessages((current) =>
        current.map((saved) =>
          saved.outreach_id === item.outreach_id
            ? { ...saved, message: result.message, updated_at: result.updated_at }
            : saved,
        ),
      );
      setNotice("Outreach message saved.");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to save this outreach message.");
    } finally {
      setSavingId(null);
    }
  };

  return (
    <div className="min-h-screen">
      <div className="ambient-canvas" />
      <Navbar />
      <main className="mx-auto max-w-5xl space-y-6 px-4 py-10 sm:px-6 sm:py-14">
        <header className="space-y-2">
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-[var(--primary-accent)]">Library</p>
          <h1 className="text-3xl font-extrabold tracking-tight text-[var(--text-heading)]">Past outreach messages</h1>
          <p className="text-sm text-[var(--text-muted)]">Review and edit saved cold outreach drafts.</p>
        </header>

        {error && (
          <p role="alert" className="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700 dark:border-rose-400/20 dark:bg-rose-400/10 dark:text-rose-200">
            {error}
          </p>
        )}
        {notice && <p role="status" className="text-sm font-semibold text-emerald-700 dark:text-emerald-300">{notice}</p>}

        {loading ? (
          <div className="flex justify-center rounded-3xl p-12 glass-panel">
            <Loader2 className="h-7 w-7 animate-spin text-[var(--primary-accent)]" />
          </div>
        ) : !error && messages.length === 0 ? (
          <div className="space-y-4 rounded-3xl p-8 text-center glass-panel">
            <MessageSquareText className="mx-auto h-8 w-8 text-[var(--primary-accent)]" />
            <p className="text-sm text-[var(--text-muted)]">No outreach messages saved yet.</p>
            <Link href="/upload" className="inline-flex rounded-xl bg-[var(--primary-gradient)] px-4 py-2.5 text-xs font-bold text-white">
              Tailor a resume
            </Link>
          </div>
        ) : (
          <ul className="space-y-4">
            {messages.map((item) => (
              <li key={item.outreach_id} className="space-y-4 rounded-3xl p-5 glass-panel">
                <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
                  <h2 className="text-sm font-bold text-[var(--text-heading)]">{item.candidate_name}</h2>
                  <p className="text-xs text-[var(--text-muted)]">
                    Updated {new Date(item.updated_at).toLocaleString()}
                  </p>
                </div>
                <label className="block text-xs font-semibold text-[var(--text-body)]">
                  Message
                  <textarea
                    value={item.message}
                    onChange={(event) => updateMessage(item.outreach_id, event.target.value)}
                    rows={14}
                    aria-label={`Edit outreach message for ${item.candidate_name}`}
                    spellCheck
                    className="mt-1.5 min-h-72 w-full resize-y rounded-2xl border border-[var(--border-subtle)] bg-[var(--bg-elevated)] px-4 py-4 text-base font-normal leading-7 text-[var(--text-body)]"
                  />
                </label>
                <div className="flex justify-end">
                  <button
                    type="button"
                    onClick={() => void saveMessage(item)}
                    disabled={savingId === item.outreach_id || !item.message.trim()}
                    className="inline-flex items-center gap-2 rounded-xl bg-[var(--primary-gradient)] px-4 py-2.5 text-xs font-bold text-white disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {savingId === item.outreach_id ? (
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    ) : (
                      <Save className="h-3.5 w-3.5" />
                    )}
                    {savingId === item.outreach_id ? "Saving..." : "Save changes"}
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </main>
    </div>
  );
}
