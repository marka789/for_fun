export type Lesson = {
  id: string;
  date: string;
  student: string;
  parent: string;
  phone: string;
  subject: string;
  minutes: number;
  amount: number;
  paid: boolean;
};

export type Tutor = {
  slug: string;
  name: string;
  subject: string;
  fpsId: string;
  phone: string;
  plan: "demo" | "paid";
  paidUntil: string | null;
  lessons: Lesson[];
};

export type Lead = {
  id: string;
  name: string;
  phone: string;
  subject: string;
  createdAt: string;
};

export type Studio = {
  tutors: Tutor[];
};

export type ParentBill = {
  parent: string;
  phone: string;
  lessons: Lesson[];
  unpaid: number;
};

export type OutboxItem = {
  tutorSlug: string;
  tutorName: string;
  parent: string;
  phone: string;
  whatsapp: string;
  unpaid: number;
  message: string;
};

export type Outbox = {
  generatedAt: string;
  month: string;
  origin: string;
  items: OutboxItem[];
  totalUnpaid: number;
};

export type SalesReport = {
  generatedAt: string;
  launchDate: string;
  daysSinceLaunch: number;
  paidTutors: number;
  demoTutors: number;
  leadsWaiting: Lead[];
  kill: boolean;
  reason: string;
  post: string;
};
