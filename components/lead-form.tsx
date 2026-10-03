import { createLead } from "@/lib/actions";

export function LeadForm({ sent }: { sent: boolean }) {
  if (sent) {
    return <p className="ok">收到。我開會用你嘅 WhatsApp 覆你，開一條家長連結。</p>;
  }

  return (
    <form className="stack" action={createLead}>
      <label>
        老師點稱呼
        <input name="name" required maxLength={40} placeholder="陳老師" />
      </label>
      <label>
        WhatsApp
        <input name="phone" required inputMode="tel" placeholder="9xxxxxxx" />
      </label>
      <label>
        教咩
        <input name="subject" maxLength={40} placeholder="小五英文" />
      </label>
      <label className="honeypot">
        Company
        <input name="company" tabIndex={-1} autoComplete="off" />
      </label>
      <button className="button button-green" type="submit">留低，等我開頁</button>
    </form>
  );
}
