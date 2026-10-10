# Setup: daily availability story

The workflow posts two stories to the Instagram Business account `wereform_mk`:

| Story | Posted at (Skopje) | Covers |
|---|---|---|
| Morning | 19:00 the day before | Tomorrow's morning slots (06:00 to 09:59) |
| Afternoon | 14:00 the same day | Today's afternoon slots (after 15:00) |

Slots between 10:00 and 15:00 are never shown.

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
4. In Meta Business Manager: **System Users** → create a system user with admin access to the app and the Page → generate a token with permissions to publish content to Instagram (`instagram_content_publish` and the Page/Instagram permissions listed in the app).
5. Copy the token and the Instagram account ID. Save them as the secrets `IG_ACCESS_TOKEN` and `IG_USER_ID`.

Do not put the token in code or in this repo.

## 3. Test once

1. In GitHub: **Actions → Daily availability story → Run workflow**.
2. Choose `kind` = `morning`, and a `date` that has free morning slots.
3. The run commits the image to `docs/stories/`, then publishes it. Check the story in the Instagram app.
4. If the run passes, it will repeat at 19:00 and 14:00 every day.

## What runs when

GitHub cron uses UTC and does not know about daylight saving. The workflow fires at both UTC hours for 19:00 and 14:00, and `run_daily.py` exits quietly unless the Skopje hour matches. GitHub can also start scheduled runs a few minutes late.

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
