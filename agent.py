import io
import json
import os
import time
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

# Hard timeout for every Groq API call. The SDK's default is 600s with
# automatic retries on connection errors, which is what was causing the
# "minutes" of hanging -- any network hiccup would silently retry instead
# of failing fast. 20s is generous for both Whisper and Llama on Groq's
# infra (normally sub-2-second); if it's actually taking that long, we want
# a fast, visible failure instead of a silent multi-minute stall.
GROQ_TIMEOUT_SECONDS = 20.0
GROQ_MAX_RETRIES = 1

@st.cache_resource
def get_groq_client():
    return Groq(api_key=GROQ_API_KEY, timeout=GROQ_TIMEOUT_SECONDS, max_retries=GROQ_MAX_RETRIES)

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
            timeout=(3, 5),
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
            timeout=(3, 5),
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

    client = get_groq_client()
    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = filename 

    t0 = time.perf_counter()
    transcription = client.audio.transcriptions.create(
        file=audio_file,
        model=ASR_MODEL,
        response_format="text",
        language="en",
    )
    print(f"DEBUG transcribe_audio: {time.perf_counter() - t0:.2f}s, {len(audio_bytes)} bytes")
    text = transcription if isinstance(transcription, str) else transcription.text
    return text.strip()


##LLM + tool-calling
def get_agent_reply(conversation_history: list[dict]) -> str:
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is not set. Add it to your .env file.")

    client = get_groq_client()
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + conversation_history

    t0 = time.perf_counter()
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
        tools=TOOL_SCHEMAS,
        tool_choice="auto",
        temperature=0.7,
        max_tokens=300,
    )
    print(f"DEBUG llm_call_1: {time.perf_counter() - t0:.2f}s")
    msg = response.choices[0].message

    if msg.tool_calls:
        # Append a plain dict (not the raw SDK message object) -- the SDK
        # object doesn't serialize correctly when sent back in the next
        # chat.completions.create call, which was silently raising and
        # aborting the whole turn before any assistant reply was produced.
        messages.append(
            {
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [
                    {
                        "id": call.id,
                        "type": "function",
                        "function": {
                            "name": call.function.name,
                            "arguments": call.function.arguments,
                        },
                    }
                    for call in msg.tool_calls
                ],
            }
        )

        for call in msg.tool_calls:
            fn = TOOL_REGISTRY.get(call.function.name)
            try:
                args = json.loads(call.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            t_tool = time.perf_counter()
            try:
                result = fn(**args) if fn else f"Error: unknown tool '{call.function.name}'"
            except Exception as e:
                result = f"Error running tool '{call.function.name}': {e}"
            print(f"DEBUG tool_call [{call.function.name}]: {time.perf_counter() - t_tool:.2f}s")
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "name": call.function.name,
                    "content": str(result),
                }
            )

        t1 = time.perf_counter()
        follow_up = client.chat.completions.create(
            model=LLM_MODEL, messages=messages, temperature=0.7, max_tokens=300
        )
        print(f"DEBUG llm_call_2: {time.perf_counter() - t1:.2f}s")
        return (follow_up.choices[0].message.content or "").strip()

    return (msg.content or "").strip()

##Text-to-Speech: (Deepgram Aura-2)
def synthesize_speech(text: str) -> bytes:
    return _synthesize_deepgram(text)

##Send text to deepgram and return audio
def _synthesize_deepgram(text: str) -> bytes:
    if not DEEPGRAM_API_KEY:
        raise RuntimeError("DEEPGRAM_API_KEY is not set. Add it to your .env file.")

    url = f"https://api.deepgram.com/v1/speak?model={DEEPGRAM_TTS_MODEL}"
    headers = {"Authorization": f"Token {DEEPGRAM_API_KEY}", "Content-Type": "application/json"}
    t0 = time.perf_counter()
    resp = requests.post(url, headers=headers, json={"text": text}, timeout=(3, 15))
    print(f"DEBUG deepgram_tts: {time.perf_counter() - t0:.2f}s, {len(text)} chars")
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