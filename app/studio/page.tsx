import { addLesson, createTutor, deleteLesson, login, logout, renewTutor, togglePaid } from "@/lib/actions";
import { canManage, passwordRequired } from "@/lib/auth";
import { formatDate, formatMoney, hongKongToday, unpaidTotal } from "@/lib/bill";
import { readStudio } from "@/lib/store";

export const dynamic = "force-dynamic";
export const metadata = { robots: { index: false, follow: false } };

const errors: Record<string, string> = {
  locked: "未設定密碼，對外之前唔好打開後台。",
  password: "密碼唔啱。",
  tutor: "連結名稱用英文細階同短橫線，轉數快同電話都要填。",
  exists: "呢個連結名稱用咗。",
  lesson: "堂數資料唔完整。",
  missing: "搵唔到呢一堂。",
};

export default async function StudioPage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string; tutor?: string }>;
}) {
  const query = await searchParams;
  const allowed = await canManage();

  if (!allowed) {
    return (
      <main className="card">
        <h1>老師後台</h1>
        {query.error ? <p className="error">{errors[query.error] || "入唔到。"}</p> : null}
        {passwordRequired() && process.env.ADMIN_PASSWORD ? (
          <form className="stack" action={login}>
            <label>
              密碼
              <input name="password" type="password" required />
            </label>
            <button className="button" type="submit">入去</button>
          </form>
        ) : (
          <p>生產環境要先設定 ADMIN_PASSWORD。</p>
        )}
      </main>
    );
  }

  const studio = readStudio();
  const selected = studio.tutors.find((tutor) => tutor.slug === query.tutor) || studio.tutors[0];
  const today = hongKongToday();

  return (
    <main className="stack">
      {!passwordRequired() ? <p className="notice">未設密碼。而家只可以喺呢部機用。對外之前喺環境變數設定 ADMIN_PASSWORD。</p> : null}
      {query.error ? <p className="error">{errors[query.error] || "有啲野唔啱。"}</p> : null}
      <div className="grid">
        <section className="card">
          <div className="bill-head">
            <h1>堂數</h1>
            <form action={logout}><button className="button button-ghost button-small" type="submit">登出</button></form>
          </div>
          {selected ? (
            <>
              <p className="kicker">
                {selected.name} · {selected.plan === "paid" ? `已收至 ${selected.paidUntil}` : selected.plan === "trial" ? `試用至 ${selected.paidUntil}` : "示範"}
              </p>
              {selected.plan === "trial" ? (
                <form action={renewTutor}>
                  <input type="hidden" name="slug" value={selected.slug} />
                  <button className="button button-small" type="submit">收咗一年</button>
                </form>
              ) : null}
              {selected.editKey ? <p className="fine">鑰匙 {selected.editKey}</p> : null}
              <p>未付 {formatMoney(unpaidTotal(selected.lessons))} · <a href={`/p/${selected.slug}`}>家長頁</a></p>
              <form className="lesson-form" action={addLesson}>
                <input type="hidden" name="slug" value={selected.slug} />
                <label>日期<input name="date" type="date" required defaultValue={today} /></label>
                <label>分鐘<input name="minutes" type="number" min={15} max={480} defaultValue={60} required /></label>
                <label>學生<input name="student" required placeholder="林小明" /></label>
                <label>家長<input name="parent" required placeholder="林太" /></label>
                <label>家長 WhatsApp<input name="phone" required inputMode="tel" placeholder="9xxxxxxx" /></label>
                <label>金額 HK$<input name="amount" type="number" min={1} max={100000} required placeholder="450" /></label>
                <label className="span-2">科目<input name="subject" placeholder={selected.subject} /></label>
                <button className="button span-2" type="submit">加一堂</button>
              </form>
              <div className="table">
                {selected.lessons
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
                          <input type="hidden" name="slug" value={selected.slug} />
                          <input type="hidden" name="id" value={lesson.id} />
                          <button className="button button-small" type="submit">{lesson.paid ? "改未付" : "已付"}</button>
                        </form>
                        <form action={deleteLesson}>
                          <input type="hidden" name="slug" value={selected.slug} />
                          <input type="hidden" name="id" value={lesson.id} />
                          <button className="button button-ghost button-small" type="submit">刪除</button>
                        </form>
                      </div>
                    </div>
                  ))}
              </div>
            </>
          ) : <p>未有老師。</p>}
        </section>
        <aside className="stack">
          <section className="card">
            <h2>邊個老師</h2>
            <div className="stack">
              {studio.tutors.map((tutor) => (
                <a key={tutor.slug} href={`/studio?tutor=${tutor.slug}`}>{tutor.name}</a>
              ))}
            </div>
          </section>
          <section className="card">
            <h2>收咗 HK$480 先開</h2>
            <form className="stack" action={createTutor}>
              <label>稱呼<input name="name" required placeholder="李老師" /></label>
              <label>連結名稱<input name="slug" required placeholder="lee" pattern="[a-z0-9]+(-[a-z0-9]+)*" /></label>
              <label>科目<input name="subject" placeholder="數學" /></label>
              <label>轉數快<input name="fpsId" required placeholder="手機號碼或 FPS ID" /></label>
              <label>老師 WhatsApp<input name="phone" required inputMode="tel" /></label>
              <button className="button button-green" type="submit">開頁</button>
            </form>
          </section>
        </aside>
      </div>
    </main>
  );
}
