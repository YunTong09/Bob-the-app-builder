import { spawnSync } from "node:child_process";
import { homedir } from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = fileURLToPath(new URL("../", import.meta.url));
const windows = process.platform === "win32";
const interpreter = (directory) => path.join(directory, windows ? "python.exe" : "bin/python");
const candidates = [
  ...(process.env.PYTHON ? [[process.env.PYTHON, []]] : []),
  [path.join(root, "backend", ".venv", windows ? "Scripts/python.exe" : "bin/python"), []],
  ...(process.env.CONDA_PREFIX ? [[interpreter(process.env.CONDA_PREFIX), []]] : []),
  ...(windows ? [[interpreter(path.join(homedir(), "miniconda3")), []], ["py", ["-3"]]] : []),
  ["python3", []],
  ["python", []],
];

for (const [command, prefix] of candidates) {
  const probe = spawnSync(command, [...prefix, "--version"], {
    encoding: "utf8", windowsHide: true, timeout: 10_000,
  });
  const version = `${probe.stdout ?? ""} ${probe.stderr ?? ""}`.match(/Python (\d+)\.(\d+)/);
  if (probe.status !== 0 || !version || Number(version[1]) !== 3 || Number(version[2]) < 11) continue;

  console.log(`Checking backend syntax with ${command}`);
  const result = spawnSync(command, [...prefix, "-m", "compileall", "-q", "-x", "[.]venv|__pycache__", "backend"], {
    cwd: root, stdio: "inherit", windowsHide: true,
  });
  if (result.error) console.error(`Could not run the backend syntax check: ${result.error.message}`);
  process.exit(result.status ?? 1);
}

console.error("Python 3.11+ was not found. Install Python, create backend/.venv, or set PYTHON to your Python executable's full path.");
process.exit(1);
