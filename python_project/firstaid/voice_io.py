from __future__ import annotations

import os
import tempfile
import logging
from typing import Optional

import torch
import whisper

try:
    from pydub import AudioSegment, effects, silence
    _PYDUB_AVAILABLE = True
except Exception:
    _PYDUB_AVAILABLE = False

log = logging.getLogger("firstaid-stt")
if not log.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter("%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"))
    log.addHandler(h)
    log.setLevel(logging.INFO)

def _pick_device() -> str:
    if torch.cuda.is_available():
        return "cuda"
    try:
        if torch.backends.mps.is_available() and torch.backends.mps.is_built():
            return "mps"
    except Exception:
        pass
    return "cpu"

_DEVICE = _pick_device()
_FP16 = (_DEVICE == "cuda")

def _default_model_for_device() -> str:
    env_model = os.getenv("WHISPER_MODEL")
    if env_model:
        return env_model
    if _DEVICE == "cuda":
        return "medium"
    if _DEVICE == "mps":
        return "small"
    return "base"

_MODEL_CANDIDATES = [
    _default_model_for_device(), 
    "small",
    "base",
    "tiny",
]

def _load_model() -> whisper.Whisper:
    last_err: Optional[Exception] = None
    for name in _MODEL_CANDIDATES:
        try:
            log.info("Loading Whisper model '%s' on %s", name, _DEVICE)
            m = whisper.load_model(name, device=_DEVICE)
            log.info("Whisper model ready: %s", name)
            return m
        except Exception as e:
            log.warning("Failed to load model '%s': %s", name, e)
            last_err = e
    raise RuntimeError(f"Could not load any Whisper model from {_MODEL_CANDIDATES}: {last_err}")

_WHISPER = _load_model()

def _clean_audio_if_possible(path: str) -> str:
    """Trim leading/trailing silence & normalize to mono 16k WAV when pydub is available."""
    if not _PYDUB_AVAILABLE:
        return path
    try:
        audio = AudioSegment.from_file(path)
        audio = effects.normalize(audio)

        nonsilent = silence.detect_nonsilent(
            audio,
            min_silence_len=400,
            silence_thresh=audio.dBFS - 16,
            seek_step=10,
        )
        if nonsilent:
            start = max(0, nonsilent[0][0] - 100)  # small preroll
            end = min(len(audio), nonsilent[-1][1] + 100)
            audio = audio[start:end]

        audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        tmp.close()
        audio.export(tmp.name, format="wav")
        return tmp.name
    except Exception as e:
        log.warning("Audio cleanup failed; using original file. Error: %s", e)
        return path

_INITIAL_PROMPT = (
    "You are transcribing short first-aid questions. Users may ask about burns, "
    "cuts, bleeding, CPR, choking, fractures, sprains, shock, allergic reactions, "
    "bandages, and when to call emergency services."
)

def stt_from_file(path: str) -> str | None:

    cleaned = _clean_audio_if_possible(path)

    try:
        result = _WHISPER.transcribe(
            cleaned,
            fp16=_FP16,
            language="en",                     
            condition_on_previous_text=False,  # single-turn queries
            initial_prompt=_INITIAL_PROMPT,    # bias to first-aid domain
            temperature=[0.0, 0.2, 0.4],       # retry schedule for tougher clips
            no_speech_threshold=0.4,           # treat low-energy as silence
            logprob_threshold=-1.0,            # do not aggressively reject
            compression_ratio_threshold=2.4,   # avoid pathological decodes
        )
    except Exception as e:
        log.exception("Whisper transcription failed: %s", e)
        return None
    finally:
        if cleaned != path:
            try:
                os.remove(cleaned)
            except Exception:
                pass

    text = (result.get("text") or "").strip()
    if not text:
        return None

    # lightweight normalization for common mishears
    return _normalize(text)

_COMMON_FIXES = {
    "i'm burned": "i am burned",
    "i got burned": "i am burned",
    "if i am burn": "if i am burned",
    "if i'm burn": "if i am burned",
    "first aide": "first aid",
    "cprr": "cpr",
}

def _normalize(t: str) -> str:
    s = t.strip()
    low = s.lower()
    for bad, good in _COMMON_FIXES.items():
        if bad in low:
            low = low.replace(bad, good)
    if low:
        low = low[0].upper() + low[1:]
    return low
