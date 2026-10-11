import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import path from "node:path";

const appDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const repoRoot = path.resolve(appDir, "../..");
const agentDir = path.join(repoRoot, "libs", "archwise-agent");
const uv = process.env.ARCHWISE_UV_BIN ?? process.env.UV_BIN ?? "uv";

const child = spawn(
  uv,
  ["run", "python", "-m", "archwise_agent.backend.server"],
  {
    cwd: agentDir,
    env: { ...process.env, PYTHONUNBUFFERED: "1" },
    stdio: "inherit",
  },
);

let stopping = false;
const stop = (signal) => {
  if (stopping || child.killed) return;
  stopping = true;
  child.kill(signal);
};

process.on("SIGINT", () => stop("SIGINT"));
process.on("SIGTERM", () => stop("SIGTERM"));
child.on("error", (error) => {
  console.error("Could not start the ArchWISE backend:", error.message);
  process.exitCode = 1;
});
child.on("exit", (code, signal) => {
  if (signal && !stopping) process.kill(process.pid, signal);
  else if (!stopping) process.exit(code ?? 1);
});
