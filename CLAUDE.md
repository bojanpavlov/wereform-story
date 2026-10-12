# CLAUDE.md

Guidance for working on this repo. Read this before changing anything.

## What this is

Automatic Instagram stories for WE RE:FORM (Pilates studio, Skopje). Each story shows the day's free spots for the group classes, pulled from the public booking calendar at `https://wereform.mk`. The story goes out to the Business account `wereform_mk`.

Repo: `https://github.com/bojanpavlov/wereform-story` (public, so GitHub Pages can serve the images).
Local folder: `~/Projects/wereform-story`. It is separate from the WordPress repo at `~/Projects/wereform`.

## Hard rules

1. **Always check first, then create, then publish.** Fetch fresh slots from the live calendar, render the image from that data, then publish. Never publish from data read earlier. Bookings change during the day, and a story once went out with numbers that were already out of date.
2. **Never publish without the user's approval.** Publishing posts to a real Instagram account. A manual run (`workflow_dispatch`) counts as publishing. Ask first, unless the user has already asked for that exact story.
3. **Never print or commit secrets.** The Instagram token and account ID live only in GitHub Actions secrets (`IG_ACCESS_TOKEN`, `IG_USER_ID`). Don't put them in files, chat, logs, or commit messages. The same applies to the Meta Graph API Explorer token, which is temporary and must not be shared or saved.
4. **Commit and push only when the user asks.** Each commit message ends with the Co-Authored-By line for Claude.

## Schedule (Skopje time)

| Story | Check (fresh data) | Publish | Covers |
|---|---|---|---|
| Morning | 19:25 the day before | 19:30 the day before | Tomorrow: morning slots 06:00 to 09:59, plus afternoon slots after 15:00 |
| Afternoon | 09:55 the same day | 10:00 the same day | Today: afternoon slots after 15:00 |

- Slots between 10:00 and 15:00 are never shown.
- Days the booking calendar doesn't open (holidays and other closed days) get no story. A day counts as open if it has any slot, free or fully booked. Example: 12 October 2026 is a holiday and has no story.
- A slot with no bookings counts as 5 free places (`MAX_CAPACITY`). Group service ID is 3.
- The schedule runs in UTC, so both UTC times are listed for each check. `run_daily.py` skips a run outside its check window.

## How it works

| File | Job |
|---|---|
| `fetch_availability.py` | Reads the calendar from `wereform.mk` (`admin-ajax.php?action=wpamelia_api&call=/slots`). Sends a project user agent, since the site returns HTTP 406 to Python's default. |
| `run_daily.py` | Decides which story is due, checks the slots, renders the image, and writes the file name to the workflow output. |
| `make_story.py` | Draws the image on `assets/mockup.png`. It erases the old table and date, then draws the date and a table with one row per slot. |
| `publish_story.py` | Waits for the image URL on GitHub Pages, waits for the post time on scheduled runs, then creates and publishes the story through the Instagram Graph API. |
| `cleanup_stories.py` | Removes story images 24 hours after they were committed. Runs hourly through its own workflow. |
| `.github/workflows/daily-story.yml` | Daily story job. Scheduled checks plus a manual run with `kind`, `date`, and `publish_delay_minutes` inputs. |
| `.github/workflows/cleanup-stories.yml` | Hourly cleanup. |
| `docs/` | GitHub Pages site. `docs/stories/` holds the images. `robots.txt` blocks Google and Bing. `index.html` has a noindex tag. |
| `SETUP.md` | Setup steps for GitHub, Pages, Meta, and the token. |

## Running it

- Local check (read-only, safe): `FORCE_KIND=morning FORCE_DATE=2026-10-13 .venv/bin/python run_daily.py` writes an image to `docs/stories/` but publishes nothing. Use the scratchpad for test images, not the repo.
- Read the slots only: `WEREFORM_BASE_URL=https://wereform.mk .venv/bin/python fetch_availability.py 2026-10-13`
- Manual publish: GitHub Actions, "Daily availability story", Run workflow. Only with the user's approval.
- The `.venv` is local only and is gitignored. Install with `pip install -r requirements.txt`.

## Settings and secrets

- GitHub secrets: `IG_ACCESS_TOKEN`, `IG_USER_ID`.
- GitHub variable: `PAGES_BASE_URL` = `https://bojanpavlov.github.io/wereform-story/`.
- Meta app: "Availability story". Use case: "Manage messaging & content on Instagram". Login path: API setup with Facebook login. Token: a System User named `wereform-story`, with access to the app, the studio Page, and the Instagram account. Its token never expires.
- Permissions on the token: `instagram_basic`, `instagram_content_publishing`, `pages_read_engagement`, `pages_show_list`, `business_management`. Messaging permissions were deliberately left out.
- Graph API version: `v21.0` (`GRAPH_VERSION`). Check Meta's changelog before any API change.

## Decisions and why

- **System User token over Instagram Login.** The token doesn't expire, so there's no refresh job. The trade-off is that a leaked token keeps working until it's revoked.
- **Public repo.** GitHub Pages is free only for public repos, and Instagram has to fetch the images from a public URL. Google and Bing are told not to crawl the site.
- **Images deleted after 24 hours.** Instagram fetches each image once, when the story goes out. Deleting the file stops the link working. Git history still holds the file, so anyone can see old images in old commits.
- **Check windows and publish time.** Each run checks about 5 minutes before the post time, then waits. `publish_story.py` waits for the post time before publishing. A manual run can wait a set number of minutes with `publish_delay_minutes`.
- **Unique image names.** Each render gets a new file name, so the Pages CDN can't serve an old image from cache.
- **Unchanged images.** The commit step skips when the image is identical to what's already committed.

## Known issues and open items

- **Font on the server:** the server draws with DejaVu Sans, not Arial, so the text looks slightly different from the local samples. Bundling an Arial-compatible font would fix this.
- **Mockup:** the background is the exported mockup with the old table erased. A clean export would be better.
- **Public repo:** the file names of the story images are visible on GitHub. Google can index the repo page, which the robots rules can't stop.
- **Old stories:** Instagram can't edit or delete a story through the API. A story published with old data has to be removed by hand in the app.
- **Late runs:** GitHub can start scheduled runs a few minutes late. If a run starts after its check window, it skips.
- **Repo history:** deleted images stay in git history. Clearing that would mean rewriting history, which hasn't been done.
- **Live data:** the calendar only shows the next couple of months. Check the live response after any change to the booking plugin.

## Who to ask

The owner is Bojan Pavlov (`bojanpavlov`). Confirm before publishing, changing schedules, or deleting anything.
