"""
Given:
- YouTube video_id

Do:
- Fetch transcript using youtube-transcript-api
- Download only the m4a audio (no ffmpeg needed)
- Run pyannote speaker diarization
- For each transcript segment, assign the speaker with max time-overlap
- Return the transcript with `speaker` added

Usage: python assign_speakers_from_audio.py VIDEO_ID
"""

from __future__ import annotations
import os, tempfile, json, sys
from typing import List, Dict, Tuple
from pyannote.audio import Pipeline
from youtube_transcript_api import YouTubeTranscriptApi
import yt_dlp

# Set environment variables to avoid Windows symlink issues
os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'
os.environ['SPEECHBRAIN_CACHE'] = os.path.expanduser('~/.cache/speechbrain_nosymlink')

# Force SpeechBrain to use copy strategy instead of symlinks
import speechbrain.utils.fetching
# Override the symlink strategy to avoid Windows permission issues
original_link_with_strategy = speechbrain.utils.fetching.link_with_strategy

def copy_instead_of_symlink(src, dst, strategy):
    """Copy files instead of creating symlinks to avoid Windows permission issues."""
    import shutil
    if dst.exists():
        return dst
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return dst

speechbrain.utils.fetching.link_with_strategy = copy_instead_of_symlink

def download_m4a(video_id: str) -> str:
    """Download YouTube audio and convert to WAV using scipy."""
    url = f"https://www.youtube.com/watch?v={video_id}"
    tmp = tempfile.mkdtemp(prefix="yt_audio_")
    
    # Download as m4a first (most common format)
    output_template = os.path.join(tmp, "audio.%(ext)s")
    ydl_opts = {
        'format': 'bestaudio[ext=m4a]/bestaudio',
        'outtmpl': output_template,
        'quiet': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    
    # Find the downloaded file
    downloaded_file = None
    for file in os.listdir(tmp):
        if file.startswith("audio."):
            downloaded_file = os.path.join(tmp, file)
            break
    
    if not downloaded_file:
        raise RuntimeError("No audio file found after download")
    
    actual_format = downloaded_file.split('.')[-1].lower()
    print(f"Downloaded audio as: {actual_format}")
    
    # Convert to WAV using a simple approach
    wav_file = os.path.join(tmp, "audio.wav")
    
    # Try moviepy conversion first (handles more formats)
    try:
        return _convert_with_moviepy(downloaded_file, wav_file)
    except Exception as e:
        print(f"MoviePy conversion failed: {e}")
    
    # Try conversion with scipy.io.wavfile for simple cases
    try:
        return _convert_with_scipy(downloaded_file, wav_file)
    except Exception as e:
        print(f"Scipy conversion failed: {e}")
    
    # Try with torchaudio directly (since pyannote uses it)
    try:
        return _convert_with_torchaudio(downloaded_file, wav_file)
    except Exception as e:
        print(f"Torchaudio conversion failed: {e}")
    
    # As last resort, return the original file and let pyannote try to handle it
    print(f"Using original {actual_format} file - pyannote may handle it directly")
    return downloaded_file

def _convert_with_moviepy(input_file: str, output_file: str) -> str:
    """Convert using moviepy."""
    from moviepy.editor import AudioFileClip
    
    # Load audio with moviepy
    audio_clip = AudioFileClip(input_file)
    
    # Convert to mono and set sample rate
    audio_clip = audio_clip.set_fps(16000)
    if audio_clip.nchannels > 1:
        audio_clip = audio_clip.to_mono()
    
    # Export as WAV
    audio_clip.write_audiofile(output_file, verbose=False, logger=None)
    audio_clip.close()
    
    return output_file

def _convert_with_scipy(input_file: str, output_file: str) -> str:
    """Convert using scipy (only works for WAV files)."""
    import shutil
    # If it's already a WAV, just copy it
    if input_file.endswith('.wav'):
        shutil.copy2(input_file, output_file)
        return output_file
    raise RuntimeError("Scipy can only handle WAV files")

def _convert_with_torchaudio(input_file: str, output_file: str) -> str:
    """Convert using torchaudio."""
    import torchaudio
    
    # Try different backends for loading
    backends = ['soundfile', 'sox', 'sox_io']
    
    for backend in backends:
        try:
            torchaudio.set_audio_backend(backend)
            waveform, sample_rate = torchaudio.load(input_file)
            break
        except Exception as e:
            print(f"Backend {backend} failed: {e}")
            continue
    else:
        raise RuntimeError("All torchaudio backends failed")
    
    # Convert to mono if needed
    if waveform.shape[0] > 1:
        waveform = waveform.mean(dim=0, keepdim=True)
    
    # Resample to 16kHz if needed
    if sample_rate != 16000:
        resampler = torchaudio.transforms.Resample(sample_rate, 16000)
        waveform = resampler(waveform)
    
    # Save as WAV
    torchaudio.save(output_file, waveform, 16000)
    return output_file

def _convert_with_librosa(input_file: str, output_file: str) -> str:
    """Convert using librosa."""
    import librosa
    import soundfile as sf
    audio, sr = librosa.load(input_file, sr=16000, mono=True)
    sf.write(output_file, audio, 16000)
    return output_file

def _convert_with_pydub_mp3(input_file: str, output_file: str) -> str:
    """Convert using pydub for MP3 files."""
    from pydub import AudioSegment
    # Only try if it's an MP3 file
    if input_file.endswith('.mp3'):
        audio = AudioSegment.from_mp3(input_file)
        audio = audio.set_channels(1).set_frame_rate(16000)
        audio.export(output_file, format="wav")
        return output_file
    raise RuntimeError("Not an MP3 file")

def _try_direct_copy(input_file: str, output_file: str) -> str:
    """Try to use the file directly if it's already in a compatible format."""
    import shutil
    # If it's already a WAV file, just copy it
    if input_file.endswith('.wav'):
        shutil.copy2(input_file, output_file)
        return output_file
    raise RuntimeError("Not a WAV file")

def diarize(audio_path: str) -> List[Tuple[str, float, float]]:
    """Run pyannote diarization; return list of (speaker_label, start, end)."""
    token = os.environ.get("HUGGINGFACE_TOKEN")
    if not token:
        raise RuntimeError("Set HUGGINGFACE_TOKEN for pyannote pretrained diarizer.")
    pipe = Pipeline.from_pretrained("pyannote/speaker-diarization", use_auth_token=token)
    diar = pipe(audio_path)
    turns: List[Tuple[str, float, float]] = []
    for spk, seg in diar.itertracks(yield_label=True):
        turns.append((spk, float(seg.start), float(seg.end)))
    # Sort by start time for deterministic mapping
    turns.sort(key=lambda t: t[1])
    return turns

def _overlap(a0: float, a1: float, b0: float, b1: float) -> float:
    return max(0.0, min(a1, b1) - max(a0, b0))

def assign_speakers(
    transcript: List[Dict],  # each: {"start": float, "end": float, "text": str, ...}
    turns: List[Tuple[str, float, float]],
) -> List[Dict]:
    """Add 'speaker' to each transcript segment by max-overlap with diarized turns."""
    out: List[Dict] = []
    for seg in transcript:
        s0, s1 = float(seg["start"]), float(seg["end"])
        best_spk, best_olap = None, -1.0
        for spk, t0, t1 in turns:
            ol = _overlap(s0, s1, t0, t1)
            if ol > best_olap:
                best_spk, best_olap = spk, ol
        out.append({**seg, "speaker": best_spk or "SPEAKER_0"})
    # Optional: remap labels to SPEAKER_0/1/2 by first appearance
    remap = {}
    next_id = 0
    for row in out:
        spk = row["speaker"]
        if spk not in remap:
            remap[spk] = f"SPEAKER_{next_id}"
            next_id += 1
        row["speaker"] = remap[spk]
    return out

def fetch_transcript_raw(video_id: str) -> List[Dict]:
    """Fetch transcript using youtube-transcript-api."""
    try:
        ytt_api = YouTubeTranscriptApi()
        fetched = ytt_api.fetch(video_id)
        return fetched.to_raw_data()
    except Exception as e:
        raise SystemExit(f"Error fetching transcript: {e}")

def assign_speakers_for_video(video_id: str) -> List[Dict]:
    """Fetch transcript and assign speakers using audio diarization."""
    print(f"Fetching transcript for video {video_id}...")
    transcript = fetch_transcript_raw(video_id)
    print(f"Retrieved {len(transcript)} transcript segments")
    
    print("Downloading audio...")
    audio = download_m4a(video_id)
    try:
        print("Running speaker diarization...")
        turns = diarize(audio)
        print(f"Found {len(turns)} speaker turns")
        
        print("Assigning speakers to transcript segments...")
        result = assign_speakers(transcript, turns)
        print("Speaker assignment completed!")
        return result
    finally:
        try:
            os.remove(audio)
            os.rmdir(os.path.dirname(audio))
        except Exception:
            pass

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python assign_speakers_from_audio.py VIDEO_ID")
        sys.exit(1)
    
    video_id = sys.argv[1]
    result = assign_speakers_for_video(video_id)
    
    print("\n" + "="*60)
    print(f"SPEAKER ASSIGNMENT RESULTS - VIDEO {video_id}")
    print("="*60)
    print(json.dumps(result, indent=2, ensure_ascii=False))
