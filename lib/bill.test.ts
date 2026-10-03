import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  addDays,
  buildDigest,
  buildOutbox,
  buildSalesReport,
  formatMoney,
  groupByParent,
  isLive,
  shiftMonth,
  unpaidTotal,
  whatsappNumber,
} from "./bill";
import type { Lead, Tutor } from "./types";

const tutor: Tutor = {
  slug: "miss-chan",
  name: "陳老師",
  subject: "英文",
  fpsId: "51234567",
  phone: "90000001",
  plan: "paid",
  paidUntil: "2027-10-03",
  editKey: "secret",
  createdAt: "2026-10-03T00:00:00.000Z",
  lessons: [
    {
      id: "1",
      date: "2026-10-03",
      student: "林小明",
      parent: "林太",
      phone: "90000033",
      subject: "英文",
      minutes: 90,
      amount: 450,
      paid: false,
    },
    {
      id: "2",
      date: "2026-10-02",
      student: "張樂兒",
      parent: "張生",
      phone: "90000022",
      subject: "英文",
      minutes: 60,
      amount: 300,
      paid: false,
    },
    {
      id: "3",
      date: "2026-10-01",
      student: "黃子晴",
      parent: "黃太",
      phone: "90000011",
      subject: "英文",
      minutes: 90,
      amount: 450,
      paid: true,
    },
  ],
};

describe("bills", () => {
  it("sums only unpaid lessons", () => {
    assert.equal(unpaidTotal(tutor.lessons), 750);
    assert.equal(formatMoney(750), "HK$750");
  });

  it("groups a parent into one reminder", () => {
    const groups = groupByParent(tutor.lessons);
    assert.equal(groups.length, 3);
    const lam = groups.find((group) => group.parent === "林太");
    assert.equal(lam?.unpaid, 450);
  });

  it("turns an 8-digit Hong Kong number into a WhatsApp id", () => {
    assert.equal(whatsappNumber("9000 0033"), "85290000033");
  });

  it("writes one outbox item per parent who still owes money", () => {
    const outbox = buildOutbox([tutor], "2026-10", "https://tongdaan.example", new Date("2026-10-03T01:00:00Z"));
    assert.equal(outbox.items.length, 2);
    assert.equal(outbox.totalUnpaid, 750);
    assert.match(outbox.items[0].message, /轉數快：51234567/);
    assert.match(outbox.items[0].whatsapp, /^https:\/\/wa\.me\/852/);
  });

  it("does not remind parents of a demo page", () => {
    const outbox = buildOutbox([{ ...tutor, plan: "demo" }], "2026-10", "https://tongdaan.example");
    assert.equal(outbox.items.length, 0);
  });

  it("moves across year boundaries", () => {
    assert.equal(shiftMonth("2026-01", -1), "2025-12");
    assert.equal(shiftMonth("2026-12", 1), "2027-01");
  });

  it("keeps a 14-day trial live and then closes it", () => {
    const trial: Tutor = { ...tutor, plan: "trial", paidUntil: addDays("2026-10-03", 14) };
    assert.equal(trial.paidUntil, "2026-10-17");
    assert.equal(isLive(trial, "2026-10-17"), true);
    assert.equal(isLive(trial, "2026-10-18"), false);
  });

  it("mentions a page opened in the last 24 hours", () => {
    const digest = buildDigest([tutor], "https://tongdaan.example", new Date("2026-10-03T02:00:00Z"));
    assert.equal(digest.quiet, false);
    assert.match(digest.text, /新頁：陳老師/);
    const beforeEight = buildDigest(
      [{ ...tutor, createdAt: "2026-10-02T23:00:00.000Z" }],
      "https://tongdaan.example",
      new Date("2026-10-03T01:00:00Z"),
    );
    assert.match(beforeEight.text, /新頁：陳老師/);
    const older = buildDigest(
      [{ ...tutor, createdAt: "2026-10-01T00:00:00.000Z" }],
      "https://tongdaan.example",
      new Date("2026-10-03T02:00:00Z"),
    );
    assert.equal(older.quiet, true);
    assert.equal(older.text, "無事。");
  });

  it("kills the idea after 21 days without 5 paying tutors", () => {
    const leads: Lead[] = [
      { id: "l", name: "李老師", phone: "91111111", subject: "數學", createdAt: "2026-10-03T00:00:00Z" },
    ];
    const early = buildSalesReport([], leads, "https://tongdaan.example", "2026-10-03", new Date("2026-10-10T02:00:00Z"));
    assert.equal(early.kill, false);
    assert.equal(early.leadsWaiting.length, 1);
    const late = buildSalesReport([], leads, "https://tongdaan.example", "2026-10-03", new Date("2026-10-24T02:00:00Z"));
    assert.equal(late.kill, true);
  });
});
