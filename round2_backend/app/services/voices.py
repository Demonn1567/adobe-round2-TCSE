import os
import requests

def list_voices(locale: str | None = None, contains: str | None = None):
    provider = os.getenv("TTS_PROVIDER", "openai").lower()

    if provider == "openai":
        voices = [{"name": "alloy", "shortName": "alloy", "locale": "multilingual"}]
        return _filter(voices, locale, contains)

    key = os.getenv("AZURE_SPEECH_KEY")
    region = os.getenv("AZURE_SPEECH_REGION", "eastus")
    if not key:
        return []

    url = f"https://{region}.tts.speech.microsoft.com/cognitiveservices/voices/list"
    headers = {"Ocp-Apim-Subscription-Key": key}
    r = requests.get(url, headers=headers, timeout=20)
    r.raise_for_status()

    arr = r.json()
    voices = [
        {
            "name": v.get("DisplayName") or v.get("ShortName"),
            "shortName": v.get("ShortName"),
            "locale": v.get("Locale"),
        }
        for v in arr
    ]
    return _filter(voices, locale, contains)

def _filter(voices, locale, contains):
    out = voices
    if locale:
        lc = locale.lower()
        out = [v for v in out if (v.get("locale") or "").lower().startswith(lc)]
    if contains:
        s = contains.lower()
        out = [v for v in out if s in (v.get("name","").lower() + v.get("shortName","").lower())]
    return out
