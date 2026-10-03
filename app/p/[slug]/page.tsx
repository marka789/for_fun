import { notFound } from "next/navigation";
import { CopyButton } from "@/components/copy-button";
import { formatDate, formatMoney, formatMonth, groupByParent, hongKongMonth, monthLessons, shiftMonth, unpaidTotal, validMonth } from "@/lib/bill";
import { readStudio } from "@/lib/store";
import { headers } from "next/headers";

export const dynamic = "force-dynamic";

async function origin() {
  if (process.env.APP_ORIGIN) return process.env.APP_ORIGIN.replace(/\/$/, "");
  const headerList = await headers();
  const host = headerList.get("x-forwarded-host") || headerList.get("host") || "localhost:3000";
  const proto = headerList.get("x-forwarded-proto") || "http";
  return `${proto}://${host}`;
}

export default async function ParentPage({
  params,
  searchParams,
}: {
  params: Promise<{ slug: string }>;
  searchParams: Promise<{ month?: string }>;
}) {
  const { slug } = await params;
  const query = await searchParams;
  const tutor = readStudio().tutors.find((item) => item.slug === slug);
  if (!tutor) notFound();

  const month = query.month && validMonth(query.month) ? query.month : hongKongMonth();
  const lessons = monthLessons(tutor, month);
  const owed = unpaidTotal(lessons);
  const pageUrl = `${await origin()}/p/${tutor.slug}?month=${month}`;

  return (
    <main className="card">
      {tutor.plan === "demo" ? <p className="notice">示範頁。轉數快號碼是假的，唔好轉帳。</p> : null}
      <div className="month-nav">
        <a href={`/p/${tutor.slug}?month=${shiftMonth(month, -1)}`}>上個月</a>
        <strong>{formatMonth(month)}</strong>
        <a href={`/p/${tutor.slug}?month=${shiftMonth(month, 1)}`}>下個月</a>
      </div>
      <div className="bill-head">
        <div>
          <p className="kicker">{tutor.name} · {tutor.subject}</p>
          <p className="money">{formatMoney(owed)}</p>
          <p className="muted">{owed === 0 ? "這個月沒有未付堂數。" : "未付"}</p>
        </div>
        <div className={owed === 0 ? "stamp paid" : "stamp"}>{owed === 0 ? "已付" : "未付"}</div>
      </div>
      {lessons.length === 0 ? <p>這個月未有堂數。</p> : null}
      {groupByParent(lessons).map((bill) => (
        <section key={`${bill.parent}-${bill.phone}`}>
          <h2>{bill.parent}</h2>
          {bill.lessons.map((lesson) => (
            <div className={lesson.paid ? "lesson paid-row" : "lesson"} key={lesson.id}>
              <div>
                <strong>{lesson.student}</strong>
                <small>{formatDate(lesson.date)} · {lesson.subject} · {lesson.minutes}分鐘{lesson.paid ? " · 已付" : ""}</small>
              </div>
              <div>{formatMoney(lesson.amount)}</div>
            </div>
          ))}
        </section>
      ))}
      <div className="actions">
        <CopyButton value={tutor.fpsId} label={`複製轉數快 ${tutor.fpsId}`} />
        <CopyButton value={pageUrl} label="複製呢條連結" />
      </div>
      <p className="fine">轉數快俾 {tutor.name}。堂單唔會代收這筆錢。</p>
    </main>
  );
}
