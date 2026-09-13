import { useCallback, useState } from "react";

export function useSidebarAccountMenu() {
  const [open, setOpen] = useState(false);
  const setMenuOpen = useCallback((nextOpen: boolean) => setOpen(nextOpen), []);
  const toggle = useCallback(() => setOpen((current) => !current), []);
  const close = useCallback(() => setOpen(false), []);

  return { open, setMenuOpen, toggle, close };
}
