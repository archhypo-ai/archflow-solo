import { createRequire } from "node:module";

const args = process.argv.slice(2);
if (
  process.platform === "linux" &&
  args.includes("dev") &&
  process.env.WEBKIT_DISABLE_DMABUF_RENDERER === undefined
) {
  process.env.WEBKIT_DISABLE_DMABUF_RENDERER = "1";
}

const require = createRequire(import.meta.url);
const { run } = require("@tauri-apps/cli");

try {
  await run(args, `npm run ${process.env.npm_lifecycle_event ?? "tauri"}`);
} catch (error) {
  console.error(error instanceof Error ? error.message : error);
  process.exitCode = 1;
}
