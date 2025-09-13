"""
Test script for youtube-transcript-api.

Usage examples:
python experiments/test_youtube_transcript_api.py dQw4w9WgXcQ

Notes:
- This script performs network requests to YouTube to retrieve transcripts.
- Provide a valid YouTube video ID (the value after v= in a YouTube URL).
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import List, Dict, Any

from youtube_transcript_api import YouTubeTranscriptApi


def fetch_transcript_raw(video_id: str) -> Dict[str, Any]:
    """Fetch transcript using the class-based API and return both raw data and metadata.

    Returns a dict with keys: raw (list of dicts), meta (dict).
    """
    try:
        ytt_api = YouTubeTranscriptApi()
        fetched = ytt_api.fetch(video_id)
    except Exception as e:  # noqa: BLE001
        raise SystemExit(f"Error fetching transcript: {e}")

    # Convert to list[dict] with keys: text, start, duration
    raw = fetched.to_raw_data()
    meta = {
        "video_id": getattr(fetched, "video_id", video_id),
        "language": getattr(fetched, "language", None),
        "language_code": getattr(fetched, "language_code", None),
        "is_generated": getattr(fetched, "is_generated", None),
    }
    return {"raw": raw, "meta": meta}


def print_summary(transcript: List[Dict[str, Any]], preview_lines: int = 10) -> None:
    total_secs = sum(item.get("duration", 0.0) for item in transcript)
    total_chars = sum(len(item.get("text", "")) for item in transcript)
    total_items = len(transcript)

    print("\nTranscript summary:")
    print(f"  segments: {total_items}")
    print(f"  total duration (approx): {total_secs:.1f}s")
    print(f"  total characters: {total_chars}")

    print("\nFirst lines:")
    for i, item in enumerate(transcript[:preview_lines], start=1):
        start = item.get("start", 0.0)
        dur = item.get("duration", 0.0)
        text = item.get("text", "").replace("\n", " ")
        print(f"  {i:02d} [{start:6.2f}s +{dur:5.2f}s] {text}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Test youtube-transcript-api (class-based API) with a YouTube video ID.")
    parser.add_argument("video_id", help="YouTube video ID (the value after v= in the URL)")
    parser.add_argument(
        "--preview-lines",
        type=int,
        default=1000,
        help="How many transcript lines to preview (default: 1000)",
    )

    args = parser.parse_args()

    result = fetch_transcript_raw(args.video_id)
    meta = result["meta"]
    transcript_raw = result["raw"]

    print("Fetched transcript metadata:")
    print(json.dumps(meta, ensure_ascii=False))

    print_summary(transcript_raw, preview_lines=args.preview_lines)


if __name__ == "__main__":
    main()
