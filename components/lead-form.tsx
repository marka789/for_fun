import { openTrial } from "@/lib/actions";

export function LeadForm() {
  return (
    <form className="stack" action={openTrial}>
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
        <input name="subject" required maxLength={40} placeholder="小五英文" />
      </label>
      <label>
        你嘅轉數快
        <input name="fpsId" required placeholder="手機號碼或 FPS ID" />
      </label>
      <label className="honeypot">
        Company
        <input name="company" tabIndex={-1} autoComplete="off" />
      </label>
      <button className="button button-green" type="submit">即刻開我嘅頁</button>
    </form>
  );
}
