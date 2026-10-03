import { buildSalesReport, LAUNCH_DATE } from "../lib/bill";
import { readLeads, readStudio, writeReport } from "../lib/store";

const origin = (process.env.APP_ORIGIN || "http://localhost:3000").replace(/\/$/, "");
const report = buildSalesReport(readStudio().tutors, readLeads(), origin, LAUNCH_DATE);
writeReport("sales-report.json", report);
console.log(report.reason);
if (report.kill) process.exitCode = 2;
