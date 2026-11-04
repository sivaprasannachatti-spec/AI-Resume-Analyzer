import { ResumeSchema } from "@/types/resume";
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

  const contact = [
    personal.email,
    personal.phone,
    personal.location,
    personal.linkedin_url,
    personal.github_url,
  ].filter((value): value is string => typeof value === "string" && value.trim().length > 0)
    .map(escapeLatex)
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
  const customSections = (resume.customSections ?? []).map((section) => {
    const title = section.title ?? section.key?.replaceAll("_", " ") ?? "Additional";
    const items = (section.items ?? []).map((item) => [
      `\\resumeEntry{${escapeLatex(item.title)}}{${escapeLatex(item.years)}}`,
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
    "\\usepackage{adjustbox}",
    `\\geometry{${settings.pageSize === "LETTER" ? "letterpaper" : "a4paper"},margin=36pt}`,
    "\\pagestyle{empty}",
    "\\setlength{\\parindent}{0pt}",
    "\\setlength{\\parskip}{2pt}",
    "\\renewcommand{\\baselinestretch}{1.25}",
    "\\definecolor{resumeheading}{HTML}{1F2937}",
    "\\newcommand{\\resumeSection}[1]{%",
    "  \\vspace{5pt}\\noindent{\\small\\scshape\\color{resumeheading}#1}\\par",
    "  \\vspace{1pt}\\hrule\\vspace{3pt}",
    "}",
    "\\newcommand{\\resumeEntry}[2]{%",
    "  \\textbf{#1}\\hfill{\\small #2}\\par",
    "}",
    "\\begin{document}",
    "\\begin{adjustbox}{max totalsize={\\textwidth}{\\textheight}}",
    "\\begin{minipage}{\\textwidth}",
    "\\fontsize{10pt}{12.5pt}\\selectfont",
    "\\begin{center}",
    `  {\\fontsize{22pt}{25pt}\\selectfont\\scshape ${escapeLatex(personal.name)}}\\\\`,
    personal.title ? `  {\\small ${escapeLatex(personal.title)}}\\\\` : "",
    `  {\\small ${contact}}`,
    "\\end{center}",
    "\\vspace{-4pt}\\hrule\\vspace{5pt}",
    ...sections,
    "\\end{minipage}",
    "\\end{adjustbox}",
    "\\end{document}",
  ].filter((line) => line !== "").join("\n") + "\n";
}
