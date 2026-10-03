import { buildOutbox, hongKongMonth } from "../lib/bill";
import { readStudio, writeReport } from "../lib/store";

const origin = (process.env.APP_ORIGIN || "http://localhost:3000").replace(/\/$/, "");
const month = process.argv[2] || hongKongMonth();
const outbox = buildOutbox(readStudio().tutors, month, origin);
writeReport("outbox.json", outbox);
console.log(`${outbox.items.length} reminders, ${outbox.totalUnpaid} HKD unpaid, written to data/outbox.json`);
