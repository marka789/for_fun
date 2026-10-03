import { createHmac, timingSafeEqual } from "crypto";
import { cookies, headers } from "next/headers";
import { readStudio } from "./store";

function secret() {
  return process.env.SESSION_SECRET || "tongdaan-dev-session";
}

function signature(value: string) {
  return createHmac("sha256", secret()).update(value).digest("hex");
}

function safeEqual(left: string, right: string) {
  const a = Buffer.from(left);
  const b = Buffer.from(right);
  if (a.length !== b.length) return false;
  return timingSafeEqual(a, b);
}

function cookieName(slug: string) {
  return `edit_${slug}`;
}

export async function canEdit(slug: string): Promise<boolean> {
  const tutor = readStudio().tutors.find((item) => item.slug === slug);
  if (!tutor?.editKey) return false;
  const jar = await cookies();
  const got = jar.get(cookieName(slug))?.value || "";
  return safeEqual(got, signature(`${slug}:${tutor.editKey}`));
}

export async function unlockEdit(slug: string, key: string) {
  const tutor = readStudio().tutors.find((item) => item.slug === slug);
  if (!tutor?.editKey || tutor.editKey !== key) return false;
  const headerList = await headers();
  const proto = headerList.get("x-forwarded-proto") ?? "http";
  const jar = await cookies();
  jar.set(cookieName(slug), signature(`${slug}:${tutor.editKey}`), {
    httpOnly: true,
    sameSite: "lax",
    path: "/",
    secure: proto === "https",
  });
  return true;
}
