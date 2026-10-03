# 堂單

A Hong Kong tutor sends parents one link. The page shows this month’s lessons, the unpaid balance, and the tutor’s FPS number. Parents pay the tutor directly. The product costs HK$480 a year.

The demo parent page is `/p/miss-chan`. The FPS number on it is fake.

## Run

```bash
npm install
npm test
npm run dev
```

Open http://localhost:3000. On your own machine the studio at `/studio` is open until you set a password. Before anyone else can reach it:

```bash
ADMIN_PASSWORD=choose-one
APP_ORIGIN=https://your-domain
```

`/sell` is the paste-ready post and the list of tutors who left a WhatsApp number.

## Money rule

Do not spend the HK$2,000 test budget on ads or a company. A one-year Hong Kong business registration certificate is HK$2,350, so the first sales have to pay that.

Stop if 21 days pass and fewer than 5 tutors have paid. `npm run sales` prints that decision. Exit code 2 means stop.

A tutor page is opened only after the HK$480 arrives in your FPS. Create it in the studio. Demo pages are never included in reminder messages.

## Grokbot

Two jobs are ready to port. The host clock should be Asia/Hong_Kong, because grokbot cron uses the host’s local time.

- `automations/monthly-reminders.json` — 09:00 on the 1st. Runs `npm run month`, then sends only the WhatsApp texts in `data/outbox.json`.
- `automations/weekly-sales.json` — 10:00 on Mondays. Runs `npm run sales`. If `kill` is true, stop. Otherwise hand you the post. It does not publish the post itself.

Grokbot’s schedule call is a host-local cron, for example `0 9 1 * *`, with the prompt copied from the JSON file.
