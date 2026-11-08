import { CustomSection, ResumeSchema } from "@/types/resume";
import { TemplateSettings } from "./template-settings";

function escapeLatex(value: unknown): string {
  const escapedCharacters: Record<string, string> = {
    "\\": "\\textbackslash{}",
    "{": "\\{",
    "}": "\\}",
    "%": "\\%",
    "$": "\\$",
    "&": "\\&",
    "#": "\\#",
    "_": "\\_",
    "^": "\\textasciicircum{}",
    "~": "\\textasciitilde{}",
  };
  return String(value ?? "").replace(/[\\{}%$&#_^~]/g, (character) => escapedCharacters[character]);
}

function normalizeExternalUrl(value: string): string {
  const trimmed = value.trim();
  if (/^https?:\/\//i.test(trimmed)) return trimmed;
  return `https://${trimmed.replace(/^\/\//, "")}`;
}

function formatSocialLinkLabel(value: string): string {
  const key = value.toLowerCase().replace(/_url$/, "").replace(/[-_]+/g, " ").trim();
  const knownLabels: Record<string, string> = {
    x: "X",
    dev: "DEV",
    devto: "DEV",
    github: "GitHub",
    linkedin: "LinkedIn",
    medium: "Medium",
    stackoverflow: "Stack Overflow",
    "stack overflow": "Stack Overflow",
  };
  return knownLabels[key] ?? key.replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function asTextList(value: unknown): string[] {
  if (typeof value === "string") {
    return value.split(",").map((item) => item.trim()).filter(Boolean);
  }
  return Array.isArray(value)
    ? value.filter((item): item is string => typeof item === "string" && item.trim().length > 0)
    : [];
}

function asSkillList(value: unknown): string[] {
  const direct = asTextList(value);
  if (direct.length || !value || Array.isArray(value) || typeof value !== "object") {
    return direct;
  }
  return Object.values(value).flatMap(asTextList);
}

function renderList(items: string[]): string {
  if (!items.length) return "";
  return [
    "\\begin{itemize}[leftmargin=1.2em,itemsep=0pt,topsep=2pt,parsep=0pt]",
    ...items.map((item) => `  \\item ${escapeLatex(item)}`),
    "\\end{itemize}",
  ].join("\n");
}

function renderSection(title: string, content: string): string {
  if (!content.trim()) return "";
  return [
    `\\resumeSection{${escapeLatex(title)}}`,
    content,
    "\\par",
  ].join("\n");
}

function getCustomSectionEntries(
  sections: ResumeSchema["customSections"],
): Array<[string, CustomSection]> {
  if (Array.isArray(sections)) {
    return sections.map((section, index) => [
      section.key || `custom_${index + 1}`,
      section,
    ]);
  }
  return sections && typeof sections === "object"
    ? Object.entries(sections)
    : [];
}

function formatCustomSectionTitle(key: string): string {
  return key
    .split(/[_\s]+/)
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

export function generateLatexResume(
  resume: ResumeSchema,
  settings: TemplateSettings,
): string {
  const personal = resume.personalInfo;
  const additional = Array.isArray(resume.additional)
    ? resume.additional[0] ?? {}
    : resume.additional ?? {};
  const technicalSkills = asSkillList(additional.technicalSkills ?? resume.skills);
  const languages = asTextList(additional.languages);
  const certifications = asTextList(additional.certificationsTraining);
  const awards = asTextList(additional.awards);

  const profileLinks = [
    { label: "LinkedIn", url: personal.linkedin_url },
    { label: "GitHub", url: personal.github_url },
    { label: "Twitter / X", url: personal.twitter_url },
    { label: "Portfolio", url: personal.portfolio_url },
    ...Object.entries(personal.other_links ?? {}).map(([label, url]) => ({
      label: formatSocialLinkLabel(label),
      url,
    })),
  ].filter(
    (link): link is { label: string; url: string } =>
      typeof link.url === "string" && link.url.trim().length > 0,
  );
  const contact = [
    personal.email,
    personal.phone,
    personal.location,
  ].filter((value): value is string => typeof value === "string" && value.trim().length > 0)
    .map(escapeLatex)
    .concat(
      profileLinks.map(
        ({ label, url }) =>
          `\\href{${escapeLatex(normalizeExternalUrl(url))}}{${escapeLatex(label)}}`,
      ),
    )
    .join(" \\textbar{} ");

  const experience = (resume.workExperience ?? []).map((item) => [
    `\\resumeEntry{${escapeLatex(item.title)}}{${escapeLatex(item.years)}}`,
    `\\textit{${escapeLatex(item.company)}${item.location ? `, ${escapeLatex(item.location)}` : ""}}`,
    renderList(item.responsibilities ?? []),
  ].filter(Boolean).join("\n")).join("\n");

  const education = (resume.education ?? []).map((item) => [
    `\\resumeEntry{${escapeLatex(item.degree)}}{${escapeLatex(item.years)}}`,
    escapeLatex(item.institution),
    item.description ? `\\\\\n${escapeLatex(item.description)}` : "",
  ].filter(Boolean).join("\n")).join("\n");

  const projects = (resume.projects ?? []).map((item) => [
    `\\resumeEntry{${escapeLatex(item.project_name)}}{${escapeLatex(item.project_years)}}`,
    item.project_technologies?.length
      ? `\\textit{${escapeLatex(item.project_technologies.join(", "))}}`
      : "",
    item.project_url ? `\\\\\n${escapeLatex(item.project_url)}` : "",
    item.project_github_url ? `\\\\\n${escapeLatex(item.project_github_url)}` : "",
    renderList(item.project_description ?? []),
  ].filter(Boolean).join("\n")).join("\n");

  const skills = technicalSkills.length
    ? escapeLatex(technicalSkills.join(" \\textbullet{} "))
    : "";
  const customSections = getCustomSectionEntries(resume.customSections).map(([key, section]) => {
    const title = section.title
      ?? section.key?.replaceAll("_", " ")
      ?? (Array.isArray(resume.customSections) ? "Additional" : formatCustomSectionTitle(key));
    const sectionType = section.sectionType
      ?? (section.text !== undefined
        ? "text"
        : section.strings
          ? "stringList"
          : section.items
            ? "itemList"
            : undefined);
    if (sectionType === "text") {
      return renderSection(title, escapeLatex(section.text));
    }
    if (sectionType === "stringList") {
      return renderSection(
        title,
        escapeLatex((section.strings ?? []).join(" \\textbullet{} ")),
      );
    }
    const items = (section.items ?? []).map((item) => [
      `\\resumeEntry{${escapeLatex(item.title)}}{${escapeLatex(item.years)}}`,
      item.subtitle || item.location
        ? `\\textit{${escapeLatex([item.subtitle, item.location].filter(Boolean).join(", "))}}`
        : "",
      Array.isArray(item.description)
        ? renderList(item.description)
        : escapeLatex(item.description),
    ].filter(Boolean).join("\n")).join("\n");
    return renderSection(title, items);
  }).filter(Boolean);

  const sections = [
    renderSection("Profile Summary", escapeLatex(resume.summary)),
    renderSection("Education", education),
    renderSection("Technical Skills", skills),
    renderSection("Work Experience", experience),
    renderSection("Projects", projects),
    renderSection("Languages", escapeLatex(languages.join(" \\textbullet{} "))),
    renderSection("Certifications", escapeLatex(certifications.join(" \\textbullet{} "))),
    renderSection("Awards", escapeLatex(awards.join(" \\textbullet{} "))),
    ...customSections,
  ].filter(Boolean);

  return [
    "% Generated from the tailored structured resume data.",
    "% Compile with pdfLaTeX: pdflatex tailored-resume.tex",
    "\\documentclass[10pt]{article}",
    "\\usepackage[T1]{fontenc}",
    "\\usepackage[utf8]{inputenc}",
    "\\usepackage{lmodern}",
    "\\usepackage{geometry}",
    "\\usepackage{enumitem}",
    "\\usepackage[hidelinks]{hyperref}",
    "\\usepackage{xcolor}",
    "\\usepackage{microtype}",
    `\\geometry{${settings.pageSize === "LETTER" ? "letterpaper" : "a4paper"},margin=36pt}`,
    "\\pagestyle{empty}",
    "\\setlength{\\parindent}{0pt}",
    "\\setlength{\\parskip}{0pt}",
    "\\definecolor{resumeheading}{HTML}{1F2937}",
    "\\newcommand{\\resumeSection}[1]{%",
    "  \\vspace{3pt}\\noindent{\\small\\scshape\\color{resumeheading}#1}\\par",
    "  \\vspace{1pt}\\hrule\\vspace{2pt}",
    "}",
    "\\newcommand{\\resumeEntry}[2]{%",
    "  \\textbf{#1}\\hfill{\\small #2}\\par",
    "}",
    "\\begin{document}",
    "\\fontsize{10pt}{12.5pt}\\selectfont",
    "\\begin{center}",
    `  {\\fontsize{22pt}{25pt}\\selectfont\\scshape ${escapeLatex(personal.name)}}\\\\`,
    personal.title ? `  {\\small ${escapeLatex(personal.title)}}\\\\` : "",
    `  {\\small ${contact}}`,
    "\\end{center}",
    "\\vspace{-4pt}\\hrule\\vspace{3pt}",
    ...sections,
    "\\end{document}",
  ].filter((line) => line !== "").join("\n") + "\n";
}
