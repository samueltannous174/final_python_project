from django.urls import path
from .views import VoiceHelpView, VoicePage, text_help_tts, ask_first_aid, identify_page

urlpatterns = [
    path("voice-help/", VoiceHelpView.as_view(), name="voice_help"),
    path("voice/", VoicePage.as_view(), name="voice_page"),
    path("ask/", ask_first_aid, name="ask_first_aid"),
    path("text-help/", text_help_tts, name="firstaid_text_help"),
    path("identify", identify_page, name="identify"),
]
