import { spawn } from "node:child_process";
import { buildDigest } from "../lib/bill";
import { readStudio, writeReport } from "../lib/store";
import { mkdirSync, writeFileSync } from "fs";
import path from "path";

function writeDigest() {
  const origin = (process.env.APP_ORIGIN || "http://localhost:3000").replace(/\/$/, "");
  const digest = buildDigest(readStudio().tutors, origin);
  mkdirSync(path.join(process.cwd(), "data"), { recursive: true });
  writeReport("digest.json", digest);
  writeFileSync(path.join(process.cwd(), "data", "digest.txt"), `${digest.text}\n`);
}

writeDigest();
const timer = setInterval(writeDigest, 60 * 60 * 1000);
timer.unref();

const child = spawn("npx", ["next", "start", ...process.argv.slice(2)], { stdio: "inherit" });
child.on("exit", (code) => process.exit(code ?? 0));
