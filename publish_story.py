"""Publish a story image through the Instagram Graph API.

The image must already be committed under docs/stories/ so GitHub Pages serves
it. Instagram fetches it from that public URL, so this script first waits
until the URL answers.

Needed environment variables:
  IG_USER_ID        Instagram Business account ID (numeric)
  IG_ACCESS_TOKEN   System User token with permission to publish to the account
  PAGES_BASE_URL    Public base of the Pages site, e.g. https://<user>.github.io/wereform-story/
  GRAPH_VERSION     optional, default v21.0 (check Meta's changelog before first run)

Usage: python publish_story.py docs/stories/2026-10-13-morning.png
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

GRAPH_VERSION = os.environ.get("GRAPH_VERSION", "v21.0")
GRAPH = f"https://graph.facebook.com/{GRAPH_VERSION}"


def public_url(local_path):
    base = os.environ["PAGES_BASE_URL"].rstrip("/") + "/"
    rel = local_path.replace("\\", "/")
    if "docs/" in rel:
        rel = rel.split("docs/", 1)[1]
    return base + rel


def wait_until_live(url, attempts=20, delay=15):
    for _ in range(attempts):
        try:
            with urllib.request.urlopen(url, timeout=20) as resp:
                if resp.status == 200:
                    return
        except urllib.error.URLError:
            pass
        time.sleep(delay)
    raise RuntimeError(f"Image not reachable at {url} after {attempts} tries")


def graph_post(path, fields):
    data = urllib.parse.urlencode(fields).encode()
    req = urllib.request.Request(f"{GRAPH}/{path}", data=data, method="POST")
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.load(resp)


def graph_get(path, fields):
    url = f"{GRAPH}/{path}?{urllib.parse.urlencode(fields)}"
    with urllib.request.urlopen(url, timeout=30) as resp:
        return json.load(resp)


def publish(image_url, ig_user_id, token):
    container = graph_post(f"{ig_user_id}/media", {
        "image_url": image_url,
        "media_type": "STORIES",
        "access_token": token,
    })
    container_id = container["id"]

    # Instagram processes the image first; publish only when it reports FINISHED.
    for _ in range(20):
        status = graph_get(container_id, {"fields": "status_code", "access_token": token})
        if status.get("status_code") == "FINISHED":
            break
        if status.get("status_code") == "ERROR":
            raise RuntimeError(f"Instagram could not process the image: {status}")
        time.sleep(10)
    else:
        raise RuntimeError("Container did not reach FINISHED in time")

    result = graph_post(f"{ig_user_id}/media_publish", {
        "creation_id": container_id,
        "access_token": token,
    })
    return result.get("id")


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    ig_user_id = os.environ["IG_USER_ID"]
    token = os.environ["IG_ACCESS_TOKEN"]
    url = public_url(argv[0])
    wait_until_live(url)
    media_id = publish(url, ig_user_id, token)
    print(f"Published story {media_id} from {url}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
