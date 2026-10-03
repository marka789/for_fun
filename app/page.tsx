import { LeadForm } from "@/components/lead-form";
import { PRICE_HKD } from "@/lib/bill";

export const dynamic = "force-dynamic";

const errors: Record<string, string> = {
  lead: "留個名同一個香港電話號碼。",
};

export default async function HomePage({
  searchParams,
}: {
  searchParams: Promise<{ sent?: string; error?: string }>;
}) {
  const query = await searchParams;

  return (
    <main>
      <section className="hero">
        <p className="kicker">補習老師用</p>
        <h1>一條連結，收齐學費。</h1>
        <p className="lede">家長打開就見到今個月上咗邊幾堂、未付幾多、同你嘅轉數快。你唔使再逐個 WhatsApp 計數。</p>
        <p className="english">Parents open one link. It shows this month’s lessons, what they still owe, and your FPS number.</p>
      </section>
      <section className="grid">
        <div className="card">
          <h2>點樣用</h2>
          <p>你記低堂數。家長收到一條連結。佢哋自己轉數快俾你，錢直接入你戶口。</p>
          <div className="row">
            <a className="button button-green" href="/p/miss-chan">睇吓家長頁</a>
            <a className="button button-ghost" href="#ask">我想用</a>
          </div>
          {query.error ? <p className="error">{errors[query.error] || "再試一次。"}</p> : null}
        </div>
        <div className="card" id="ask">
          <p className="kicker">一年</p>
          <p className="price">HK${PRICE_HKD}</p>
          <p className="fine">收咗錢先開你嘅頁。示範頁而家就可以俾人睇。</p>
          <LeadForm sent={query.sent === "1"} />
        </div>
      </section>
    </main>
  );
}
