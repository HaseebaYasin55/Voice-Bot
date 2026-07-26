import io
import json
import os
import streamlit as st
from datetime import datetime
import requests
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY", "")
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY") or st.secrets.get("DEEPGRAM_API_KEY", "")

ASR_MODEL = "whisper-large-v3"          
LLM_MODEL = "llama-3.3-70b-versatile"  
DEEPGRAM_TTS_MODEL = "aura-2-thalia-en"

##system prompt
SYSTEM_PROMPT = (
   "You are a conversational AI voice assistant that sounds friendly, calm, and natural. "
    "Respond like a helpful human assistant rather than a chatbot. "
    "Keep replies brief and easy to listen to, unless the user requests a detailed explanation. "
    "Be polite, engaging, and conversational while maintaining accuracy. "
    "Avoid markdown, lists, or unnecessary punctuation that would sound awkward when spoken. "
    "Use available tools whenever they can improve the accuracy of your response."
)

##Time tool
def get_current_time() -> str:
    return datetime.now().strftime("It is %A, %B %d, %Y, %I:%M %p")

#Weather tool
def get_weather(city: str) -> str:
    try:
        geo = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 1},
            timeout=5,
        ).json()
        if not geo.get("results"):
            return f"I couldn't find a location called {city}."
        loc = geo["results"][0]

        weather = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": loc["latitude"],
                "longitude": loc["longitude"],
                "current_weather": True,
            },
            timeout=5,
        ).json()
        temp = weather["current_weather"]["temperature"]
        wind = weather["current_weather"]["windspeed"]
        return f"It's currently {temp}°C in {loc['name']} with wind speeds of {wind} km/h."
    except Exception as e:
        return f"Sorry, I couldn't fetch the weather right now ({e})."


TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get the current date and time.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather for a given city.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "e.g. 'Islamabad' or 'Paris'"}
                },
                "required": ["city"],
            },
        },
    },
]

TOOL_REGISTRY = {
    "get_current_time": get_current_time,
    "get_weather": get_weather,
}

##Speech-to-Text: (Groq Whisper)
def transcribe_audio(audio_bytes: bytes, filename: str = "audio.wav") -> str:
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is not set. Add it to your .env file.")

    client = Groq(api_key=GROQ_API_KEY)
    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = filename 

    transcription = client.audio.transcriptions.create(
        file=audio_file,
        model=ASR_MODEL,
        response_format="text",
        language="en",
    )
    text = transcription if isinstance(transcription, str) else transcription.text
    return text.strip()


##LLM + tool-calling
def get_agent_reply(conversation_history: list[dict]) -> str:
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is not set. Add it to your .env file.")

    client = Groq(api_key=GROQ_API_KEY)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + conversation_history

    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
        tools=TOOL_SCHEMAS,
        tool_choice="auto",
        temperature=0.7,
        max_tokens=300,
    )
    msg = response.choices[0].message

    if msg.tool_calls:
        messages.append(msg)
        for call in msg.tool_calls:
            fn = TOOL_REGISTRY.get(call.function.name)
            args = json.loads(call.function.arguments or "{}")
            result = fn(**args) if fn else f"Error: unknown tool '{call.function.name}'"
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "name": call.function.name,
                    "content": str(result),
                }
            )

        follow_up = client.chat.completions.create(
            model=LLM_MODEL, messages=messages, temperature=0.7, max_tokens=300
        )
        return follow_up.choices[0].message.content.strip()

    return msg.content.strip()

##Text-to-Speech: (Deepgram Aura-2)
def synthesize_speech(text: str) -> bytes:
    return _synthesize_deepgram(text)

##Send text to deepgram and return audio
def _synthesize_deepgram(text: str) -> bytes:
    if not DEEPGRAM_API_KEY:
        raise RuntimeError("DEEPGRAM_API_KEY is not set. Add it to your .env file.")

    url = f"https://api.deepgram.com/v1/speak?model={DEEPGRAM_TTS_MODEL}"
    headers = {"Authorization": f"Token {DEEPGRAM_API_KEY}", "Content-Type": "application/json"}
    resp = requests.post(url, headers=headers, json={"text": text}, timeout=30)
    resp.raise_for_status()
    return resp.content


##Voice -> Text -> AI -> Speech
def run_turn(audio_bytes: bytes, conversation_history: list[dict]) -> dict:
    user_text = transcribe_audio(audio_bytes)
    if not user_text:
        fallback = "I didn't catch that, could you try again?"
        return {
            "user_text": "",
            "assistant_text": fallback,
            "assistant_audio": synthesize_speech(fallback),
        }

    conversation_history.append({"role": "user", "content": user_text})
    assistant_text = get_agent_reply(conversation_history)
    conversation_history.append({"role": "assistant", "content": assistant_text})
    assistant_audio = synthesize_speech(assistant_text)

    return {
        "user_text": user_text,
        "assistant_text": assistant_text,
        "assistant_audio": assistant_audio,
    }