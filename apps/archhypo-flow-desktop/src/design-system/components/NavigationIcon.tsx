import { IconArchive, IconFolderPlus, IconLayoutSidebarLeftCollapse,
  IconLayoutSidebarLeftExpand, IconPencilPlus, IconPuzzle, IconStack2 } from "@tabler/icons-react";

type NavigationSymbol = "left_panel_open" | "left_panel_close" | "edit_square" |
  "create_new_folder" | "inventory_2" | "stacks" | "extension";

const icons = {
  left_panel_open: IconLayoutSidebarLeftExpand,
  left_panel_close: IconLayoutSidebarLeftCollapse,
  edit_square: IconPencilPlus,
  create_new_folder: IconFolderPlus,
  inventory_2: IconArchive,
  stacks: IconStack2,
  extension: IconPuzzle,
} satisfies Record<NavigationSymbol, typeof IconArchive>;

export function NavigationIcon({ symbol }: { symbol: NavigationSymbol }) {
  const Icon = icons[symbol];
  return <Icon aria-hidden="true" />;
}
