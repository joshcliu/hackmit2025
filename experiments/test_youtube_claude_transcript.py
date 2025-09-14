"""
Minimal YouTube -> transcript (LLM-inferred speakers) using Claude.
- Input: YouTube video ID
- Output: Transcript printed to stdout

Requirements:
  pip install yt-dlp pydub anthropic
Env:
  export ANTHROPIC_API_KEY="..."
"""

import os
import sys
import base64
import tempfile
import subprocess
from typing import List
from pydub import AudioSegment
from anthropic import Anthropic
import audioop_lts as audioop

MODEL = "claude-3-5-sonnet-20240620"  # adjust if you prefer a different Claude model
CHUNK_MS = 5 * 60 * 1000  # ~5 minutes per request; tweak for token/size limits

PROMPT = (
    "Transcribe this audio with clear speaker labels (e.g., 'Speaker 1:', 'Speaker 2:'). "
    "Preserve order, punctuation, and paragraphs. If unsure, still tag each turn."
)

def download_audio(video_id: str) -> str:
    """Download YouTube audio as MP3 and return the file path."""
    url = f"https://www.youtube.com/watch?v={video_id}"
    tmpdir = tempfile.mkdtemp(prefix="yt_audio_")
    outfile = os.path.join(tmpdir, "audio.mp3")
    cmd = [
        "yt-dlp", "-f", "bestaudio",
        "--extract-audio", "--audio-format", "mp3",
        "-o", outfile, url
    ]
    subprocess.run(cmd, check=True)
    return outfile

def chunk_audio(path: str, chunk_ms: int = CHUNK_MS) -> List[AudioSegment]:
    audio = AudioSegment.from_file(path)
    return [audio[i:i+chunk_ms] for i in range(0, len(audio), chunk_ms)]

def encode_mp3(seg: AudioSegment) -> bytes:
    """Export a segment to MP3 and return raw bytes."""
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    seg.export(tmp.name, format="mp3")
    with open(tmp.name, "rb") as f:
        data = f.read()
    os.remove(tmp.name)
    return data

def transcribe_chunk_with_claude(client: Anthropic, mp3_bytes: bytes) -> str:
    audio_b64 = base64.b64encode(mp3_bytes).decode("utf-8")
    resp = client.messages.create(
        model=MODEL,
        max_tokens=4000,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": PROMPT},
                {
                    "type": "input_audio",
                    "audio": {"data": audio_b64, "format": "mp3"}
                }
            ]
        }]
    )
    # Claude responses have content as a list of blocks; join any text blocks
    parts = []
    for block in resp.content:
        if block.type == "text":
            parts.append(block.text)
    return "\n".join(parts).strip()

def youtube2transcript_claude(video_id: str) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("Set ANTHROPIC_API_KEY in your environment.")
    client = Anthropic(api_key=api_key)

    audio_path = download_audio(video_id)
    try:
        chunks = chunk_audio(audio_path, CHUNK_MS)
        results = []
        for i, seg in enumerate(chunks, 1):
            print(f"[info] Transcribing chunk {i}/{len(chunks)}...", file=sys.stderr)
            mp3_bytes = encode_mp3(seg)
            text = transcribe_chunk_with_claude(client, mp3_bytes)
            # Optional: prepend a timestamp header per chunk
            results.append(text)
        return "\n\n".join(results)
    finally:
        # best-effort cleanup
        try:
            os.remove(audio_path)
            os.rmdir(os.path.dirname(audio_path))
        except Exception:
            pass

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python youtube2transcripts_claude.py <VIDEO_ID>")
        sys.exit(1)
    vid = sys.argv[1]
    out = youtube2transcript_claude(vid)
    print("==== Transcript ====")
    print(out)
