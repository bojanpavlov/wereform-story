# Setup: daily availability story

The workflow posts two stories to the Instagram Business account `wereform_mk`:

| Story | Posted at (Skopje) | Covers |
|---|---|---|
| Morning | 19:30 the day before (slots checked at 19:25) | Tomorrow's morning slots (06:00 to 09:59) |
| Afternoon | 10:00 the same day (slots checked at 09:55) | Today's afternoon slots (after 15:00) |

Slots between 10:00 and 15:00 are never shown.

Days the booking calendar doesn't open (holidays and other closed days) get no story. A day counts as open if it has any slot, free or fully booked.

## 1. Create the GitHub repo

1. On github.com, create a new **private** repo named `wereform-story`.
2. In this folder:

   ```bash
   git add .
   git commit -m "Initial daily story pipeline"
   git branch -M main
   git remote add origin https://github.com/<your-user>/wereform-story.git
   git push -u origin main
   ```

3. In the repo: **Settings → Pages** → Source: *Deploy from a branch*, branch `main`, folder `/docs`. Pages then serves the story images.
4. In the repo: **Settings → Secrets and variables → Actions**:
   - **Variables** tab, new variable `PAGES_BASE_URL` = `https://<your-user>.github.io/wereform-story/`
   - **Secrets** tab (values from step 2 below): `IG_USER_ID`, `IG_ACCESS_TOKEN`

## 2. Meta developer app and Instagram

1. Go to developers.facebook.com, create an app of type *Business*.
2. Add the **Instagram** product (Instagram API with Facebook Login or Instagram Platform, whichever Meta offers for your app).
3. Make sure `wereform_mk` is an Instagram **Business** account linked to a Facebook Page where you are an admin.
4. In Meta Business Manager: **System Users** → create a system user and give it access only to the app, the studio Page, and the `wereform_mk` Instagram account. Generate a token with the content permissions from the app's *API setup with Facebook login* screen: `instagram_basic`, `instagram_content_publishing`, `pages_read_engagement`, `pages_show_list`, and `business_management`. Set expiry to **Never**.
5. Copy the token and the Instagram account ID. Save them as the secrets `IG_ACCESS_TOKEN` and `IG_USER_ID`.

Do not put the token in code or in this repo.

## 3. Test once

1. In GitHub: **Actions → Daily availability story → Run workflow**.
2. Choose `kind` = `morning`, a `date` that has free morning slots, and `publish_delay_minutes` (0 publishes at once; 5 waits five minutes after the slots are checked).
3. The run commits the image to `docs/stories/`, then publishes it. Check the story in the Instagram app.
4. A run with a `date` publishes at once and ignores the schedule. Leave `date` empty only to stand in for the scheduled story.

## What runs when

GitHub's own timer is not reliable: it has started runs hours late and skipped others. So an outside scheduler starts the workflow at the exact time, and GitHub's timer is only a backup.

1. **cron-job.org** starts the workflow at 19:25 (`kind` = `morning`) and 09:55 (`kind` = `afternoon`), Skopje time.
2. The run reads the live booking calendar, draws the image, and commits it.
3. The publish step waits for 19:30 or 10:00 and publishes. It then writes `published/<date>-<kind>.txt`.
4. **Backup:** GitHub's timer fires at the same time and again one and two hours later. A run that finds the marker does nothing. If the story isn't out yet, the late run checks fresh and posts.

## 4. Set up cron-job.org

1. **GitHub token.** On github.com: Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate new token. Repository access: *Only select repositories* → `wereform-story`. Repository permissions: **Actions: Read and write**. Nothing else. Note the expiry date; the jobs stop working when the token expires.
2. **Account.** Create a free account on cron-job.org.
3. **Two jobs**, both with these settings:
   - URL: `https://api.github.com/repos/bojanpavlov/wereform-story/actions/workflows/daily-story.yml/dispatches`
   - Request method: `POST`
   - Headers: `Accept: application/vnd.github+json`, `Authorization: Bearer <the token>`, `X-GitHub-Api-Version: 2022-11-28`, `Content-Type: application/json`
   - Time zone: `Europe/Skopje`
   - Morning job: every day at 19:25, body `{"ref":"main","inputs":{"kind":"morning"}}`
   - Afternoon job: every day at 09:55, body `{"ref":"main","inputs":{"kind":"afternoon"}}`
4. A successful call returns HTTP 204. Turn on failure notifications in cron-job.org.

## Settings to check

- **Maximum capacity** is 5 (`MAX_CAPACITY` in `fetch_availability.py`). A slot with no bookings is treated as 5 free places.
- **Group service ID** is 3 (`AMELIA_GROUP_SERVICE_ID`). Check it on the live site.
- **Graph API version** defaults to `v21.0` (`GRAPH_VERSION` in `publish_story.py`). Check Meta's changelog for the current version before the first real post.
- **Live site**: the workflow reads `https://wereform.mk`. Test the endpoint there before relying on it.

## Running locally

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
WEREFORM_BASE_URL=https://wereform.mk .venv/bin/python fetch_availability.py 2026-10-13 morning
FORCE_KIND=morning FORCE_DATE=2026-10-13 .venv/bin/python run_daily.py
```

Rendering needs Arial (macOS) or DejaVu Sans (Linux) for Cyrillic text.
