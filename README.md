# 🎙️ VoiceBot — Conversational Voice AI Agent

A **voice-first AI agent** built with **Streamlit**, powered by **Groq** (speech-to-text + LLM reasoning + tool-calling) and **Deepgram** (text-to-speech), that lets you *talk* to an assistant instead of typing — you speak, it transcribes, thinks, decides whether it needs a tool, and replies back to you in natural-sounding audio.

---

# Key Features

- Full voice-in / voice-out loop — no typing required
- Multi-tool calling AI agent (time + weather lookups, extensible to more)
- Real speech-to-text transcription via Groq Whisper (not guessed captions)
- Natural-sounding text-to-speech replies via Deepgram Aura-2
- Persistent multi-turn conversation history within a session
- Chat-bubble transcript view alongside the voice interaction
- One-click **Clear Chat** to reset the conversation
- Simple, elegant, dark-themed Streamlit interface with an animated mic

---

# Project Structure

```
voice-bot/
│
├── app.py
├── agent.py
├── requirements.txt
├── .gitignore
└── README.md
```

---

# How the Agent Works

The agent follows this flow:

1. User clicks the mic and speaks; clicking again stops the recording.
2. The recorded audio is sent to **Groq Whisper** (`whisper-large-v3`) for transcription.
3. The transcribed text is appended to the conversation history and sent to the **Groq LLM** (`llama-3.3-70b-versatile`), along with two tool definitions.
4. The model decides, turn by turn, whether it needs to call a tool (e.g. current time or weather) to answer accurately.
5. If a tool is called, its result is fed back to the model, which then produces a final natural-language reply.
6. The reply text is sent to **Deepgram Aura-2** for text-to-speech synthesis.
7. The synthesized audio is auto-played back to the user, and both the user's and the agent's turns are added to the on-screen chat history.

This is **tool use / function calling** — the agent isn't a fixed script; the LLM is given a description of each tool (name, purpose, expected arguments) and decides which one to call and with what arguments.

---

# Tools

The agent has access to two tools, both described to the LLM as JSON schemas:

| Tool | Engine | Purpose |
|---|---|---|
| **`get_current_time`** | Local system clock | Returns the current date and time in a spoken-friendly format. |
| **`get_weather`** | Open-Meteo (geocoding + forecast API) | Looks up a city's coordinates, then fetches current temperature and wind speed for it. |

Each tool is a plain Python function defined in `agent.py`, wrapped in a JSON schema so the model knows when and how to call it.

---

## System Prompt

The agent uses a single system prompt that instructs the model to:

- Sound friendly, calm, and natural — like a helpful human, not a chatbot
- Keep replies brief and easy to listen to, unless a detailed explanation is requested
- Avoid markdown, lists, or punctuation that would sound awkward when spoken aloud
- Use the available tools whenever they would improve the accuracy of a response

This keeps the agent's spoken replies natural and its tool usage predictable.

---

# AI Models Used

| Model | Purpose |
|---|---|
| **`whisper-large-v3`** (via Groq) | Speech-to-text transcription of the user's recorded audio. |
| **`llama-3.3-70b-versatile`** (via Groq) | Drives the agent's reasoning and tool-calling — decides which tool to call, extracts arguments, and writes the final reply. |
| **`aura-2-thalia-en`** (via Deepgram) | Converts the agent's text reply into natural-sounding speech. |

---

# Tech Stack

- Python
- Streamlit
- Groq API (Whisper ASR + LLM reasoning/tool-calling)
- Deepgram API (Aura-2 text-to-speech)
- audio-recorder-streamlit (in-browser mic capture)
- Open-Meteo (free geocoding + weather API)
- python-dotenv
- requests

---

# Installation

## 1. Clone the repository

```
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
```

## 2. Move into the project folder

```
cd voice-bot
```

## 3. Open the project in VS Code

```
code .
```

## 4. Install all dependencies

Open the terminal inside VS Code and run:

```
pip install -r requirements.txt
```

## 5. Create a `.env` file

Inside the project folder, create a file named:

```
.env
```

Add your API keys:

```
GROQ_API_KEY=your_groq_api_key_here
DEEPGRAM_API_KEY=your_deepgram_api_key_here
```

Get your free keys here:

- **Groq**: https://console.groq.com/keys
- **Deepgram**: https://console.deepgram.com/

---

# Run the Application

Launch the agent using Streamlit:

```
streamlit run app.py
```

This opens at `http://localhost:8501`, where you can click the microphone, ask something like *"what's the weather in Islamabad"* or *"what time is it"*, and hear the agent think, call a tool if needed, and reply back out loud.

---

# Live Demo
 
You can try the deployed application here: [VoiceBot](https://voice-bot-11.streamlit.app/)

---

# Notes & Limitations

- Requires a working microphone and browser permission to record audio.
- Weather lookups depend on Open-Meteo's geocoding matching the spoken city name correctly.
- Conversation history is kept in-session only (`st.session_state`) and resets on page reload or when **Clear Chat** is pressed.
- Both `GROQ_API_KEY` and `DEEPGRAM_API_KEY` must be set (via `.env` locally or `st.secrets` when deployed) or the agent will raise a clear error instead of failing silently.

---

# 💡 Future Improvements

Some ideas for future enhancements:

- Streaming (word-by-word) TTS playback instead of waiting for the full reply
- More tools (calendar, reminders, search, smart-home control)
- Persistent conversation history across sessions
- Multi-language speech input and output
- Interruptible playback (barge-in while the agent is speaking)
- Voice selection / customization for the TTS output

---

# 👩‍💻 Author

**Haseeba Yasin**

If you found this project helpful, feel free to ⭐ the repository.