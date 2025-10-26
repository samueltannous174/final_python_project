import os
import re
import time
import base64
import tempfile
import logging
from typing import Optional

import requests
from django.views import View
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts import render
from django.views.decorators.http import require_POST

from .voice_io import stt_from_file
from .tts_utils import tts_wav_bytes
from .haystack_setup import run_rag

log = logging.getLogger("firstaid-views")


def _print_user_and_answer(user_text: str, answer: Optional[str]) -> None:
    try:
        print("\n" + "-" * 64)
        print(f"User said: {user_text}")
        if answer is None:
            print("Model answer: <none>")
        else:
            print(f"Model answer: {answer}")
        print("-" * 64 + "\n")
    except Exception:
        pass

    if answer is None:
        log.info("User: %s | Answer: <none>", user_text)
    else:
        log.info("User: %s | Answer: %s", user_text, answer)


class VoicePage(View):
    def get(self, request):
        return render(request, "firstaid/voice.html")


@method_decorator(csrf_exempt, name="dispatch")
class VoiceHelpView(View):
    def post(self, request):
        if "audio" not in request.FILES:
            return JsonResponse({"error": "file field 'audio' required"}, status=400)

        f = request.FILES["audio"]
        suffix = os.path.splitext(f.name)[1] or ".webm"

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            for chunk in f.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name

        try:
            st = time.time()
            user_text = stt_from_file(tmp_path)
        finally:
            try:
                os.remove(tmp_path)
            except Exception:
                pass

        if not user_text:
            log.warning("Speech not recognized.")
            return JsonResponse({"error": "speech not recognized"}, status=400)

        _print_user_and_answer(user_text, None)

        try:
            answer = run_rag(user_text)
        except Exception as e:
            log.exception("run_rag failed: %s", e)
            return JsonResponse({"error": "internal error running RAG"}, status=500)

        _print_user_and_answer(user_text, answer)

        try:
            audio = tts_wav_bytes(answer or "")
        except Exception as e:
            log.exception("tts_wav_bytes failed: %s", e)
            return JsonResponse({"answer": answer or ""}, status=200)

        dur_ms = int((time.time() - st) * 1000)
        log.debug("VoiceHelp end-to-end duration: %d ms", dur_ms)
        return HttpResponse(audio, content_type="audio/wav")


@csrf_exempt
def ask_first_aid(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    q = (request.POST.get("q") or "").strip()
    if not q:
        return JsonResponse({"error": "q required"}, status=400)

    st = time.time()
    try:
        answer = run_rag(q)
    except Exception as e:
        log.exception("run_rag failed: %s", e)
        return JsonResponse({"error": "internal error running RAG"}, status=500)

    _print_user_and_answer(q, answer)

    dur_ms = int((time.time() - st) * 1000)
    log.debug("ask_first_aid duration: %d ms", dur_ms)
    return JsonResponse({"question": q, "answer": answer})


@csrf_exempt
@require_POST
def text_help_tts(request):
    q = (request.POST.get("q") or "").strip()
    if not q:
        return JsonResponse({"error": "q required"}, status=400)

    st = time.time()
    try:
        answer = run_rag(q)
    except Exception as e:
        log.exception("run_rag failed: %s", e)
        return JsonResponse({"error": "internal error running RAG"}, status=500)

    _print_user_and_answer(q, answer)

    try:
        audio = tts_wav_bytes(answer or "")
        dur_ms = int((time.time() - st) * 1000)
        log.debug("text_help_tts duration: %d ms", dur_ms)
        return HttpResponse(audio, content_type="audio/wav")
    except Exception as e:
        log.exception("tts_wav_bytes failed: %s", e)
        return JsonResponse({"error": "tts failed", "answer": answer or ""}, status=500)


def extract_medicine_names(text: str) -> list[str]:
    matches = re.findall(
        r'^\s*\d+\.\s*(?:\*\*([^*]+)\*\*|([^-–:\n]+))',
        text,
        flags=re.M,
    )
    return [(a or b).strip().rstrip(".") for a, b in matches if (a or b)]


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"


@csrf_exempt
def identify_page(request):
    result, error = None, None

    if request.method == "POST" and "image" in request.FILES:
        f = request.FILES["image"]
        mime = getattr(f, "content_type", "image/jpeg")
        raw = f.read()
        if not raw:
            error = "Empty file."
        else:
            if not OPENROUTER_API_KEY:
                return render(
                    request,
                    "firstaid/identify.html",
                    {"result": None, "error": "Missing OPENROUTER_API_KEY"},
                )

            img_b64 = base64.b64encode(raw).decode("utf-8")
            data_url = f"data:{mime};base64,{img_b64}"

            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            }

            prompt = "Identify the medicine(s) in this image. Give name and strength."

            payload = {
                "model": MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": data_url}},
                        ],
                    }
                ],
                "temperature": 0.1,
            }

            try:
                r = requests.post(ENDPOINT, headers=headers, json=payload, timeout=60)
                if r.ok:
                    result = r.json()["choices"][0]["message"]["content"]
                    names = extract_medicine_names(result)
                    print(names)
                else:
                    error = r.text[:500]
            except Exception as e:
                error = str(e)

    return render(request, "firstaid/identify.html", {"result": result, "error": error})
