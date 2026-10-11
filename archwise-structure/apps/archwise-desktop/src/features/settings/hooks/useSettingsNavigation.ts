import { useState } from "react";
import type { SettingsSectionId } from "../types";

export function useSettingsNavigation() {
  const [activeSection, setActiveSection] =
    useState<SettingsSectionId>("general");

  return { activeSection, setActiveSection };
}
