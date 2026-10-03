import { createHmac, timingSafeEqual } from "crypto";
import { cookies } from "next/headers";

const cookieName = "studio_session";

function secret() {
  return process.env.SESSION_SECRET || "tongdaan-dev-session";
}

export function passwordRequired(): boolean {
  return Boolean(process.env.ADMIN_PASSWORD) || process.env.NODE_ENV === "production";
}

function signature(password: string) {
  return createHmac("sha256", secret()).update(password).digest("hex");
}

function safeEqual(left: string, right: string) {
  const a = Buffer.from(left);
  const b = Buffer.from(right);
  if (a.length !== b.length) return false;
  return timingSafeEqual(a, b);
}

export async function canManage(): Promise<boolean> {
  const expected = process.env.ADMIN_PASSWORD;
  if (!expected) return process.env.NODE_ENV !== "production";
  const jar = await cookies();
  const got = jar.get(cookieName)?.value || "";
  return safeEqual(got, signature(expected));
}

export async function signIn(password: string) {
  const expected = process.env.ADMIN_PASSWORD;
  if (!expected || password !== expected) return false;
  const jar = await cookies();
  jar.set(cookieName, signature(expected), {
    httpOnly: true,
    sameSite: "lax",
    path: "/",
    secure: process.env.NODE_ENV === "production",
  });
  return true;
}

export async function signOut() {
  const jar = await cookies();
  jar.delete(cookieName);
}
