"use client";

import React, { useLayoutEffect, useRef, useState } from "react";
import { ResumeSchema, WorkExperience, Project, Education, CustomSection } from "@/types/resume";
import {
  TemplateSettings,
  DEFAULT_TEMPLATE_SETTINGS,
  ResumeTemplateId,
  ACCENT_COLOR_MAP,
  FONT_SIZE_MAP,
  ITEM_SPACING_MAP,
  LINE_HEIGHT_MAP,
  SECTION_SPACING_MAP,
  settingsToCssVars,
} from "./template-settings";
import {
  Mail,
  Phone,
  MapPin,
  ExternalLink,
} from "lucide-react";

const GithubIcon = ({ className = "w-3 h-3" }: { className?: string }) => (
  <svg className={className} viewBox="0 0 24 24" fill="currentColor">
    <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/>
  </svg>
);

const LinkedinIcon = ({ className = "w-3 h-3" }: { className?: string }) => (
  <svg className={className} viewBox="0 0 24 24" fill="currentColor">
    <path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"/>
  </svg>
);

export interface ResumeTemplateProps {
  resume: ResumeSchema;
  settings?: TemplateSettings;
  variant?: string;
}

function parseSkills(resume: ResumeSchema): { categories: Record<string, string[]>; flatList: string[] } {
  const add: any = resume.additional;
  let rawSkills: any = null;

  if (Array.isArray(add) && add.length > 0) {
    rawSkills = add[0]?.technicalSkills || add[0]?.skills;
  } else if (add && typeof add === "object") {
    rawSkills = add.technicalSkills || add.skills;
  }
  if (!rawSkills && resume.skills) {
    rawSkills = resume.skills;
  }

  if (rawSkills && typeof rawSkills === "object" && !Array.isArray(rawSkills)) {
    const flat: string[] = [];
    const categories: Record<string, string[]> = {};
    for (const [cat, val] of Object.entries(rawSkills)) {
      if (Array.isArray(val)) {
        categories[cat] = val.map(String);
        flat.push(...val.map(String));
      } else if (typeof val === "string") {
        const items = val.split(",").map((s) => s.trim()).filter(Boolean);
        categories[cat] = items;
        flat.push(...items);
      }
    }
    return { categories, flatList: flat };
  }

  if (Array.isArray(rawSkills)) {
    return { categories: {}, flatList: rawSkills.map(String) };
  }

  return { categories: {}, flatList: [] };
}

function parseListSection(val: any): string[] {
  if (Array.isArray(val)) return val.map(String);
  if (typeof val === "string") return val.split(",").map((s) => s.trim()).filter(Boolean);
  return [];
}

export function ResumeBase({
  resume,
  settings = DEFAULT_TEMPLATE_SETTINGS,
  variant,
}: ResumeTemplateProps) {
  const contentRef = useRef<HTMLDivElement>(null);
  const [fitScale, setFitScale] = useState(1);
  const templateId: ResumeTemplateId = (variant as ResumeTemplateId) || settings.template || "swiss-single";
  const accent = ACCENT_COLOR_MAP[settings.accentColor] || ACCENT_COLOR_MAP.blue;
  const isCompact = settings.compactMode;
  const isA4 = settings.pageSize === "A4";

  const pageWidth = isA4 ? "210mm" : "8.5in";
  const pageHeight = isA4 ? "297mm" : "11in";
  const marginTop = settings.margins.top;
  const marginBottom = settings.margins.bottom;
  const marginLeft = settings.margins.left;
  const marginRight = settings.margins.right;
  const spacingFactor = isCompact ? 0.6 : 1;
  const sectionGap = `calc(${SECTION_SPACING_MAP[settings.spacing.section]} * ${spacingFactor})`;
  const itemGap = `calc(${ITEM_SPACING_MAP[settings.spacing.item]} * ${spacingFactor})`;
  const lineHeight = LINE_HEIGHT_MAP[settings.spacing.lineHeight] * (isCompact ? 0.92 : 1);
  const baseFontSize = FONT_SIZE_MAP[settings.fontSize.base];
  const bodyFont = settings.fontSize.bodyFont === "serif"
    ? "Georgia, serif"
    : settings.fontSize.bodyFont === "mono"
      ? "ui-monospace, monospace"
      : "Arial, sans-serif";
  const resumeStyle = {
    ...settingsToCssVars(settings),
    width: pageWidth,
    height: pageHeight,
    maxHeight: pageHeight,
    paddingTop: `${marginTop}mm`,
    paddingBottom: `${marginBottom}mm`,
    paddingLeft: `${marginLeft}mm`,
    paddingRight: `${marginRight}mm`,
    fontSize: baseFontSize,
    lineHeight,
    fontFamily: bodyFont,
    overflow: "hidden",
    backgroundColor: "#ffffff",
    color: "#0f172a",
  } as React.CSSProperties;
  const headerFont = settings.fontSize.headerFont === "serif" || templateId === "latex"
    ? "Georgia, serif"
    : settings.fontSize.headerFont === "mono"
      ? "ui-monospace, monospace"
      : "Arial, sans-serif";

  useLayoutEffect(() => {
    const content = contentRef.current;
    if (!content) return;

    const pageHeightMm = isA4 ? 297 : 279.4;
    const availableHeight =
      (pageHeightMm - marginTop - marginBottom) * (96 / 25.4);
    const updateFit = () => {
      const contentHeight = content.scrollHeight;
      if (contentHeight > 0) {
        setFitScale(Math.min(1, availableHeight / contentHeight));
      }
    };

    updateFit();
    const observer = new ResizeObserver(updateFit);
    observer.observe(content);
    document.fonts?.ready.then(updateFit);
    window.addEventListener("beforeprint", updateFit);
    return () => {
      observer.disconnect();
      window.removeEventListener("beforeprint", updateFit);
    };
  }, [resume, settings, isA4, marginTop, marginBottom]);

  const { personalInfo, summary, workExperience = [], projects = [], education = [], customSections = [] } = resume;
  const { categories: skillCategories, flatList: technicalSkills } = parseSkills(resume);

  const add: any = Array.isArray(resume.additional) ? resume.additional[0] || {} : resume.additional || {};
  const languages = parseListSection(add.languages);
  const certifications = parseListSection(add.certificationsTraining);
  const awards = parseListSection(add.awards);

  const isSerif = templateId === "latex" || settings.fontSize?.headerFont === "serif";
  const fontFamilyClass = isSerif ? "font-serif" : "font-sans";

  // -------------------------------------------------------------
  // Contact Bar
  // -------------------------------------------------------------
  const ContactInfo = ({ centered = false, icons = false }: { centered?: boolean; icons?: boolean }) => (
    <div
      className={`flex flex-wrap items-center gap-x-2.5 gap-y-0.5 text-[length:var(--font-size-body)] text-slate-600 ${
        centered ? "justify-center" : "justify-start"
      }`}
    >
      {personalInfo.email && (
        <a
          href={`mailto:${personalInfo.email}`}
          className="flex items-center gap-1 text-slate-700 hover:text-slate-900 transition-colors"
        >
          {icons && <Mail className="w-2.5 h-2.5 text-slate-400 shrink-0" />}
          <span>{personalInfo.email}</span>
        </a>
      )}
      {personalInfo.phone && (
        <span className="flex items-center gap-1 text-slate-700">
          <span className="text-slate-300">|</span>
          {icons && <Phone className="w-2.5 h-2.5 text-slate-400 shrink-0" />}
          <span>{personalInfo.phone}</span>
        </span>
      )}
      {personalInfo.location && (
        <span className="flex items-center gap-1 text-slate-700">
          <span className="text-slate-300">|</span>
          {icons && <MapPin className="w-2.5 h-2.5 text-slate-400 shrink-0" />}
          <span>{personalInfo.location}</span>
        </span>
      )}
      {personalInfo.linkedin_url && (
        <a
          href={personalInfo.linkedin_url.startsWith("http") ? personalInfo.linkedin_url : `https://${personalInfo.linkedin_url}`}
          target="_blank"
          rel="noreferrer"
          className="flex items-center gap-1 text-blue-600 hover:underline"
        >
          <span className="text-slate-300">|</span>
          {icons && <LinkedinIcon className="w-2.5 h-2.5 text-blue-600 shrink-0" />}
          <span>LinkedIn</span>
        </a>
      )}
      {personalInfo.github_url && (
        <a
          href={personalInfo.github_url.startsWith("http") ? personalInfo.github_url : `https://${personalInfo.github_url}`}
          target="_blank"
          rel="noreferrer"
          className="flex items-center gap-1 text-slate-800 hover:underline"
        >
          <span className="text-slate-300">|</span>
          {icons && <GithubIcon className="w-2.5 h-2.5 text-slate-700 shrink-0" />}
          <span>GitHub</span>
        </a>
      )}
    </div>
  );

  // -------------------------------------------------------------
  // Section Headings matching Template Style
  // -------------------------------------------------------------
  const SectionHeading = ({ title }: { title: string }) => {
    if (templateId === "latex") {
      return (
        <div className="border-b border-slate-900 pb-0.5 mb-1 mt-1.5 flex items-baseline justify-between">
          <h2 className="text-[length:var(--font-size-section)] font-serif font-bold uppercase tracking-wider text-slate-950">
            {title}
          </h2>
        </div>
      );
    }
    if (templateId === "clean") {
      return (
        <div className="border-b border-slate-200 pb-0.5 mb-1 mt-1.5">
          <h2 className="text-[length:var(--font-size-section)] font-semibold tracking-wider uppercase text-slate-700">
            {title}
          </h2>
        </div>
      );
    }
    if (templateId === "modern" || templateId === "modern-two-column") {
      return (
        <div className="border-b border-slate-200 pb-0.5 mb-1 mt-1.5 flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: accent.primary }} />
          <h2 className="text-[length:var(--font-size-section)] font-bold tracking-wider uppercase text-slate-900">
            {title}
          </h2>
        </div>
      );
    }
    if (templateId === "vivid" || templateId === "vivid-single") {
      return (
        <div className="border-b-2 pb-0.5 mb-1 mt-1.5" style={{ borderColor: accent.primary }}>
          <h2 className="text-[length:var(--font-size-section)] font-bold tracking-wide uppercase" style={{ color: accent.primary }}>
            {title}
          </h2>
        </div>
      );
    }
    if (templateId === "deedy" || templateId === "modern-deedy") {
      return (
        <div className="border-b border-slate-300 pb-0.5 mb-1 mt-1.5">
          <h2 className="text-[length:var(--font-size-section)] font-bold tracking-widest uppercase text-slate-800">
            {title}
          </h2>
        </div>
      );
    }
    // Swiss Default
    return (
      <div className="border-b-2 pb-0.5 mb-1 mt-1.5" style={{ borderColor: accent.primary }}>
        <h2 className="text-[length:var(--font-size-section)] font-extrabold tracking-widest uppercase text-slate-900">
          {title}
        </h2>
      </div>
    );
  };

  // -------------------------------------------------------------
  // Content Sections
  // -------------------------------------------------------------
  const EducationSection = () => {
    if (!education.length) return null;
    return (
      <section style={{ marginBottom: sectionGap }}>
        <SectionHeading title="Education" />
        <div style={{ display: "flex", flexDirection: "column", gap: "0.2rem" }}>
          {education.map((edu: Education, idx: number) => (
            <div key={`${edu.institution}-${idx}`} className="flex justify-between items-baseline gap-2 text-left">
              <div className="truncate">
                <span className="font-bold text-[length:var(--font-size-body)] text-slate-900">{edu.degree}</span>
                <span className="text-slate-600 text-[length:var(--font-size-body)]"> — {edu.institution}</span>
                {edu.description && (
                  <span className="text-slate-500 font-medium text-[length:var(--font-size-meta)] ml-1">({edu.description})</span>
                )}
              </div>
              <div className="text-[length:var(--font-size-meta)] text-slate-500 whitespace-nowrap font-medium">{edu.years}</div>
            </div>
          ))}
        </div>
      </section>
    );
  };

  const SkillsSection = ({ compact = false }: { compact?: boolean }) => {
    const hasCategories = Object.keys(skillCategories).length > 0;
    if (!hasCategories && !technicalSkills.length) return null;

    return (
      <section style={{ marginBottom: sectionGap }}>
        <SectionHeading title="Technical Skills" />
        {hasCategories ? (
          <div className="space-y-0.5 text-left text-[length:var(--font-size-body)]">
            {Object.entries(skillCategories).map(([category, items]) => (
              <div key={category} className="leading-[var(--line-height)]">
                <span className="font-bold text-slate-800">{category}: </span>
                <span className="text-slate-700">{items.join(", ")}</span>
              </div>
            ))}
          </div>
        ) : templateId === "latex" || templateId === "clean" ? (
          <p className="text-[length:var(--font-size-body)] text-slate-700 leading-[var(--line-height)] text-left">
            {technicalSkills.join(" • ")}
          </p>
        ) : (
          <div className="flex flex-wrap gap-1 pt-0.5">
            {technicalSkills.map((skill: string, idx: number) => (
              <span
                key={`${skill}-${idx}`}
                className="inline-block px-1.5 py-0.5 rounded text-[length:var(--font-size-meta)] font-medium"
                style={{
                  backgroundColor: accent.light,
                  color: accent.primary,
                  border: `1px solid ${accent.primary}30`,
                }}
              >
                {skill}
              </span>
            ))}
          </div>
        )}
      </section>
    );
  };

  const WorkExperienceSection = () => {
    if (!workExperience.length) return null;
    return (
      <section style={{ marginBottom: sectionGap }}>
        <SectionHeading title="Work Experience" />
        <div style={{ display: "flex", flexDirection: "column", gap: itemGap }}>
          {workExperience.map((exp: WorkExperience, idx: number) => (
            <div key={`${exp.company}-${idx}`} className="text-left">
              <div className="flex justify-between items-baseline gap-2">
                <div className="font-bold text-[length:var(--font-size-body)] text-slate-900">
                  {exp.title}{" "}
                  <span className="font-semibold text-slate-700" style={{ color: accent.primary }}>
                    · {exp.company}
                  </span>
                  {exp.location && (
                    <span className="font-normal text-[length:var(--font-size-meta)] text-slate-500 ml-1.5">({exp.location})</span>
                  )}
                </div>
                <div className="text-[length:var(--font-size-meta)] text-slate-500 font-medium whitespace-nowrap">
                  {exp.years}
                </div>
              </div>
              {exp.responsibilities && exp.responsibilities.length > 0 && (
                <ul className="list-disc pl-3.5 mt-0.5 space-y-0.5 text-slate-700 text-[length:var(--font-size-body)] leading-[var(--line-height)]">
                  {exp.responsibilities.map((resp: string, rIdx: number) => (
                    <li key={rIdx}>{resp}</li>
                  ))}
                </ul>
              )}
            </div>
          ))}
        </div>
      </section>
    );
  };

  const ProjectsSection = () => {
    if (!projects.length) return null;
    return (
      <section style={{ marginBottom: sectionGap }}>
        <SectionHeading title="Projects" />
        <div style={{ display: "flex", flexDirection: "column", gap: itemGap }}>
          {projects.map((proj: Project, idx: number) => (
            <div key={`${proj.project_name}-${idx}`} className="text-left">
              <div className="flex justify-between items-baseline gap-2">
                <div className="font-bold text-[length:var(--font-size-body)] text-slate-900">
                  {proj.project_name}
                  {proj.project_technologies && proj.project_technologies.length > 0 && (
                    <span className="font-normal text-[length:var(--font-size-meta)] text-slate-500 ml-1.5">
                      ({proj.project_technologies.slice(0, 6).join(", ")})
                    </span>
                  )}
                </div>
                <div className="text-[length:var(--font-size-meta)] text-slate-500 font-medium whitespace-nowrap">
                  {proj.project_years}
                </div>
              </div>
              {proj.project_description && proj.project_description.length > 0 && (
                <ul className="list-disc pl-3.5 mt-0.5 space-y-0.5 text-slate-700 text-[length:var(--font-size-body)] leading-[var(--line-height)]">
                  {proj.project_description.map((desc: string, dIdx: number) => (
                    <li key={dIdx}>{desc}</li>
                  ))}
                </ul>
              )}
            </div>
          ))}
        </div>
      </section>
    );
  };

  const CustomSectionsRenderer = () => {
    if (!customSections || customSections.length === 0) return null;
    return (
      <>
        {customSections.map((sec: any, sIdx: number) => {
          const title = sec.title || (sec.key ? sec.key.replaceAll("_", " ") : "Additional");
          const items = sec.items || [];
          if (!items.length) return null;
          return (
            <section key={sIdx} style={{ marginBottom: sectionGap }}>
              <SectionHeading title={title} />
              <div style={{ display: "flex", flexDirection: "column", gap: itemGap }}>
                {items.map((item: any, iIdx: number) => (
                  <div key={iIdx} className="text-left">
                    <div className="flex justify-between items-baseline gap-2">
                      <div className="font-bold text-[length:var(--font-size-body)] text-slate-900">{item.title}</div>
                      {item.years && (
                        <div className="text-[length:var(--font-size-meta)] text-slate-500 font-medium whitespace-nowrap">
                          {item.years}
                        </div>
                      )}
                    </div>
                    {item.description && (
                      <p className="mt-0.5 text-slate-700 text-[length:var(--font-size-body)] leading-[var(--line-height)]">
                        {Array.isArray(item.description) ? item.description.join(" ") : item.description}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </section>
          );
        })}
      </>
    );
  };

  const SummarySection = () => {
    if (!summary) return null;
    return (
      <section style={{ marginBottom: sectionGap }}>
        <SectionHeading title="Profile Summary" />
        <p className="text-[length:var(--font-size-body)] text-slate-700 leading-[var(--line-height)] text-left">{summary}</p>
      </section>
    );
  };

  // -------------------------------------------------------------
  // Layout Variations (Single Column vs Two Column)
  // -------------------------------------------------------------
  const isTwoColumn =
    templateId === "swiss-two-column" ||
    templateId === "modern-two-column" ||
    templateId === "deedy" ||
    templateId === "modern-deedy";

  return (
    <>
    <style>{`@media print { @page { size: ${settings.pageSize === "LETTER" ? "letter" : "A4"} portrait; margin: 0; } }`}</style>
    <div className="w-full flex justify-center bg-slate-200/60 dark:bg-slate-950 p-2 sm:p-4 rounded-2xl overflow-x-auto print:p-0 print:bg-white print:overflow-visible">
      <article
        id="resume-canvas-paper"
        className={`resume-paper relative bg-white text-slate-900 box-border text-left shadow-2xl print:shadow-none ${fontFamilyClass}`}
        style={resumeStyle}
      >
        {/* Modern Top Accent Bar */}
        {(templateId === "modern" || templateId === "modern-two-column") && (
          <div
            className="absolute top-0 left-0 right-0 h-1.5"
            style={{ backgroundColor: accent.primary }}
          />
        )}

        <div
          ref={contentRef}
          style={{
            width: "100%",
            transform: `scale(${fitScale})`,
            transformOrigin: "top left",
          }}
        >
        {/* ================= HEADER ================= */}
        {templateId === "latex" ? (
          <header className="text-center pb-2 mb-1.5 border-b border-slate-900" style={{ fontFamily: headerFont }}>
            <h1 className="text-[length:var(--font-size-header)] font-serif font-bold tracking-wider text-slate-950 uppercase">
              {personalInfo.name}
            </h1>
            {personalInfo.title && (
              <p className="text-[length:var(--font-size-body)] text-slate-700 italic mt-0.5">{personalInfo.title}</p>
            )}
            <div className="mt-1">
              <ContactInfo centered={true} />
            </div>
          </header>
        ) : (
          <header className="pb-2 mb-1.5 border-b border-slate-200" style={{ fontFamily: headerFont }}>
            <div className="flex flex-wrap justify-between items-baseline gap-2">
              <div>
                <h1 className="text-[length:var(--font-size-header)] font-extrabold tracking-tight text-slate-900">
                  {personalInfo.name}
                </h1>
                {personalInfo.title && (
                  <p className="text-[length:var(--font-size-body)] font-semibold mt-0.5" style={{ color: accent.primary }}>
                    {personalInfo.title}
                  </p>
                )}
              </div>
            </div>
            <div className="mt-1">
              <ContactInfo icons={settings.showContactIcons} />
            </div>
          </header>
        )}

        {/* ================= BODY ================= */}
        {isTwoColumn ? (
          // Two-column Layout (66% Main / 34% Sidebar)
          <div className="grid grid-cols-[1fr_195px] gap-4 items-start">
            {/* Left Main Column */}
            <div>
              <SummarySection />
              <WorkExperienceSection />
              <ProjectsSection />
            </div>

            {/* Right Sidebar Column */}
            <div className="border-l border-slate-200 pl-3.5 space-y-2">
              <SkillsSection compact={true} />
              <EducationSection />
              <CustomSectionsRenderer />
              {languages.length > 0 && (
                <section style={{ marginBottom: sectionGap }}>
                  <SectionHeading title="Languages" />
                  <p className="text-[length:var(--font-size-body)] text-slate-700 leading-[var(--line-height)]">
                    {languages.join(", ")}
                  </p>
                </section>
              )}
              {certifications.length > 0 && (
                <section style={{ marginBottom: sectionGap }}>
                  <SectionHeading title="Certifications" />
                  <p className="text-[length:var(--font-size-body)] text-slate-700 leading-[var(--line-height)]">
                    {certifications.join(" • ")}
                  </p>
                </section>
              )}
              {awards.length > 0 && (
                <section style={{ marginBottom: sectionGap }}>
                  <SectionHeading title="Awards" />
                  <p className="text-[length:var(--font-size-body)] text-slate-700 leading-[var(--line-height)]">
                    {awards.join(" • ")}
                  </p>
                </section>
              )}
            </div>
          </div>
        ) : (
          // Single-column Layout (All sections in optimal ATS priority order)
          <div>
            <SummarySection />
            <EducationSection />
            <SkillsSection />
            <WorkExperienceSection />
            <ProjectsSection />
            <CustomSectionsRenderer />
            {(languages.length > 0 || certifications.length > 0 || awards.length > 0) && (
              <div className="grid grid-cols-2 gap-3 mt-1">
                {languages.length > 0 && (
                  <div>
                    <SectionHeading title="Languages" />
                    <p className="text-[length:var(--font-size-body)] text-slate-700 leading-[var(--line-height)]">
                      {languages.join(" • ")}
                    </p>
                  </div>
                )}
                {certifications.length > 0 && (
                  <div>
                    <SectionHeading title="Certifications" />
                    <p className="text-[length:var(--font-size-body)] text-slate-700 leading-[var(--line-height)]">
                      {certifications.join(" • ")}
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
        </div>
      </article>
    </div>
    </>
  );
}
