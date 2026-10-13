"""Delete story images 24 hours after they were committed (the story is published then).
Also deletes the published/ markers after a week; they only matter on the day itself.

Instagram fetches each image once, when the story is published, so the image is
no longer needed after the story's 24-hour life. Once the file is removed from
the repo, GitHub Pages stops serving it.

Usage: python cleanup_stories.py
"""
import glob
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
# (files, maximum age in seconds)
RULES = [
    (os.path.join(HERE, "docs", "stories", "*.png"), 24 * 60 * 60),
    (os.path.join(HERE, "published", "*.txt"), 7 * 24 * 60 * 60),
]


def committed_at(rel_path):
    """Unix time of the commit that added the file, or None if git doesn't know it."""
    out = subprocess.run(
        ["git", "log", "-1", "--format=%ct", "--", rel_path],
        cwd=HERE, capture_output=True, text=True, check=True,
    ).stdout.strip()
    return int(out) if out else None


def main():
    now = time.time()
    removed = []
    for pattern, max_age in RULES:
        for path in sorted(glob.glob(pattern)):
            rel = os.path.relpath(path, HERE)
            added = committed_at(rel)
            if added is None:
                continue
            if now - added > max_age:
                os.remove(path)
                removed.append(rel)

    if removed:
        print("Removed:\n  " + "\n  ".join(removed))
    else:
        print("Nothing to remove.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
