import { notFound } from "next/navigation";
import { CopyButton } from "@/components/copy-button";
import { unlockTutor } from "@/lib/actions";
import { formatDate, PRICE_HKD } from "@/lib/bill";
import { readStudio } from "@/lib/store";
import { headers } from "next/headers";

export const dynamic = "force-dynamic";
export const metadata = { robots: { index: false, follow: false } };

async function origin() {
  if (process.env.APP_ORIGIN) return process.env.APP_ORIGIN.replace(/\/$/, "");
  const headerList = await headers();
  const host = headerList.get("x-forwarded-host") || headerList.get("host") || "localhost:3000";
  const proto = headerList.get("x-forwarded-proto") || "http";
  return `${proto}://${host}`;
}

export default async function WelcomePage({
  params,
  searchParams,
}: {
  params: Promise<{ slug: string }>;
  searchParams: Promise<{ key?: string }>;
}) {
  const { slug } = await params;
  const query = await searchParams;
  const tutor = readStudio().tutors.find((item) => item.slug === slug);
  if (!tutor || !tutor.editKey || query.key !== tutor.editKey) notFound();
  const base = await origin();
  const parentUrl = `${base}/p/${tutor.slug}`;
  const editUrl = `${base}/edit/${tutor.slug}`;

  return (
    <main className="card stack">
      <p className="kicker">開咗</p>
      <h1>{tutor.name}，頁面用得。</h1>
      <p>家長連結。呢條可以轉發。</p>
      <p><a href={parentUrl}>{parentUrl}</a></p>
      <CopyButton value={parentUrl} label="複製家長連結" />
      <p>記堂數要用鑰匙，唔好轉發俾家長。用到 {tutor.paidUntil ? formatDate(tutor.paidUntil) : "14日後"}。之後一年 HK${PRICE_HKD}。</p>
      <p>鑰匙：{tutor.editKey}</p>
      <CopyButton value={tutor.editKey} label="複製鑰匙" />
      <form action={unlockTutor}>
        <input type="hidden" name="slug" value={tutor.slug} />
        <input type="hidden" name="key" value={tutor.editKey} />
        <button className="button button-green" type="submit">去記堂數</button>
      </form>
      <p className="fine">記低 {editUrl}。下次用鑰匙入。</p>
    </main>
  );
}
