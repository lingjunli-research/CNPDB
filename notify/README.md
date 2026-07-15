# cNPDB email notifications

Automated emails so nobody has to watch the GitHub Actions tab. Three of them:

| When | Email | Workflow |
|------|-------|----------|
| **Monthly**, after the literature scan | "Papers to check this month" — crustacean-neuropeptide papers not yet in the database. A paper drops off automatically once its DOI is in the DB. | `lit-mining.yml` |
| **When the database is pushed** | "QC found issues to check" — a summary of any accuracy problems. Does **not** block the update. | `db-accuracy.yml` |
| **When the tests fail** on any push | "Unit tests FAILED" — with a link to the run. | `tests.yml` |

All three send to the same list and are otherwise independent.

## Who gets the emails — `recipients.txt`

Edit [`recipients.txt`](recipients.txt): one email address per line. Lines
starting with `#` are ignored. Commit the change — that's all. No code involved.

## One-time setup: let Actions send email (required once)

Nothing sends until this is done. Until then, the workflows still run fine — the
email step just logs "email skipped" and succeeds.

### Important: only the *sending* account needs 2FA

Gmail requires 2-Step Verification (2FA) on the account that **sends** the email,
because an "app password" can only be created once 2FA is on. This does **not**
affect your shared lab inboxes — they only ever *receive* these emails, and
recipients need nothing set up at all.

So don't put 2FA on a shared account. Instead, make **one dedicated bot account**
that exists only to send these notifications, and put 2FA on that:

1. Create a new Gmail just for this, e.g. `cnpdb.notifications@gmail.com`. One
   person owns it; nobody reads it.
2. On that bot account, turn on 2-Step Verification.
3. Go to <https://myaccount.google.com/apppasswords> and create an app password
   named e.g. "cNPDB GitHub". Copy the 16-character code.
4. In this repository on GitHub: **Settings → Secrets and variables → Actions →
   New repository secret**, and add two secrets:
   - `MAIL_USERNAME` — the bot's full Gmail address
   - `MAIL_PASSWORD` — the 16-character app password
5. Add the real recipient addresses (including your shared lab inboxes) to
   `recipients.txt` and commit.

That's it. To test immediately without waiting for a schedule, open the
**Actions** tab, pick **db-accuracy** or **literature-mining**, and click
**Run workflow** (workflow_dispatch).

### Switching away from Gmail later

If you ever want to send through a different provider (a transactional service
like Brevo/SendGrid, or a university relay), you don't need Gmail-specific
secrets — just pass `server_address` (and `server_port`) to the
`notify-email` action in each workflow, and set `MAIL_USERNAME` / `MAIL_PASSWORD`
to that provider's SMTP credentials. The default is Gmail's server.

## Turning it off

Remove the secrets (or empty `recipients.txt`) and emails stop; the workflows
keep working. To stop a whole notification, delete or disable its workflow.

## Clearing QC alerts you've reviewed

The database-accuracy email reports only **new / not-yet-reviewed** issues. To
stop being alerted about issues you've reviewed and accepted, run the
**acknowledge-qc** workflow (Actions → acknowledge-qc → Run workflow). In the
categories box, list specific categories (e.g. `missing_OS,missing_DOI`) or type
`ALL` to accept everything; leaving it blank acknowledges nothing (safe default).
Accepted issues are recorded in
`DataCuration/outputs/qc_acknowledged.csv` and won't trigger future emails.
Nothing is acknowledged automatically.

## What each email can and can't tell you

- The **papers-to-check** list depends on the source **DOI** being recorded when
  sequences are added. If a paper's sequences go in without its DOI, it will keep
  appearing on the list.
- The **accuracy** email reports mechanical QC problems (wrong mass, missing
  species, a modification left inside a sequence). It cannot tell whether a
  sequence is the *correct* one for its paper — only a human reading the paper can.
