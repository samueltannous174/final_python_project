def is_emergency(text: str) -> bool:
    t = (text or "").lower()
    triggers = [
        "not breathing","no pulse","severe chest pain","unconscious","stroke",
        "difficulty breathing","seizure","severe bleeding","anaphylaxis","choking","blue lips"
    ]
    return any(k in t for k in triggers)
