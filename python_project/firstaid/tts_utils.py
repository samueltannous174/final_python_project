import io, asyncio
from pydub import AudioSegment
import edge_tts

def tts_wav_bytes(text: str) -> bytes:
    async def _synth():
        tts = edge_tts.Communicate(text, voice="en-US-JennyNeural")
        mp3 = b""
        async for chunk in tts.stream():
            if chunk["type"] == "audio":
                mp3 += chunk["data"]
        audio = AudioSegment.from_file(io.BytesIO(mp3), format="mp3")
        buf = io.BytesIO()
        audio.export(buf, format="wav")
        return buf.getvalue()
    return asyncio.run(_synth())
