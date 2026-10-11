import { spawn } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const appDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const repoRoot = path.resolve(appDir, "../..");
const backendDir = path.join(repoRoot, "libs", "archhypo-flow-agent");
const apiUrl = "http://127.0.0.1:8765";
const healthUrl = `${apiUrl.replace(/\/$/, "")}/health`;
const uv = process.env.ARCHHYPO_UV_BIN ?? process.env.UV_BIN ?? "uv";
const npm = process.platform === "win32" ? "npm.cmd" : "npm";
const children = [];
let stopping = false;

async function isBackendReady() {
  try {
    const response = await fetch(healthUrl, { signal: AbortSignal.timeout(700) });
    return response.ok;
  } catch {
    return false;
  }
}

function start(command, args, cwd) {
  const child = spawn(command, args, {
    cwd,
    env: { ...process.env, PYTHONUNBUFFERED: "1" },
    stdio: "inherit",
  });
  children.push(child);
  child.on("error", (error) => {
    console.error(`Could not start ${command}:`, error.message);
    stop("SIGTERM", 1);
  });
  child.on("exit", (code, signal) => {
    if (!stopping) {
      console.error(`${command} exited${signal ? ` with ${signal}` : ` (${code})`}.`);
      stop("SIGTERM", code ?? 1);
    }
  });
  return child;
}

function stop(signal, exitCode = 0) {
  if (stopping) return;
  stopping = true;
  process.exitCode = exitCode;
  for (const child of children) {
    if (child.exitCode === null && !child.killed) child.kill(signal);
  }
}

async function waitForBackend(child) {
  for (let attempt = 0; attempt < 100; attempt += 1) {
    if (await isBackendReady()) return;
    if (stopping || child.exitCode !== null) {
      throw new Error("The local chat API stopped before becoming ready.");
    }
    await new Promise((resolve) => setTimeout(resolve, 200));
  }
  throw new Error(`The local chat API did not become ready at ${healthUrl}.`);
}

process.on("SIGINT", () => stop("SIGINT", 130));
process.on("SIGTERM", () => stop("SIGTERM", 143));

try {
  if (!(await isBackendReady())) {
    const backend = start(
      uv,
      [
        "run",
        "--extra",
        "research",
        "--project",
        backendDir,
        "python",
        "-m",
        "uvicorn",
        "archhypo_flow_agent.backend.app:app",
        "--host",
        "127.0.0.1",
        "--port",
        new URL(apiUrl).port || "8765",
      ],
      backendDir,
    );
    await waitForBackend(backend);
  }

  start(npm, ["run", "dev"], appDir);
} catch (error) {
  console.error(error instanceof Error ? error.message : error);
  stop("SIGTERM", 1);
}
