import openai
import json
import streamlit as st

def transcribe_audio(audio_file, api_key):
    """
    Transcribes audio file object using OpenAI Whisper API.
    """
    if not api_key:
        return None, "API Key missing."

    client = openai.OpenAI(api_key=api_key)
    try:
        # Streamlit audio_input returns a BytesIO-like object.
        # OpenAI API expects a file-like object with a name.
        audio_file.name = "input.wav"
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="text"
        )
        return transcript, None
    except Exception as e:
        return None, str(e)

def parse_workout_text(text, api_key):
    """
    Uses OpenAI Chat Completion to parse natural language workout text into a JSON object.
    Expected keys: Exercise, Target_Muscle, Region, Target_Sets_Reps, Min_Weight, Max_Weight, Reps, Notes
    """
    if not api_key:
        return None, "API Key missing."

    client = openai.OpenAI(api_key=api_key)

    prompt = f"""
    Extract workout data from the following text into a JSON object.
    Text: "{text}"

    The JSON should have these keys:
    - "Exercise": (string) name of exercise
    - "Target_Muscle": (string) primary muscle group worked
    - "Region": (string) e.g. Upper Body, Lower Body, Core, Full Body
    - "Target_Sets_Reps": (string) e.g. "3x10", "4 sets of 8"
    - "Min_Weight": (number) minimum weight used (in kg/lbs, just number)
    - "Max_Weight": (number) maximum weight used
    - "Reps": (string or number) total reps or reps per set
    - "Notes": (string) any specific notes mentioned

    If any field is not mentioned, infer it if obvious (like Muscle/Region for common exercises), or set to null/empty string.
    Return only the JSON object.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo", # Cost effective
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        content = response.choices[0].message.content
        # Clean markdown if present
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]

        data = json.loads(content)
        return data, None
    except Exception as e:
        return None, str(e)
