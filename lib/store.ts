import { mkdirSync, readFileSync, renameSync, writeFileSync, existsSync } from "fs";
import path from "path";
import type { Lead, Studio } from "./types";

const dataDir = path.join(process.cwd(), "data");
const studioPath = path.join(dataDir, "studio.json");
const seedPath = path.join(dataDir, "seed.json");
const leadsPath = path.join(dataDir, "leads.json");

function writeJson(file: string, value: unknown) {
  mkdirSync(path.dirname(file), { recursive: true });
  const tmp = `${file}.tmp`;
  writeFileSync(tmp, JSON.stringify(value, null, 2));
  renameSync(tmp, file);
}

export function readStudio(): Studio {
  if (!existsSync(studioPath)) {
    const seed = JSON.parse(readFileSync(seedPath, "utf8")) as Studio;
    writeJson(studioPath, seed);
    return seed;
  }
  return JSON.parse(readFileSync(studioPath, "utf8")) as Studio;
}

export function writeStudio(studio: Studio) {
  writeJson(studioPath, studio);
}

export function readLeads(): Lead[] {
  if (!existsSync(leadsPath)) return [];
  return JSON.parse(readFileSync(leadsPath, "utf8")) as Lead[];
}

export function writeLeads(leads: Lead[]) {
  writeJson(leadsPath, leads);
}

export function writeReport(name: string, value: unknown) {
  writeJson(path.join(dataDir, name), value);
}
