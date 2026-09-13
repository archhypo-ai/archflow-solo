import { useCallback, useState } from "react";

export function useSidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const toggle = useCallback(() => setCollapsed((current) => !current), []);

  return { collapsed, setCollapsed, toggle };
}
