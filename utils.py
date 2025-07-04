# file: utils.py
import os
import re
from openai import OpenAI

# either read from env or hard-code
api_key = os.getenv("OPENAI_API_KEY")  # make sure you set this in your shell
# api_key = "sk-…your key…"           # or paste it here (not recommended for public repos)

client = OpenAI(api_key=api_key)

def transcribe_video(video_path: str, verbose: bool = False) -> dict:
    """
    Transkrip audio dari video menggunakan OpenAI Whisper API (v1).
    Mengembalikan dict dengan key 'text' dan 'segments'.
    """
    with open(video_path, "rb") as f:
        # Panggil endpoint transcriptions baru
        resp = client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            response_format="verbose_json"
        )

    if verbose:
        print("⏳ Transcript:", resp)

    # Ubah ComplexModel ke dict
    data = resp.to_dict()
    text = data.get("text", "")
    segments = data.get(
        "segments", [{"start": 0.0, "end": 0.0, "text": text}]
    )

    return {"text": text, "segments": segments}


def estimate_virality(transcript: str) -> float:
    """
    Rate viral potential 0–100 dengan ChatCompletion.
    """
    prompt = (
        "Rate the viral potential of the following video transcript on a scale of 0 to 100, "
        "where 0 is not viral at all and 100 is extremely viral:\n\n" + transcript
    )
    # Atur parameter sesuai kebutuhan
    resp = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    # Ambil skor di pesan assistant
    content = resp.choices[0].message.content.strip()
    try:
        score = float(re.search(r"\d+(?:\.\d+)?", content).group())
    except Exception:
        score = 0.0
    return max(0.0, min(100.0, score))
