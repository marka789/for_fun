import type { Lead, Lesson, Outbox, OutboxItem, ParentBill, SalesReport, Tutor } from "./types";

export const PRICE_HKD = 480;
export const KILL_DAYS = 21;
export const KILL_SALES = 5;
export const LAUNCH_DATE = "2026-10-03";

export function hongKongToday(now = new Date()): string {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Hong_Kong",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(now);
}

export function hongKongMonth(now = new Date()): string {
  return hongKongToday(now).slice(0, 7);
}

export function shiftMonth(month: string, delta: number): string {
  const [year, mon] = month.split("-").map(Number);
  const date = new Date(Date.UTC(year, mon - 1 + delta, 1));
  const y = date.getUTCFullYear();
  const m = String(date.getUTCMonth() + 1).padStart(2, "0");
  return `${y}-${m}`;
}

export function formatMonth(month: string): string {
  const [year, mon] = month.split("-");
  return `${year}年${Number(mon)}月`;
}

export function formatDate(iso: string): string {
  const [year, month, day] = iso.split("-").map(Number);
  const currentYear = Number(hongKongToday().slice(0, 4));
  const body = `${month}月${day}日`;
  return year === currentYear ? body : `${year}年${body}`;
}

export function formatMoney(amount: number): string {
  return `HK$${amount.toLocaleString("en-HK")}`;
}

export function monthLessons(tutor: Tutor, month: string): Lesson[] {
  return tutor.lessons
    .filter((lesson) => lesson.date.startsWith(month))
    .sort((a, b) => a.date.localeCompare(b.date) || a.student.localeCompare(b.student, "zh-Hant"));
}

export function unpaidTotal(lessons: Lesson[]): number {
  return lessons.reduce((sum, lesson) => sum + (lesson.paid ? 0 : lesson.amount), 0);
}

export function groupByParent(lessons: Lesson[]): ParentBill[] {
  const groups = new Map<string, ParentBill>();
  for (const lesson of lessons) {
    const key = `${lesson.parent}\u0000${lesson.phone}`;
    const existing = groups.get(key);
    if (existing) {
      existing.lessons.push(lesson);
      existing.unpaid += lesson.paid ? 0 : lesson.amount;
    } else {
      groups.set(key, {
        parent: lesson.parent,
        phone: lesson.phone,
        lessons: [lesson],
        unpaid: lesson.paid ? 0 : lesson.amount,
      });
    }
  }
  return [...groups.values()];
}

export function digitsOnly(phone: string): string {
  return phone.replace(/\D/g, "");
}

export function whatsappNumber(phone: string): string | null {
  const digits = digitsOnly(phone);
  if (digits.length === 8) return `852${digits}`;
  if (digits.length === 11 && digits.startsWith("852")) return digits;
  if (digits.length >= 10 && digits.length <= 15) return digits;
  return null;
}

export function parentMessage(tutor: Tutor, bill: ParentBill, month: string, pageUrl: string): string {
  const lines = bill.lessons.map(
    (lesson) =>
      `${lesson.student} ${formatDate(lesson.date)} ${lesson.subject} ${lesson.minutes}分鐘 ${formatMoney(lesson.amount)}${lesson.paid ? " 已付" : ""}`,
  );
  return [
    `${tutor.name} ${formatMonth(month)}堂數`,
    ...lines,
    `未付合計 ${formatMoney(bill.unpaid)}`,
    `轉數快：${tutor.fpsId}`,
    `明細：${pageUrl}`,
  ].join("\n");
}

export function whatsappLink(phone: string, message: string): string | null {
  const number = whatsappNumber(phone);
  if (!number) return null;
  return `https://wa.me/${number}?text=${encodeURIComponent(message)}`;
}

export function buildOutbox(tutors: Tutor[], month: string, origin: string, now = new Date()): Outbox {
  const items: OutboxItem[] = [];
  for (const tutor of tutors) {
    if (tutor.plan === "demo") continue;
    const pageUrl = `${origin}/p/${tutor.slug}?month=${month}`;
    for (const bill of groupByParent(monthLessons(tutor, month))) {
      if (bill.unpaid <= 0) continue;
      const message = parentMessage(tutor, bill, month, pageUrl);
      const link = whatsappLink(bill.phone, message);
      if (!link) continue;
      items.push({
        tutorSlug: tutor.slug,
        tutorName: tutor.name,
        parent: bill.parent,
        phone: bill.phone,
        whatsapp: link,
        unpaid: bill.unpaid,
        message,
      });
    }
  }
  return {
    generatedAt: now.toISOString(),
    month,
    origin,
    items,
    totalUnpaid: items.reduce((sum, item) => sum + item.unpaid, 0),
  };
}

export function salesPost(origin: string): string {
  return [
    "補習老師，學費唔好再靠記事簿。",
    "",
    "一條連結俾家長：今個月上咗幾多堂、未付幾多、轉數快號碼。",
    "家長直接 FPS 俾你，錢唔經我。",
    "",
    "一年 HK$480。",
    `示範：${origin}/p/miss-chan`,
    "",
    "想用就留低 WhatsApp。",
  ].join("\n");
}

export function daysBetween(start: string, end: string): number {
  const a = Date.parse(`${start}T00:00:00Z`);
  const b = Date.parse(`${end}T00:00:00Z`);
  return Math.floor((b - a) / 86_400_000);
}

export function isPaidTutor(tutor: Tutor, today: string): boolean {
  return tutor.plan === "paid" && Boolean(tutor.paidUntil && tutor.paidUntil >= today);
}

export function leadsWithoutPage(leads: Lead[], tutors: Tutor[]): Lead[] {
  const phones = new Set(tutors.map((tutor) => digitsOnly(tutor.phone)));
  return leads.filter((lead) => !phones.has(digitsOnly(lead.phone)));
}

export function buildSalesReport(
  tutors: Tutor[],
  leads: Lead[],
  origin: string,
  launchDate = LAUNCH_DATE,
  now = new Date(),
): SalesReport {
  const today = hongKongToday(now);
  const paidTutors = tutors.filter((tutor) => isPaidTutor(tutor, today)).length;
  const daysSinceLaunch = Math.max(0, daysBetween(launchDate, today));
  const waiting = leadsWithoutPage(leads, tutors);
  const kill = daysSinceLaunch >= KILL_DAYS && paidTutors < KILL_SALES;
  return {
    generatedAt: now.toISOString(),
    launchDate,
    daysSinceLaunch,
    paidTutors,
    demoTutors: tutors.filter((tutor) => tutor.plan === "demo").length,
    leadsWaiting: waiting,
    kill,
    reason: kill
      ? `開咗 ${daysSinceLaunch} 日，收咗錢嘅老師少過 ${KILL_SALES} 個。停。`
      : `收咗錢嘅老師 ${paidTutors} 個。未夠 ${KILL_SALES} 個就繼續貼文，唔好再花錢。`,
    post: salesPost(origin),
  };
}

export function validSlug(slug: string): boolean {
  return /^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slug);
}

export function validDate(value: string): boolean {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
  const [year, month, day] = value.split("-").map(Number);
  const date = new Date(Date.UTC(year, month - 1, day));
  return date.getUTCFullYear() === year && date.getUTCMonth() === month - 1 && date.getUTCDate() === day;
}

export function validMonth(value: string): boolean {
  return /^\d{4}-(0[1-9]|1[0-2])$/.test(value);
}
