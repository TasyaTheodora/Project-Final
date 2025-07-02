### File: app/utils.py
import os
import re
import openai

# Pastikan OPENAI_API_KEY Anda sudah di-set pada environment
openai.api_key = os.getenv("OPENAI_API_KEY")


def estimate_virality(transcript: str) -> float:
    """
    Menggunakan OpenAI untuk memperkirakan seberapa viral konten berdasar transkrip.
    Mengembalikan skor 0.0 - 100.0
    """
    prompt = (
        "Rate the viral potential of the following video transcript on a scale of 0 to 100, "
        "where 0 is not viral at all and 100 is extremely viral:\n\n" + transcript
    )
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an assistant that rates video transcripts for viral potential."},
                {"role": "user",   "content": prompt}
            ],
            temperature=0.0,
            max_tokens=16
        )
        text = resp.choices[0].message.content.strip()
        # ambil angka pertama yang muncul
        match = re.search(r"\d+\.?\d*", text)
        return float(match.group()) if match else 0.0
    except Exception as e:
        print("Error estimating virality:", e)
        return 0.0