"use server";

import { randomInt, randomUUID } from "crypto";
import { redirect } from "next/navigation";
import { revalidatePath } from "next/cache";
import { canManage, signIn, signOut } from "./auth";
import { addDays, digitsOnly, hongKongToday, TRIAL_DAYS, validDate, validSlug } from "./bill";
import { canEdit, unlockEdit } from "./edit-auth";
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

function newToken(length: number) {
  const alphabet = "abcdefghjkmnpqrstuvwxyz23456789";
  return Array.from({ length }, () => alphabet[randomInt(alphabet.length)]).join("");
}

function lessonError(formData: FormData, slug: string): never {
  if (String(formData.get("next") || "") === "edit") redirect(`/edit/${slug}?error=lesson`);
  redirect(`/studio?error=lesson&tutor=${slug}`);
}

export async function openTrial(formData: FormData) {
  if (String(formData.get("company") || "")) return;
  const name = String(formData.get("name") || "").trim();
  const phone = digitsOnly(String(formData.get("phone") || ""));
  const subject = String(formData.get("subject") || "").trim();
  const fpsId = String(formData.get("fpsId") || "").trim();
  if (name.length < 1 || name.length > 40 || phone.length < 8 || subject.length < 1 || fpsId.length < 4) {
    redirect("/?error=lead");
  }
  const studio = readStudio();
  let slug = newToken(6);
  while (studio.tutors.some((tutor) => tutor.slug === slug)) slug = newToken(6);
  const editKey = newToken(8);
  const createdAt = new Date().toISOString();
  studio.tutors.push({
    slug,
    name,
    subject,
    fpsId,
    phone,
    plan: "trial",
    paidUntil: addDays(hongKongToday(), TRIAL_DAYS),
    editKey,
    createdAt,
    lessons: [],
  });
  writeStudio(studio);
  const leads = readLeads();
  leads.unshift({ id: randomUUID(), name, phone, subject, createdAt });
  writeLeads(leads.slice(0, 200));
  refresh(slug);
  redirect(`/welcome/${slug}?key=${editKey}`);
}

export async function unlockTutor(formData: FormData) {
  const slug = String(formData.get("slug") || "");
  const key = String(formData.get("key") || "").trim();
  const ok = await unlockEdit(slug, key);
  if (!ok) redirect(`/edit/${slug}?error=key`);
  redirect(`/edit/${slug}`);
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
    editKey: newToken(8),
    createdAt: new Date().toISOString(),
    lessons: [],
  });
  writeStudio(studio);
  refresh(slug);
  redirect("/studio");
}

export async function renewTutor(formData: FormData) {
  await guard();
  const slug = String(formData.get("slug") || "");
  const studio = readStudio();
  const tutor = studio.tutors.find((item) => item.slug === slug);
  if (!tutor || tutor.plan === "demo") redirect("/studio?error=missing");
  tutor.plan = "paid";
  tutor.paidUntil = addYears(hongKongToday(), 1);
  writeStudio(studio);
  refresh(slug);
  redirect(`/studio?tutor=${slug}`);
}

async function canChange(slug: string) {
  if (await canManage()) return;
  if (await canEdit(slug)) return;
  redirect(`/edit/${slug}?error=key`);
}

function returnTo(formData: FormData, slug: string) {
  if (String(formData.get("next") || "") === "edit") redirect(`/edit/${slug}`);
  redirect(`/studio?tutor=${slug}`);
}

export async function addLesson(formData: FormData) {
  const slug = String(formData.get("slug") || "");
  await canChange(slug);
  const date = String(formData.get("date") || "");
  const student = String(formData.get("student") || "").trim();
  const parent = String(formData.get("parent") || "").trim();
  const phone = digitsOnly(String(formData.get("phone") || ""));
  const subject = String(formData.get("subject") || "").trim();
  const minutes = Number(formData.get("minutes"));
  const amount = Number(formData.get("amount"));
  if (!validDate(date) || !student || !parent || phone.length < 8) lessonError(formData, slug);
  if (!Number.isInteger(minutes) || minutes < 15 || minutes > 480) lessonError(formData, slug);
  if (!Number.isInteger(amount) || amount < 1 || amount > 100_000) lessonError(formData, slug);
  const studio = readStudio();
  const tutor = studio.tutors.find((item) => item.slug === slug);
  if (!tutor) lessonError(formData, slug);
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
  returnTo(formData, slug);
}

export async function togglePaid(formData: FormData) {
  const slug = String(formData.get("slug") || "");
  await canChange(slug);
  const id = String(formData.get("id") || "");
  const studio = readStudio();
  const tutor = studio.tutors.find((item) => item.slug === slug);
  const lesson = tutor?.lessons.find((item) => item.id === id);
  if (!lesson) redirect("/studio?error=missing");
  lesson.paid = !lesson.paid;
  writeStudio(studio);
  refresh(slug);
  returnTo(formData, slug);
}

export async function deleteLesson(formData: FormData) {
  const slug = String(formData.get("slug") || "");
  await canChange(slug);
  const id = String(formData.get("id") || "");
  const studio = readStudio();
  const tutor = studio.tutors.find((item) => item.slug === slug);
  if (!tutor) redirect("/studio?error=missing");
  tutor.lessons = tutor.lessons.filter((lesson) => lesson.id !== id);
  writeStudio(studio);
  refresh(slug);
  returnTo(formData, slug);
}

function addYears(iso: string, years: number) {
  const [year, month, day] = iso.split("-").map(Number);
  return `${year + years}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
}
