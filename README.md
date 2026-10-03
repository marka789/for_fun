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

A tutor who fills in the landing form gets a parent link immediately and 14 days to use it. Their private edit key is on the welcome page. After HK$480 arrives, open `/studio` and press 收咗一年.

`/sell` is the paste-ready post.

## Money rule

Do not spend the HK$2,000 test budget on ads or a company. A one-year Hong Kong business registration certificate is HK$2,350, so the first sales have to pay that.

Stop if 21 days pass and fewer than 5 tutors have paid. `npm run sales` prints that decision. Exit code 2 means stop.

A form on the home page opens a trial immediately. Parent reminders include trial and paid pages, and skip the demo. When the 14 days end, the parent link closes until you press 收咗一年 in `/studio`.

## Grokbot

Three jobs are ready to port. The host clock should be Asia/Hong_Kong, because grokbot cron uses the host’s local time.

- `automations/monthly-reminders.json` — 09:00 on the 1st. Runs `npm run month`, then sends only the WhatsApp texts in `data/outbox.json`.
- `automations/morning.json` — 09:00 every day. Runs `npm run morning`. If `data/digest.txt` says 無事。, it stays quiet. Otherwise it tells you about a page opened in the last 24 hours, or a trial ending within 3 days.
- `automations/weekly-sales.json` — 10:00 on Mondays. Runs `npm run sales`. If `kill` is true, stop. Otherwise hand you the post. It does not publish the post itself.

`npm start` also refreshes the morning digest when the server boots, and again every hour.

Grokbot’s schedule call is a host-local cron, for example `0 9 1 * *`, with the prompt copied from the JSON file.
