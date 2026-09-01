"""
One-time migration: push your local flashcards_data.json into Supabase.

What it does:
  1. Reads flashcards_data.json
  2. Uploads each inline base64 image to the 'flashcard-images' Storage bucket
  3. Replaces answer_image with the public Storage URL
  4. Upserts all cards into the 'flashcards' table

Run it ONCE, after you've created the table + bucket (supabase_setup.sql).

Usage (from the flashcard-ppl-main folder):
    # credentials are read from .streamlit/secrets.toml, OR from env vars
    #   set SUPABASE_URL=...   set SUPABASE_KEY=...
    python migrate_to_supabase.py
"""

import base64
import json
import os
import uuid
from pathlib import Path

from supabase import create_client

FLASHCARDS_JSON = "flashcards_data.json"
STORAGE_BUCKET = "flashcard-images"


def load_credentials():
    """Read Supabase URL/key from env vars, falling back to .streamlit/secrets.toml."""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if url and key:
        return url, key

    secrets_path = Path(".streamlit") / "secrets.toml"
    if secrets_path.exists():
        try:
            import tomllib  # Python 3.11+
            data = tomllib.loads(secrets_path.read_text(encoding="utf-8"))
        except ModuleNotFoundError:
            # Minimal fallback parser for two simple KEY = "value" lines
            data = {}
            for line in secrets_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    data[k.strip()] = v.strip().strip('"').strip("'")
        url = data.get("SUPABASE_URL")
        key = data.get("SUPABASE_KEY")

    if not url or not key:
        raise SystemExit(
            "Missing credentials. Set SUPABASE_URL and SUPABASE_KEY env vars, "
            "or fill in .streamlit/secrets.toml."
        )
    return url, key


def split_data_uri(data_uri):
    """Return (raw_bytes, file_ext) from a 'data:image/...;base64,...' string."""
    header, encoded = data_uri.split(",", 1)
    # header looks like: data:image/jpg;base64
    mime = header.split(":", 1)[1].split(";", 1)[0]   # image/jpg
    ext = mime.split("/", 1)[1].lower()
    if ext == "jpeg":
        ext = "jpg"
    return base64.b64decode(encoded), ext, mime


def main():
    url, key = load_credentials()
    supabase = create_client(url, key)
    storage = supabase.storage.from_(STORAGE_BUCKET)

    with open(FLASHCARDS_JSON, "r", encoding="utf-8") as f:
        cards = json.load(f)

    print(f"Loaded {len(cards)} cards from {FLASHCARDS_JSON}")

    uploaded = 0
    for card in cards:
        img = card.get("answer_image")
        if isinstance(img, str) and img.startswith("data:image"):
            raw, ext, mime = split_data_uri(img)
            object_path = f"{uuid.uuid4().hex}.{ext}"
            storage.upload(object_path, raw, {"content-type": mime})
            card["answer_image"] = storage.get_public_url(object_path)
            uploaded += 1
            print(f"  card {card['id']}: uploaded image -> {object_path}")

        # Ensure history is a list (jsonb column)
        if card.get("history") is None:
            card["history"] = []

    print(f"Uploaded {uploaded} images to Storage.")

    # Upsert in chunks to stay well under request limits
    chunk = 100
    for i in range(0, len(cards), chunk):
        supabase.table("flashcards").upsert(cards[i:i + chunk]).execute()
    print(f"Upserted {len(cards)} cards into the 'flashcards' table. Done!")


if __name__ == "__main__":
    main()
