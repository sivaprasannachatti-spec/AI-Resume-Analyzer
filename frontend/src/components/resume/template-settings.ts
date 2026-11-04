export type ResumeTemplateId =
  | "swiss-single"
  | "swiss-two-column"
  | "modern"
  | "modern-two-column"
  | "latex"
  | "clean"
  | "vivid"
  | "vivid-single"
  | "modern-deedy"
  | "deedy";

export interface ResumeTemplateSetting {
  id: ResumeTemplateId;
  name: string;
  description: string;
  category: "ATS" | "Modern" | "Editorial";
  accent: string;
}

export type PageSize = "A4" | "LETTER";
export type AccentColor = "blue" | "green" | "orange" | "red";
export type SpacingLevel = 1 | 2 | 3 | 4 | 5;
export type FontFamily = "serif" | "sans-serif" | "mono";

export interface TemplateSettings {
  template: ResumeTemplateId;
  pageSize: PageSize;
  margins: { top: number; bottom: number; left: number; right: number };
  spacing: { section: SpacingLevel; item: SpacingLevel; lineHeight: SpacingLevel };
  fontSize: { base: SpacingLevel; headerScale: SpacingLevel; headerFont: FontFamily; bodyFont: FontFamily };
  compactMode: boolean;
  showContactIcons: boolean;
  accentColor: AccentColor;
}

export const DEFAULT_TEMPLATE_SETTINGS: TemplateSettings = {
  template: "swiss-single",
  pageSize: "A4",
  margins: { top: 10, bottom: 10, left: 10, right: 10 },
  spacing: { section: 3, item: 2, lineHeight: 3 },
  fontSize: { base: 3, headerScale: 3, headerFont: "serif", bodyFont: "sans-serif" },
  compactMode: false,
  showContactIcons: false,
  accentColor: "blue",
};

export const SECTION_SPACING_MAP: Record<SpacingLevel, string> = {
  1: "0.375rem", 2: "0.625rem", 3: "1rem", 4: "1.25rem", 5: "1.5rem",
};
export const ITEM_SPACING_MAP: Record<SpacingLevel, string> = {
  1: "0.125rem", 2: "0.25rem", 3: "0.5rem", 4: "0.75rem", 5: "1rem",
};
export const LINE_HEIGHT_MAP: Record<SpacingLevel, number> = {
  1: 1.15, 2: 1.25, 3: 1.35, 4: 1.45, 5: 1.55,
};
export const FONT_SIZE_MAP: Record<SpacingLevel, string> = {
  1: "11px", 2: "12px", 3: "14px", 4: "15px", 5: "16px",
};
export const HEADER_SCALE_MAP: Record<SpacingLevel, number> = {
  1: 1.5, 2: 1.75, 3: 2, 4: 2.25, 5: 2.5,
};
export const ACCENT_COLOR_MAP: Record<AccentColor, { primary: string; light: string }> = {
  blue: { primary: "#1d4ed8", light: "#dbeafe" },
  green: { primary: "#15803d", light: "#dcfce7" },
  orange: { primary: "#ea580c", light: "#fed7aa" },
  red: { primary: "#dc2626", light: "#fee2e2" },
};

export function settingsToCssVars(settings: TemplateSettings): React.CSSProperties {
  const compact = settings.compactMode ? 0.6 : 1;
  const accent = ACCENT_COLOR_MAP[settings.accentColor];
  const pageWidth = settings.pageSize === "LETTER" ? "8.5in" : "210mm";
  const pageHeight = settings.pageSize === "LETTER" ? "11in" : "297mm";
  const baseFontSize = Number.parseFloat(FONT_SIZE_MAP[settings.fontSize.base]);
  const bodyFont = settings.fontSize.bodyFont;
  const headerFont = settings.fontSize.headerFont;
  return {
    "--page-width": pageWidth,
    "--page-height": pageHeight,
    "--section-gap": `calc(${SECTION_SPACING_MAP[settings.spacing.section]} * ${compact})`,
    "--item-gap": `calc(${ITEM_SPACING_MAP[settings.spacing.item]} * ${compact})`,
    "--line-height": LINE_HEIGHT_MAP[settings.spacing.lineHeight] * (settings.compactMode ? 0.92 : 1),
    "--font-size-base": `${baseFontSize}px`,
    "--font-size-body": `${baseFontSize * 0.75}px`,
    "--font-size-small": `${baseFontSize * 0.68}px`,
    "--font-size-meta": `${baseFontSize * 0.7}px`,
    "--font-size-section": `${baseFontSize * 0.75}px`,
    "--font-size-header": `${baseFontSize * HEADER_SCALE_MAP[settings.fontSize.headerScale] * 0.7}px`,
    "--header-font": headerFont === "serif" ? "Georgia, serif" : headerFont === "mono" ? "ui-monospace, monospace" : "Arial, sans-serif",
    "--body-font": bodyFont === "serif" ? "Georgia, serif" : bodyFont === "mono" ? "ui-monospace, monospace" : "Arial, sans-serif",
    "--resume-page-size": settings.pageSize === "LETTER" ? "letter portrait" : "A4 portrait",
    "--margin-top": `${settings.margins.top}mm`,
    "--margin-bottom": `${settings.margins.bottom}mm`,
    "--margin-left": `${settings.margins.left}mm`,
    "--margin-right": `${settings.margins.right}mm`,
    "--resume-accent-primary": accent.primary,
    "--resume-accent-light": accent.light,
  } as React.CSSProperties;
}

export const TEMPLATE_SETTINGS: ResumeTemplateSetting[] = [
  { id: "swiss-single", name: "Swiss Single", description: "Precise single-column hierarchy", category: "ATS", accent: "#5664d9" },
  { id: "swiss-two-column", name: "Swiss Two Column", description: "Structured with compact sidebar", category: "ATS", accent: "#2a9d8f" },
  { id: "modern", name: "Modern", description: "Balanced contemporary layout", category: "Modern", accent: "#6875e5" },
  { id: "modern-two-column", name: "Modern Two Column", description: "Modern layout with quick facts", category: "Modern", accent: "#5ec4b6" },
  { id: "latex", name: "LaTeX", description: "Academic, compact, and formal", category: "ATS", accent: "#334155" },
  { id: "clean", name: "Clean", description: "Quiet and highly readable", category: "ATS", accent: "#64748b" },
  { id: "vivid", name: "Vivid", description: "Confident color-led hierarchy", category: "Editorial", accent: "#c58b32" },
  { id: "vivid-single", name: "Vivid Single", description: "Colorful single-column format", category: "Editorial", accent: "#e07a5f" },
  { id: "modern-deedy", name: "Modern Deedy", description: "Dense engineering portfolio style", category: "Modern", accent: "#7c83fd" },
  { id: "deedy", name: "Deedy", description: "Classic two-column technical CV", category: "ATS", accent: "#475569" },
];

export const DEFAULT_TEMPLATE_ID: ResumeTemplateId = "swiss-single";

export function isResumeTemplateId(value: string | undefined): value is ResumeTemplateId {
  return TEMPLATE_SETTINGS.some((template) => template.id === value);
}
