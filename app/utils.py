# file: app/utils.py
import os
import re
import openai

# Pastikan OPENAI_API_KEY sudah di-set di environment
openai.api_key = os.getenv("OPENAI_API_KEY")

def transcribe_video(video_path: str, verbose: bool = False) -> dict:
    """
    Transkrip audio dari video menggunakan OpenAI Whisper API.
    Mengembalikan dict dengan key 'text' dan (opsional) 'segments'.
    """
    with open(video_path, "rb") as audio_file:
        result = openai.Audio.transcribe("whisper-1", audio_file)
    if verbose:
        print("↪ Transcript:", result)
    # Jika API hanya mengembalikan 'text', kita bungkus jadi segments 1 klip penuh
    text = result.get("text", "")
    segments = result.get("segments", [{"start": 0.0, "end": 0.0, "text": text}])
    return {"text": text, "segments": segments}

def estimate_virality(transcript: str) -> float:
    """
    Rate viral potential 0–100 dengan ChatCompletion.
    """
    prompt = (
        "Rate the viral potential of the following video transcript on a scale of 0 to 100, "
        "where 0 is not viral at all and 100 is extremely viral:\n\n"
        + transcript
    )
    resp = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role":"user","content":prompt}],
        temperature=0.7,
        max_tokens=10,
    )
    content = resp.choices[0].message.content.strip()
    # ekstrak angka
    m = re.search(r"(\d+\.?\d*)", content)
    score = float(m.group(1)) if m else 0.0
    return max(0.0, min(score, 100.0))
