import { ResumeSchema } from "@/types/resume";
import { DEFAULT_TEMPLATE_SETTINGS, TemplateSettings } from "./template-settings";
import { ResumeBase } from "./resume-base";

export default function ResumeComponent({
  resumeData,
  templateSettings,
}: {
  resumeData: ResumeSchema;
  templateSettings?: TemplateSettings;
}) {
  const mergedSettings: TemplateSettings = {
    ...DEFAULT_TEMPLATE_SETTINGS,
    ...templateSettings,
  };

  return (
    <ResumeBase
      resume={resumeData}
      settings={mergedSettings}
    />
  );
}
