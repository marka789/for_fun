import { notFound } from "next/navigation";
import { addLesson, deleteLesson, togglePaid, unlockTutor } from "@/lib/actions";
import { canEdit } from "@/lib/edit-auth";
import { formatDate, formatMoney, hongKongToday, unpaidTotal } from "@/lib/bill";
import { readStudio } from "@/lib/store";

export const dynamic = "force-dynamic";
export const metadata = { robots: { index: false, follow: false } };

export default async function EditPage({
  params,
  searchParams,
}: {
  params: Promise<{ slug: string }>;
  searchParams: Promise<{ key?: string; error?: string }>;
}) {
  const { slug } = await params;
  const query = await searchParams;
  const tutor = readStudio().tutors.find((item) => item.slug === slug);
  if (!tutor || tutor.plan === "demo" || !tutor.editKey) notFound();

  const open = query.key === tutor.editKey || (await canEdit(slug));

  if (!open) {
    return (
      <main className="card">
        <h1>記堂數</h1>
        {query.error ? <p className="error">鑰匙唔啱。</p> : null}
        <form className="stack" action={unlockTutor}>
          <input type="hidden" name="slug" value={slug} />
          <label>
            鑰匙
            <input name="key" required autoComplete="off" defaultValue={query.key || ""} />
          </label>
          <button className="button" type="submit">入去</button>
        </form>
      </main>
    );
  }

  return (
    <main className="card stack">
      <p className="kicker">{tutor.name} · {tutor.plan === "paid" ? "已續" : `試用至 ${tutor.paidUntil}`}</p>
      <h1>記堂數</h1>
      <p>未付 {formatMoney(unpaidTotal(tutor.lessons))} · <a href={`/p/${tutor.slug}`}>家長頁</a></p>
      {query.error === "lesson" ? <p className="error">堂數資料唔完整。</p> : null}
      <form className="lesson-form" action={addLesson}>
        <input type="hidden" name="slug" value={slug} />
        <input type="hidden" name="next" value="edit" />
        <label>日期<input name="date" type="date" required defaultValue={hongKongToday()} /></label>
        <label>分鐘<input name="minutes" type="number" min={15} max={480} defaultValue={60} required /></label>
        <label>學生<input name="student" required /></label>
        <label>家長<input name="parent" required /></label>
        <label>家長 WhatsApp<input name="phone" required inputMode="tel" /></label>
        <label>金額 HK$<input name="amount" type="number" min={1} max={100000} required /></label>
        <label className="span-2">科目<input name="subject" placeholder={tutor.subject} /></label>
        <button className="button span-2" type="submit">加一堂</button>
      </form>
      {tutor.lessons
        .slice()
        .sort((a, b) => b.date.localeCompare(a.date))
        .map((lesson) => (
          <div className="admin-lesson" key={lesson.id}>
            <div>
              <strong>{formatDate(lesson.date)} {lesson.student}</strong>
              <small className="muted"> {lesson.parent} · {formatMoney(lesson.amount)} · {lesson.paid ? "已付" : "未付"}</small>
            </div>
            <div className="actions">
              <form action={togglePaid}>
                <input type="hidden" name="slug" value={slug} />
                <input type="hidden" name="id" value={lesson.id} />
                <input type="hidden" name="next" value="edit" />
                <button className="button button-small" type="submit">{lesson.paid ? "改未付" : "已付"}</button>
              </form>
              <form action={deleteLesson}>
                <input type="hidden" name="slug" value={slug} />
                <input type="hidden" name="id" value={lesson.id} />
                <input type="hidden" name="next" value="edit" />
                <button className="button button-ghost button-small" type="submit">刪除</button>
              </form>
            </div>
          </div>
        ))}
    </main>
  );
}
