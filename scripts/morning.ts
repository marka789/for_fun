import { buildDigest } from "../lib/bill";
import { readStudio, writeReport } from "../lib/store";
import { writeFileSync } from "fs";
import path from "path";

const origin = (process.env.APP_ORIGIN || "http://localhost:3000").replace(/\/$/, "");
const digest = buildDigest(readStudio().tutors, origin);
writeReport("digest.json", digest);
writeFileSync(path.join(process.cwd(), "data", "digest.txt"), `${digest.text}\n`);
console.log(digest.text);
if (digest.quiet) process.exitCode = 0;
