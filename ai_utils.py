import google.generativeai as genai
import json
import streamlit as st
import io

def transcribe_audio(audio_file, api_key):
    """
    Transcribes audio file object using Google Gemini 2.5 Pro.
    Gemini 2.5 Pro is multimodal and can process audio directly.
    """
    if not api_key:
        return None, "API Key missing."

    try:
        genai.configure(api_key=api_key)

        # Read the audio bytes
        # audio_file is a BytesIO-like object from st.audio_input
        audio_bytes = audio_file.getvalue()

        # Determine mime type (st.audio_input produces wav usually, but we can be generic)
        # Gemini expects mime_type.
        mime_type = "audio/wav" # Default for streamlit

        model = genai.GenerativeModel("gemini-2.5-pro")

        prompt = "Listen to this audio and provide a verbatim transcription of the speech."

        response = model.generate_content([
            prompt,
            {"mime_type": mime_type, "data": audio_bytes}
        ])

        return response.text, None
    except Exception as e:
        # Fallback to 1.5 Pro if 2.5 not available (though user asked for 2.5)
        # But user said "do not use 1.5".
        # We will report the error.
        return None, str(e)

def parse_workout_text(text, api_key):
    """
    Uses Google Gemini 2.5 Pro to parse natural language workout text into a JSON object.
    Expected keys: Exercise, Target_Muscle, Region, Target_Sets_Reps, Min_Weight, Max_Weight, Reps, Notes
    """
    if not api_key:
        return None, "API Key missing."

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-pro")

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
        Return only the JSON object, no markdown.
        """

        response = model.generate_content(prompt)
        content = response.text

        # Clean markdown if present
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
             content = content.split("```")[1].split("```")[0]

        data = json.loads(content)
        return data, None
    except Exception as e:
        return None, str(e)
