"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { Sparkles, LogIn, UserPlus, LogOut, User, Menu, X, ArrowUpRight } from "lucide-react";
import ThemeToggle from "@/components/ThemeToggle";

export default function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<{ name: string; email: string } | null>(null);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    try {
      const stored = localStorage.getItem("resumatch_user");
      if (stored) {
        setUser(JSON.parse(stored));
      }
    } catch (e) {
      console.error(e);
    }
  }, [pathname]);

  useEffect(() => {
    setMenuOpen(false);
  }, [pathname]);

  const handleLogout = () => {
    localStorage.removeItem("resumatch_user");
    setUser(null);
    router.push("/login");
  };

  const navLinks = [
    { href: "/", label: "Home" },
    { href: "/upload", label: "Upload & ATS" },
    { href: "/resumes", label: "Past resumes" },
    { href: "/outreach-messages", label: "Outreach messages" },
  ];

  return (
    <header className="sticky top-0 z-50 w-full border-b border-slate-200/70 bg-white/75 backdrop-blur-xl transition-colors dark:border-white/[0.07] dark:bg-[#0d1017]/75">
      <div className="mx-auto flex h-[4.5rem] max-w-7xl items-center justify-between px-4 sm:px-6">
        {/* Brand */}
        <Link href="/" className="flex items-center gap-3 group">
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-[var(--primary-gradient)] text-sm font-black text-white shadow-lg shadow-indigo-500/20 transition-transform group-hover:rotate-[-5deg] group-hover:scale-105">
            R<span className="text-amber-200">.</span>
          </div>
          <div className="flex flex-col">
            <span className="flex items-center gap-1 text-base font-extrabold tracking-tight text-[var(--text-heading)]">
              ResuMatch
              <span className="rounded-full bg-indigo-100 px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wider text-indigo-700 dark:bg-indigo-400/15 dark:text-indigo-200">
                AI
              </span>
            </span>
            <span className="mt-0.5 text-[10px] font-medium text-[var(--text-muted)]">
              Career clarity, engineered
            </span>
          </div>
        </Link>

        {/* Center Navigation Links */}
        <nav className="hidden items-center gap-1 rounded-2xl border border-slate-200/70 bg-slate-100/70 p-1 dark:border-white/[0.07] dark:bg-white/[0.04] md:flex">
          {navLinks.map((link) => {
            const isActive = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`rounded-xl px-4 py-2 text-xs font-semibold transition-all ${
                  isActive
                    ? "bg-white text-[var(--primary-accent)] shadow-sm dark:bg-slate-800 dark:text-indigo-200"
                    : "text-[var(--text-muted)] hover:text-[var(--text-heading)]"
                }`}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>

        {/* Right Actions */}
        <div className="flex items-center gap-2.5">
          <ThemeToggle />
          <button
            type="button"
            aria-label={menuOpen ? "Close navigation menu" : "Open navigation menu"}
            aria-expanded={menuOpen}
            onClick={() => setMenuOpen((open) => !open)}
            className="rounded-xl border border-slate-200/70 p-2 text-[var(--text-body)] transition hover:bg-slate-100 dark:border-white/[0.08] dark:hover:bg-white/[0.06] md:hidden"
          >
            {menuOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
          </button>

          {user ? (
            <div className="flex items-center gap-2">
              <div className="hidden items-center gap-1.5 rounded-xl border border-slate-200 bg-slate-100 px-3 py-1.5 text-xs font-medium text-[var(--text-body)] dark:border-white/[0.08] dark:bg-white/[0.05] sm:flex">
                <User className="h-3.5 w-3.5 text-[var(--primary-accent)]" />
                <span className="max-w-[120px] truncate">{user.name}</span>
              </div>
              <button
                onClick={handleLogout}
                title="Log out"
                className="rounded-xl p-2 text-[var(--text-muted)] transition-colors hover:bg-rose-50 hover:text-rose-600 dark:hover:bg-rose-500/10"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <Link
                href="/login"
                className="rounded-xl px-3 py-2 text-xs font-semibold text-[var(--text-body)] transition-colors hover:bg-slate-100 dark:hover:bg-white/[0.06]"
              >
                Sign In
              </Link>
              <Link
                href="/signup"
                className="rounded-xl bg-[var(--primary-gradient)] px-4 py-2 text-xs font-bold text-white shadow-md shadow-indigo-500/20 transition-all hover:-translate-y-0.5 active:scale-95"
              >
                Sign Up
              </Link>
            </div>
          )}
        </div>
      </div>
      {menuOpen && (
        <div className="border-t border-slate-200/70 bg-white/95 px-4 py-3 shadow-lg backdrop-blur-xl dark:border-white/[0.07] dark:bg-[#131821]/95 md:hidden">
          <nav className="mx-auto flex max-w-7xl flex-col gap-1">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className={`flex items-center justify-between rounded-xl px-4 py-3 text-sm font-semibold ${
                  pathname === link.href
                    ? "bg-indigo-50 text-indigo-700 dark:bg-indigo-400/10 dark:text-indigo-200"
                    : "text-[var(--text-body)] hover:bg-slate-100 dark:hover:bg-white/[0.05]"
                }`}
              >
                {link.label}
                <ArrowUpRight className="h-4 w-4 opacity-60" />
              </Link>
            ))}
          </nav>
        </div>
      )}
    </header>
  );
}
