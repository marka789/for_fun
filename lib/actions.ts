"use server";

import { randomUUID } from "crypto";
import { redirect } from "next/navigation";
import { revalidatePath } from "next/cache";
import { canManage, signIn, signOut } from "./auth";
import { digitsOnly, hongKongToday, validDate, validSlug } from "./bill";
import { readLeads, readStudio, writeLeads, writeStudio } from "./store";
import type { Lesson } from "./types";

async function guard() {
  if (!(await canManage())) redirect("/studio?error=locked");
}

function refresh(slug?: string) {
  revalidatePath("/studio");
  revalidatePath("/sell");
  if (slug) revalidatePath(`/p/${slug}`);
}

export async function login(formData: FormData) {
  const ok = await signIn(String(formData.get("password") || ""));
  if (!ok) redirect("/studio?error=password");
  redirect("/studio");
}

export async function logout() {
  await signOut();
  redirect("/studio");
}

export async function createLead(formData: FormData) {
  if (String(formData.get("company") || "")) return;
  const name = String(formData.get("name") || "").trim();
  const phone = digitsOnly(String(formData.get("phone") || ""));
  const subject = String(formData.get("subject") || "").trim();
  if (name.length < 1 || name.length > 40 || phone.length < 8 || subject.length > 40) {
    redirect("/?error=lead");
  }
  const leads = readLeads();
  leads.unshift({ id: randomUUID(), name, phone, subject, createdAt: new Date().toISOString() });
  writeLeads(leads.slice(0, 200));
  revalidatePath("/sell");
  redirect("/?sent=1");
}

export async function createTutor(formData: FormData) {
  await guard();
  const slug = String(formData.get("slug") || "").trim().toLowerCase();
  const name = String(formData.get("name") || "").trim();
  const subject = String(formData.get("subject") || "").trim();
  const fpsId = String(formData.get("fpsId") || "").trim();
  const phone = digitsOnly(String(formData.get("phone") || ""));
  if (!validSlug(slug) || name.length < 1 || fpsId.length < 4 || phone.length < 8) {
    redirect("/studio?error=tutor");
  }
  const studio = readStudio();
  if (studio.tutors.some((tutor) => tutor.slug === slug)) redirect("/studio?error=exists");
  studio.tutors.push({
    slug,
    name,
    subject: subject || "補習",
    fpsId,
    phone,
    plan: "paid",
    paidUntil: addYears(hongKongToday(), 1),
    lessons: [],
  });
  writeStudio(studio);
  refresh(slug);
  redirect("/studio");
}

export async function addLesson(formData: FormData) {
  await guard();
  const slug = String(formData.get("slug") || "");
  const date = String(formData.get("date") || "");
  const student = String(formData.get("student") || "").trim();
  const parent = String(formData.get("parent") || "").trim();
  const phone = digitsOnly(String(formData.get("phone") || ""));
  const subject = String(formData.get("subject") || "").trim();
  const minutes = Number(formData.get("minutes"));
  const amount = Number(formData.get("amount"));
  if (!validDate(date) || !student || !parent || phone.length < 8) redirect(`/studio?error=lesson&tutor=${slug}`);
  if (!Number.isInteger(minutes) || minutes < 15 || minutes > 480) redirect(`/studio?error=lesson&tutor=${slug}`);
  if (!Number.isInteger(amount) || amount < 1 || amount > 100_000) redirect(`/studio?error=lesson&tutor=${slug}`);
  const studio = readStudio();
  const tutor = studio.tutors.find((item) => item.slug === slug);
  if (!tutor) redirect("/studio?error=missing");
  const lesson: Lesson = {
    id: randomUUID(),
    date,
    student,
    parent,
    phone,
    subject: subject || tutor.subject,
    minutes,
    amount,
    paid: false,
  };
  tutor.lessons.push(lesson);
  writeStudio(studio);
  refresh(slug);
  redirect(`/studio?tutor=${slug}`);
}

export async function togglePaid(formData: FormData) {
  await guard();
  const slug = String(formData.get("slug") || "");
  const id = String(formData.get("id") || "");
  const studio = readStudio();
  const tutor = studio.tutors.find((item) => item.slug === slug);
  const lesson = tutor?.lessons.find((item) => item.id === id);
  if (!lesson) redirect("/studio?error=missing");
  lesson.paid = !lesson.paid;
  writeStudio(studio);
  refresh(slug);
  redirect(`/studio?tutor=${slug}`);
}

export async function deleteLesson(formData: FormData) {
  await guard();
  const slug = String(formData.get("slug") || "");
  const id = String(formData.get("id") || "");
  const studio = readStudio();
  const tutor = studio.tutors.find((item) => item.slug === slug);
  if (!tutor) redirect("/studio?error=missing");
  tutor.lessons = tutor.lessons.filter((lesson) => lesson.id !== id);
  writeStudio(studio);
  refresh(slug);
  redirect(`/studio?tutor=${slug}`);
}

function addYears(iso: string, years: number) {
  const [year, month, day] = iso.split("-").map(Number);
  return `${year + years}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
}
