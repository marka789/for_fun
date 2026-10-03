import { CopyButton } from "@/components/copy-button";
import { canManage } from "@/lib/auth";
import { buildSalesReport, digitsOnly, salesPost } from "@/lib/bill";
import { readLeads, readStudio } from "@/lib/store";
import { headers } from "next/headers";
import { redirect } from "next/navigation";

export const dynamic = "force-dynamic";
export const metadata = { robots: { index: false, follow: false } };

async function origin() {
  if (process.env.APP_ORIGIN) return process.env.APP_ORIGIN.replace(/\/$/, "");
  const headerList = await headers();
  const host = headerList.get("x-forwarded-host") || headerList.get("host") || "localhost:3000";
  const proto = headerList.get("x-forwarded-proto") || "http";
  return `${proto}://${host}`;
}

export default async function SellPage() {
  if (!(await canManage())) redirect("/studio");
  const base = await origin();
  const report = buildSalesReport(readStudio().tutors, readLeads(), base);
  const post = salesPost(base);

  return (
    <main className="stack">
      <section className="card">
        <p className="kicker">賣</p>
        <h1>{report.paidTutors} 個付費老師</h1>
        <p>{report.reason}</p>
        <p className="fine">開張日 {report.launchDate}，第 {report.daysSinceLaunch} 日。5 個付費老師之前唔好再花錢。</p>
        <CopyButton value={post} label="複製貼文" />
        <pre className="notice">{post}</pre>
      </section>
      <section className="card">
        <h2>未開頁嘅查詢</h2>
        {report.leadsWaiting.length === 0 ? <p className="muted">未有人留電話。</p> : null}
        <div className="stack">
          {report.leadsWaiting.map((lead) => (
            <p key={lead.id}>
              {lead.name} · {lead.subject || "未寫科目"} · {digitsOnly(lead.phone)}
            </p>
          ))}
        </div>
      </section>
    </main>
  );
}
